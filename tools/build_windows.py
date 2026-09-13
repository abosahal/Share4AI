"""Maintainer build tool; customers only download the resulting Setup.exe."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--iscc', required=True, type=Path)
    args = parser.parse_args()
    if sys.platform != 'win32':
        parser.error('Build on Windows')
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    compiler = args.iscc.resolve()
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--windowed',
        '--onedir', '--name', 'Share4AI', '--specpath', 'build', '--paths', str(root),
        '--add-data', str(root / 'provider' / 'catalog.json') + ':provider', str(root / 'desktop.py')], check=True)
    notice = root / 'dist' / 'Share4AI' / 'licenses'
    notice.mkdir(exist_ok=True)
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    if not python_license.is_file():
        raise RuntimeError('Python redistribution license missing')
    shutil.copy2(python_license, notice / 'Python.txt')
    shutil.copy2(root / 'packaging' / 'THIRD_PARTY_NOTICES.md', notice / 'THIRD_PARTY_NOTICES.md')
    report = root / 'build' / 'package-smoke.json'
    report.unlink(missing_ok=True)
    process = subprocess.run([str(root / 'dist' / 'Share4AI' / 'Share4AI.exe'), '--smoke-test', str(report)], timeout=45)
    if process.returncode or not report.is_file() or not json.loads(report.read_text())['ok']:
        raise RuntimeError('Packaged UI smoke test failed; installer not built')
    subprocess.run([str(compiler), str(root / 'packaging' / 'Share4AI.iss')], check=True)
    installer = root / 'dist' / 'installer' / 'Share4AI-Setup-1.1.0-windows-x64.exe'
    digest = hashlib.sha256(installer.read_bytes()).hexdigest()
    installer.with_suffix('.exe.sha256').write_text(digest + '  ' + installer.name + '\n', encoding='ascii')
    print(installer)


if __name__ == '__main__':
    main()
