from dataclasses import dataclass
import json
from pathlib import Path
from .hardware import Hardware


def load_catalog():
    return json.loads(Path(__file__).with_name('catalog.json').read_text(encoding='utf-8'))


@dataclass
class Recommendation:
    model: dict | None
    runtime_key: str
    gpu_index: int | None
    reason: str
    required_free_ram_mb: float = 0
    required_disk_mb: float = 0
    blockers: tuple[str, ...] = ()
    ngl: int = 99


def recommend(hw: Hardware, catalog=None):
    catalog = catalog or load_catalog()
    if hw.system != 'Windows' or hw.machine.lower() not in ('amd64', 'x86_64'):
        return Recommendation(None, '', None, 'This alpha supports Windows x64 only')
    gpus = sorted(hw.gpus, key=lambda g: g.free_mb, reverse=True)
    for model in reversed(catalog['models']):
        disk_ok = hw.disk_free_mb >= model['artifact']['size'] / 2**20 + 4096
        if hw.available_ram_mb < model['required_ram_mb'] or not disk_ok:
            continue
        for gpu in gpus:
            if gpu.free_mb >= model['required_vram_mb']:
                return Recommendation(model, 'windows-cuda', gpu.index,
                                      'Fits available memory with reserve; benchmark still required',
                                      model['required_ram_mb'], model['artifact']['size'] / 2**20 + 4096)
        if model.get('allow_ram_offload') and gpus and gpus[0].free_mb >= 4096:
            return Recommendation(model, 'windows-cuda', gpus[0].index,
                                  'Fits available memory with reserve; benchmark still required',
                                  model['required_ram_mb'], model['artifact']['size'] / 2**20 + 4096,
                                  (), model.get('offload_gpu_layers', 28))
    model = catalog['models'][0]
    if hw.available_ram_mb >= model['required_ram_mb'] + 2048 and hw.disk_free_mb >= model['artifact']['size'] / 2**20 + 4096:
        return Recommendation(model, 'windows-cpu', None, 'CPU local trial; network sharing requires GPU telemetry and benchmark',
                              model['required_ram_mb'] + 2048, model['artifact']['size'] / 2**20 + 4096)
    gpu_eligible = any(g.free_mb >= model['required_vram_mb'] for g in hw.gpus)
    required_ram = model['required_ram_mb'] + (0 if gpu_eligible else 2048)
    required_disk = model['artifact']['size'] / 2**20 + 4096
    blockers, reasons = [], []
    if hw.ram_mb < required_ram:
        blockers.append('total_ram')
        reasons.append('This device has less total memory than this version requires. Closing apps alone will not be enough.')
    elif hw.available_ram_mb < required_ram:
        blockers.append('free_ram')
        reasons.append('Not enough free memory. Close other apps and scan again.')
    if hw.disk_free_mb < required_disk:
        blockers.append('disk')
        reasons.append('Not enough free disk space. Free some space and scan again.')
    return Recommendation(None, '', None, '\n'.join(reasons), required_ram, required_disk, tuple(blockers))
