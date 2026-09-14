from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import math
import time
from .runtime import RuntimeFailure

PROMPTS = [
    'Explain three simple ways to organize a busy day. Use short clear sentences.',
    'اشرح ثلاث طرق بسيطة لتنظيم اليوم بجمل قصيرة وواضحة.',
    'Give five practical tips for learning a new language and explain each tip briefly.',
]


@dataclass
class BenchmarkResult:
    model_id: str
    model_sha256: str
    runtime_version: str
    context: int
    measured_at: str
    samples: list
    passed: bool
    max_ttft_seconds: float
    min_tokens_per_second: float
    policy_version: str = 'warm-v1-ttft2.5-tps25'

    def to_dict(self):
        return asdict(self)


def measure(runtime, prompt, cancel=None, clock=time.perf_counter):
    start, first, tokens, speed = clock(), None, None, None
    for event in runtime.stream([{'role': 'user', 'content': prompt}], max_tokens=128, cancel=cancel):
        if event.text and first is None:
            first = clock()
        if event.completion_tokens is not None:
            tokens = event.completion_tokens
        if event.tokens_per_second is not None:
            speed = event.tokens_per_second
    elapsed = clock() - start
    if first is None or not isinstance(tokens, int) or tokens < 2:
        raise RuntimeFailure('Benchmark requires content and actual runtime token usage')
    ttft = first - start
    # Runtime timing preferred; transport-inclusive estimate explicitly named otherwise.
    source = 'runtime' if speed is not None else 'usage/wall-time'
    if speed is None:
        speed = (tokens - 1) / max(elapsed - ttft, 0.001)
    if not math.isfinite(speed) or speed <= 0 or ttft < 0:
        raise RuntimeFailure('Invalid benchmark timing')
    return dict(ttft_seconds=round(ttft, 4), elapsed_seconds=round(elapsed, 4),
                completion_tokens=tokens, tokens_per_second=round(speed, 3), speed_source=source)


def benchmark(runtime, model, runtime_version, cancel=None):
    # Warmup is deliberately excluded from the admission score.
    measure(runtime, 'Say hello in one short sentence.', cancel)
    samples = [measure(runtime, prompt, cancel) for prompt in PROMPTS]
    worst_ttft = max(s['ttft_seconds'] for s in samples)
    slowest = min(s['tokens_per_second'] for s in samples)
    return BenchmarkResult(model['id'], model['artifact']['sha256'], runtime_version, model['context'],
        datetime.now(timezone.utc).isoformat(), samples, worst_ttft <= 2.5 and slowest >= 25,
        worst_ttft, slowest)
