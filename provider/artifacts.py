"""Pinned HTTPS artifacts, checked before activation. No arbitrary URL installer."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile
import threading
import urllib.parse
import urllib.request
import zipfile

ORIGINS = {'github.com', 'huggingface.co'}
REDIRECTS = ORIGINS | {'release-assets.githubusercontent.com', 'cdn-lfs.huggingface.co',
                        'cdn-lfs-us-1.hf.co', 'cas-bridge.xethub.hf.co'}


class ArtifactError(RuntimeError):
    pass


class Cancelled(ArtifactError):
    pass


def validate_url(url, redirect=False):
    p = urllib.parse.urlsplit(url)
    if p.scheme != 'https' or p.hostname not in (REDIRECTS if redirect else ORIGINS) or p.username or p.password or p.port not in (None, 443):
        raise ArtifactError('Untrusted artifact URL')


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl, redirect=True)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_signature(path, signature):
    if not signature:
        return 'not-published'
    if signature.get('type') != 'authenticode' or os.name != 'nt':
        raise ArtifactError('Unsupported required signature')
    # Path goes through an environment variable, never through interpolated shell code.
    env = dict(os.environ, SHARE4AI_VERIFY_PATH=str(Path(path).resolve()))
    command = '$s=Get-AuthenticodeSignature -LiteralPath $env:SHARE4AI_VERIFY_PATH; @{status=[string]$s.Status; thumbprint=$s.SignerCertificate.Thumbprint} | ConvertTo-Json -Compress'
    out = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
                         env=env, capture_output=True, text=True, check=True, timeout=30, creationflags=0x08000000)
    result = json.loads(out.stdout)
    if result['status'] != 'Valid' or result['thumbprint'].lower() != signature.get('thumbprint', '').lower():
        raise ArtifactError('Signature verification failed')
    return 'verified'


def download(artifact, directory: Path, cancel=None, progress=lambda done, total: None, opener=None):
    cancel = cancel or threading.Event()
    validate_url(artifact['url'])
    digest = artifact['sha256']
    if not re.fullmatch(r'[0-9a-f]{64}', digest) or not isinstance(artifact['size'], int) or artifact['size'] <= 0:
        raise ArtifactError('Invalid artifact metadata')
    directory.mkdir(parents=True, exist_ok=True)
    suffix = '.zip' if artifact['url'].split('?')[0].endswith('.zip') else '.gguf'
    destination = directory / (digest + suffix)
    if destination.is_file() and destination.stat().st_size == artifact['size'] and sha256(destination) == digest:
        verify_signature(destination, artifact.get('signature'))
        return destination
    if shutil.disk_usage(directory).free < artifact['size'] + 256 * 2**20:
        raise ArtifactError('Insufficient disk space')
    # Each attempt has a private partial file. Retry restarts safely; no unsafe Range append.
    fd, temp = tempfile.mkstemp(suffix='.part', dir=directory)
    partial = Path(temp)
    try:
        hasher, count = hashlib.sha256(), 0
        request = urllib.request.Request(artifact['url'], headers={'User-Agent': 'Share4AI/1.1'})
        open_url = opener or urllib.request.build_opener(SafeRedirect()).open
        with os.fdopen(fd, 'wb') as target:
            with open_url(request, timeout=30) as response:
                while True:
                    if cancel.is_set():
                        raise Cancelled('Download cancelled; retry is safe')
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    count += len(block)
                    if count > artifact['size']:
                        raise ArtifactError('Artifact exceeds expected size')
                    target.write(block)
                    hasher.update(block)
                    progress(count, artifact['size'])
            target.flush()
            os.fsync(target.fileno())
        if count != artifact['size'] or hasher.hexdigest() != digest:
            raise ArtifactError('SHA256 or size mismatch; artifact not activated')
        verify_signature(partial, artifact.get('signature'))
        os.replace(partial, destination)
        return destination
    finally:
        partial.unlink(missing_ok=True)


def extract_archives(archives, destination: Path, max_bytes=3 * 2**30):
    """Extract to a new directory; reject path ambiguity and duplicates before writing."""
    if destination.exists():
        raise ArtifactError('Runtime destination must be new')
    planned, names, total = [], set(), 0
    for archive in archives:
        with zipfile.ZipFile(archive) as z:
            for member in z.infolist():
                path = PurePosixPath(member.filename.replace('\\', '/'))
                if (path.is_absolute() or not path.parts or '..' in path.parts or ':' in str(path)
                        or any(p.endswith((' ', '.')) or p.split('.')[0].upper() in
                               {'CON', 'PRN', 'AUX', 'NUL', *('COM' + str(i) for i in range(10)), *('LPT' + str(i) for i in range(10))}
                               for p in path.parts)
                        or stat.S_ISLNK(member.external_attr >> 16)):
                    raise ArtifactError('Unsafe runtime archive path')
                key = str(path).lower()
                if key in names and not member.is_dir():
                    raise ArtifactError('Duplicate runtime archive path')
                names.add(key)
                total += member.file_size
                if total > max_bytes or len(names) > 10000:
                    raise ArtifactError('Runtime archive exceeds extraction limit')
                planned.append((archive, member.filename, path, member.is_dir()))
    if shutil.disk_usage(destination.parent).free < total + 256 * 2**20:
        raise ArtifactError('Insufficient extraction space')
    destination.mkdir()
    try:
        for archive, name, relative, is_dir in planned:
            target = destination.joinpath(*relative.parts)
            if is_dir:
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(archive) as z, z.open(name) as source, target.open('xb') as output:
                    shutil.copyfileobj(source, output)
        executables = list(destination.rglob('llama-server.exe'))
        if len(executables) != 1:
            raise ArtifactError('Expected one llama-server.exe')
        # Dependencies ship separately; keep DLLs beside the executable if needed.
        binary = executables[0]
        for dll in list(destination.rglob('*.dll')):
            if dll.parent != binary.parent:
                target = binary.parent / dll.name
                if target.exists():
                    raise ArtifactError('Ambiguous runtime dependency')
                shutil.copy2(dll, target)
        return binary
    except Exception:
        shutil.rmtree(destination)
        raise
