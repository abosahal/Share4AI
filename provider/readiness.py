"""Provider-facing device verdict. Presentation only; catalog decides eligibility."""
from .hardware import Hardware, GPU
from .catalog import Recommendation


def gb(amount_mb):
    if not amount_mb:
        return '—'
    return f'{amount_mb / 1024:.1f} GB'


def gpu_fields(gpu: GPU | None):
    if gpu is None:
        return dict(name='', vram='—', free_vram='—', utilization='—', temperature='—')
    util = f'{gpu.utilization:.0f}%' if gpu.utilization is not None else '—'
    temp = f'{gpu.temperature:.0f} C' if gpu.temperature is not None else '—'
    return dict(
        name=gpu.name,
        vram=gb(gpu.total_mb),
        free_vram=gb(gpu.free_mb),
        utilization=util,
        temperature=temp,
    )


def selected_gpu(hw: Hardware, rec: Recommendation | None) -> GPU | None:
    if rec and rec.gpu_index is not None:
        for gpu in hw.gpus:
            if gpu.index == rec.gpu_index:
                return gpu
    return hw.gpus[0] if hw.gpus else None


def verdict(rec: Recommendation | None) -> str:
    if rec is None:
        return 'Scan your device to find a suitable model.'
    if rec.model is None:
        return 'Device does not meet this version'
    if rec.runtime_key == 'windows-cpu':
        return 'CPU local trial only'
    if rec.ngl and rec.ngl < 99:
        return 'Ready with partial GPU offload'
    return 'Ready for GPU Local AI'


def mode_label(rec: Recommendation | None) -> str:
    if rec is None or rec.model is None:
        return 'No suitable model'
    if rec.runtime_key == 'windows-cpu':
        return 'CPU'
    if rec.ngl and rec.ngl < 99:
        return 'GPU offload'
    return 'GPU'


def diagnostic_text(hw: Hardware | None, rec: Recommendation | None) -> str:
    lines = ['Share4AI device report']
    if hw is None:
        lines.append('No scan yet')
        return '\n'.join(lines)
    lines.append(f'System: {hw.system} {hw.machine}')
    lines.append(f'CPU: {hw.cpu} ({hw.cores} cores)')
    lines.append(f'RAM: {gb(hw.ram_mb)} total / {gb(hw.available_ram_mb)} free')
    lines.append(f'Disk free: {gb(hw.disk_free_mb)}')
    if hw.gpus:
        for gpu in hw.gpus:
            fields = gpu_fields(gpu)
            lines.append(
                f'GPU {gpu.index}: {fields["name"]} • VRAM {fields["vram"]} • free {fields["free_vram"]} • '
                f'util {fields["utilization"]} • temp {fields["temperature"]}'
            )
    else:
        lines.append('No NVIDIA GPU telemetry')
    for warning in hw.warnings:
        lines.append('Warning: ' + warning)
    if rec:
        lines.append('Verdict: ' + verdict(rec))
        lines.append('Mode: ' + mode_label(rec))
        if rec.model:
            lines.append('Model: ' + rec.model['id'])
        if rec.reason:
            lines.append(rec.reason)
    return '\n'.join(lines)
