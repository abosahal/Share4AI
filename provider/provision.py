from pathlib import Path
import json
import os
import tempfile
import threading
import uuid
from .artifacts import download, extract_archives, sha256, ArtifactError, Cancelled
from .catalog import load_catalog


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def install(root, recommendation, cancel=None, progress=lambda message: None, catalog=None):
    catalog = catalog or load_catalog()
    cancel = cancel or threading.Event()
    if recommendation.model is None:
        raise ArtifactError('No suitable model recommended')
    model = recommendation.model
    progress('Downloading and verifying runtime')
    archives = [download(a, root / 'downloads', cancel, lambda d, n: progress(f'Runtime {d * 100 // n}%'))
                for a in catalog['runtimes'][recommendation.runtime_key]]
    progress('Downloading and verifying ' + model['id'])
    model_path = download(model['artifact'], root / 'models', cancel,
                          lambda d, n: progress(f'Model {d * 100 // n}%'))
    if cancel.is_set():
        raise Cancelled('Install cancelled')
    runtime_root = root / 'runtimes'
    runtime_root.mkdir(parents=True, exist_ok=True)
    executable = extract_archives(archives, runtime_root / (catalog['runtime_version'] + '-' + uuid.uuid4().hex))
    if cancel.is_set():
        raise Cancelled('Install cancelled before activation')
    inventory = {str(p.relative_to(root)): sha256(p) for p in executable.parent.rglob('*') if p.is_file()}
    record = dict(model=model, model_path=str(model_path.relative_to(root)),
                  executable=str(executable.relative_to(root)), runtime_version=catalog['runtime_version'],
                  runtime_key=recommendation.runtime_key, gpu_index=recommendation.gpu_index, inventory=inventory)
    atomic_json(root / 'installed.json', record)
    progress('Installed and SHA256 verified')
    return record


def checked_path(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ArtifactError('Invalid installed path')
    return path


def verify_install(root, record):
    catalog = load_catalog()
    approved = next((m for m in catalog['models'] if m['id'] == record['model']['id']), None)
    if approved != record['model'] or record['runtime_version'] != catalog['runtime_version']:
        raise ArtifactError('Installed manifest is not in the approved catalog')
    model = checked_path(root, record['model_path'])
    if sha256(model) != record['model']['artifact']['sha256']:
        raise ArtifactError('Installed model was modified; reinstall')
    binary = checked_path(root, record['executable'])
    inventory = record.get('inventory', {})
    if record['executable'] not in inventory:
        raise ArtifactError('Runtime inventory missing executable')
    actual = {str(p.relative_to(root)) for p in binary.parent.rglob('*') if p.is_file()}
    if actual != set(inventory):
        raise ArtifactError('Runtime directory contents changed; reinstall')
    for name, digest in inventory.items():
        if sha256(checked_path(root, name)) != digest:
            raise ArtifactError('Installed runtime was modified; reinstall')
    return binary, model
