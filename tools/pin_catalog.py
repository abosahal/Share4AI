"""Maintainer-only metadata refresh. Review diff before publishing; downloads no binaries."""
import json
from pathlib import Path
import urllib.request


def get(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def main():
    tag = 'b10868'
    release = get(f'https://api.github.com/repos/ggml-org/llama.cpp/releases/tags/{tag}')
    def artifact(name):
        a = next(a for a in release['assets'] if a['name'] == name)
        assert a['digest'].startswith('sha256:')
        return dict(url=a['browser_download_url'], size=a['size'], sha256=a['digest'][7:],
                    signature=None, digest_source=release['html_url'])
    catalog = dict(schema_version=1, runtime_version=tag, runtimes={
        'windows-cpu': [artifact(f'llama-{tag}-bin-win-cpu-x64.zip')],
        'windows-cuda': [artifact(f'llama-{tag}-bin-win-cuda-12.4-x64.zip'),
                         artifact('cudart-llama-bin-win-cuda-12.4-x64.zip')]}, models=[])
    for size, vram, ram in [('4B', 4608, 6144), ('9B', 8192, 10240)]:
        repo = f'unsloth/Qwen3.5-{size}-GGUF'
        info = get(f'https://huggingface.co/api/models/{repo}?blobs=true')
        filename = f'Qwen3.5-{size}-Q4_K_M.gguf'
        entry = next(x for x in info['siblings'] if x['rfilename'] == filename)
        catalog['models'].append(dict(id=f'qwen3.5-{size.lower()}-q4_k_m', family='Qwen3.5',
            revision=info['sha'], quantization='Q4_K_M', required_vram_mb=vram, required_ram_mb=ram,
            context=4096, source=f'https://huggingface.co/{repo}', license='Apache-2.0 (upstream Qwen; retain notices)',
            artifact=dict(url=f'https://huggingface.co/{repo}/resolve/{info["sha"]}/{filename}',
                          size=entry['size'], sha256=entry['lfs']['sha256'], signature=None,
                          digest_source=f'https://huggingface.co/api/models/{repo}/revision/{info["sha"]}?blobs=true')))
    Path('provider/catalog.json').write_text(json.dumps(catalog, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
