"""Read attached documents as text. Images are rejected: the local model is text-only."""
from io import BytesIO
from pathlib import Path
import re
import zipfile
import zlib

TEXT_SUFFIXES = {
    '.txt', '.md', '.csv', '.json', '.log', '.xml', '.html', '.htm',
    '.py', '.js', '.ts', '.css', '.yml', '.yaml', '.ini', '.toml', '.rtf',
}
MAX_BYTES = 2_000_000
MAX_CHARS = 6000
MAX_FILES = 3


class DocumentError(RuntimeError):
    pass


def _plain(data):
    return data.decode('utf-8', errors='replace')


def _docx(data):
    try:
        with zipfile.ZipFile(BytesIO(data)) as archive:
            xml = archive.read('word/document.xml').decode('utf-8', errors='replace')
    except (KeyError, zipfile.BadZipFile, ValueError) as error:
        raise DocumentError('No readable text in this file') from error
    return re.sub(r'<w:tab[^/]*/>', '\t', re.sub(r'</w:p>', '\n', xml))


def _pdf(data):
    chunks = []
    for match in re.finditer(rb'stream\r?\n(.*?)endstream', data, re.S):
        raw = match.group(1)
        try:
            raw = zlib.decompress(raw.strip())
        except zlib.error:
            pass
        for item in re.findall(rb'\((?:\\.|[^\\)]){2,}\)', raw):
            text = item[1:-1].replace(br'\n', b'\n').replace(br'\r', b'').replace(br'\t', b'\t')
            text = re.sub(br'\\(\d{1,3})', lambda m: bytes([int(m[1], 8) & 255]), text)
            decoded = text.decode('latin-1', errors='ignore')
            if any(ch.isalpha() for ch in decoded):
                chunks.append(decoded)
    return '\n'.join(chunks)


def read_document(path):
    path = Path(path)
    suffix = path.suffix.lower()
    try:
        data = path.read_bytes()
    except OSError as error:
        raise DocumentError('Could not read this file') from error
    if len(data) > MAX_BYTES:
        raise DocumentError('Attached file is too large')
    if suffix in TEXT_SUFFIXES:
        text = _plain(data)
    elif suffix == '.docx':
        text = _docx(data)
    elif suffix == '.pdf':
        text = _pdf(data)
    else:
        raise DocumentError('This file type is not supported. Attach text, PDF, or Word.')
    text = re.sub(r'<[^>]+>', ' ', text)
    text = '\n'.join(line.strip() for line in text.splitlines())
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    if not text:
        raise DocumentError('No readable text in this file')
    return dict(name=path.name, text=text[:MAX_CHARS])
