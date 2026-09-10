"""Read-only hardware discovery. Unknown telemetry is never treated as zero."""
from dataclasses import dataclass, field, asdict
import csv
import ctypes
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess


def run_hidden(args, timeout=10):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                          check=True, creationflags=0x08000000 if os.name == "nt" else 0).stdout


@dataclass
class GPU:
    index: int
    name: str
    total_mb: float
    free_mb: float
    utilization: float | None
    temperature: float | None


@dataclass
class Hardware:
    system: str
    machine: str
    cpu: str
    cores: int
    ram_mb: float
    available_ram_mb: float
    disk_free_mb: float
    gpus: list[GPU] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def parse_nvidia(output):
    result = []
    for row in csv.reader(io.StringIO(output)):
        if len(row) != 6:
            continue
        try:
            optional = lambda value: float(value.strip()) if value.strip().replace('.', '', 1).isdigit() else None
            result.append(GPU(int(row[0]), row[1].strip(), float(row[2]), float(row[3]),
                              optional(row[4]), optional(row[5])))
        except ValueError:
            continue
    return result


def scan(cache: Path, runner=run_hidden):
    cache.mkdir(parents=True, exist_ok=True)
    ram = available = 0.0
    warnings = []
    if os.name == "nt":
        class Memory(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong) for name in
                ("total", "available", "page", "availpage", "virtual", "availvirtual", "extended")]
        mem = Memory()
        mem.length = ctypes.sizeof(mem)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
            ram, available = mem.total / 2**20, mem.available / 2**20
    else:
        try:
            info = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
            ram = int(info['MemTotal'].split()[0]) / 1024
            available = int(info['MemAvailable'].split()[0]) / 1024
        except (OSError, KeyError):
            warnings.append('RAM telemetry unavailable')
    smi = shutil.which('nvidia-smi')
    if not smi and os.name == 'nt':
        candidate = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/nvidia-smi.exe'
        if candidate.is_file():
            smi = str(candidate)
    gpus = []
    if smi:
        try:
            gpus = parse_nvidia(runner([smi, '--query-gpu=index,name,memory.total,memory.free,utilization.gpu,temperature.gpu',
                                        '--format=csv,noheader,nounits']))
        except (OSError, subprocess.SubprocessError):
            warnings.append('NVIDIA telemetry unavailable')
    if not gpus:
        warnings.append('No supported NVIDIA telemetry; CPU local mode only')
        if os.name == 'nt':
            try:
                adapters = runner(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                                   'Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name | ConvertTo-Json'])
                names = json.loads(adapters)
                warnings.append('Detected display: ' + ', '.join(names if isinstance(names, list) else [names]))
            except (OSError, subprocess.SubprocessError, ValueError):
                pass
    return Hardware(platform.system(), platform.machine(), platform.processor() or 'Unknown CPU',
                    os.cpu_count() or 1, ram, available, shutil.disk_usage(cache).free / 2**20, gpus, warnings)
