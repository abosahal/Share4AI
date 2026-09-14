import io
import unittest
from provider.runtime import parse_sse, RuntimeFailure, StreamEvent
from provider.benchmark import measure


class RuntimeTests(unittest.TestCase):
    def test_sse_content_and_final_usage(self):
        data = (': ping\n\ndata: {"choices":[{"delta":{"content":"hello"}}]}\n\n'
                'data: {"choices":[],"usage":{"completion_tokens":12},"timings":{"predicted_per_second":40}}\n\n'
                'data: [DONE]\n\n')
        events = list(parse_sse(io.BytesIO(data.encode())))
        self.assertEqual(events[0].text, 'hello')
        self.assertEqual(events[1].completion_tokens, 12)
        self.assertEqual(events[1].tokens_per_second, 40)

    def test_interrupted_stream_is_failure(self):
        with self.assertRaises(RuntimeFailure):
            list(parse_sse(io.BytesIO(b'data: {"choices":[]}\n\n')))

    def test_benchmark_uses_token_usage_not_chunks(self):
        class Fake:
            def stream(self, *args, **kwargs):
                yield StreamEvent('a whole sentence')
                yield StreamEvent(completion_tokens=101, tokens_per_second=50)
        times = iter([0, 1, 3])
        result = measure(Fake(), 'prompt', clock=lambda: next(times))
        self.assertEqual(result['completion_tokens'], 101)
        self.assertEqual(result['ttft_seconds'], 1)
        self.assertEqual(result['tokens_per_second'], 50)

    def test_benchmark_missing_usage_rejected(self):
        class Fake:
            def stream(self, *args, **kwargs):
                yield StreamEvent('hello')
        with self.assertRaises(RuntimeFailure):
            measure(Fake(), 'prompt')
