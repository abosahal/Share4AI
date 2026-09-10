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


def recommend(hw: Hardware, catalog=None):
    catalog = catalog or load_catalog()
    if hw.system != 'Windows' or hw.machine.lower() not in ('amd64', 'x86_64'):
        return Recommendation(None, '', None, 'This alpha supports Windows x64 only')
    for gpu in sorted(hw.gpus, key=lambda g: g.free_mb, reverse=True):
        for model in reversed(catalog['models']):
            if (gpu.free_mb >= model['required_vram_mb'] and hw.available_ram_mb >= model['required_ram_mb']
                    and hw.disk_free_mb >= model['artifact']['size'] / 2**20 + 4096):
                return Recommendation(model, 'windows-cuda', gpu.index,
                                      'Fits available memory with reserve; benchmark still required')
    model = catalog['models'][0]
    if hw.available_ram_mb >= model['required_ram_mb'] + 2048 and hw.disk_free_mb >= model['artifact']['size'] / 2**20 + 4096:
        return Recommendation(model, 'windows-cpu', None, 'CPU local trial; network sharing requires GPU telemetry and benchmark')
    return Recommendation(None, '', None, 'Not enough free memory or disk; close other workloads and scan again')
