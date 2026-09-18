import unittest
from provider.catalog import recommend
from provider.hardware import Hardware, GPU
from provider.readiness import verdict, mode_label, selected_gpu, gpu_fields, diagnostic_text


class ReadinessTests(unittest.TestCase):
    def test_blocked_low_ram(self):
        hw = Hardware('Windows', 'AMD64', 'CPU', 4, 8 * 1024, 4 * 1024, 400 * 1024, [])
        rec = recommend(hw)
        self.assertEqual(verdict(rec), 'Device does not meet this version')
        self.assertEqual(mode_label(rec), 'No suitable model')

    def test_cpu_trial_when_no_gpu(self):
        hw = Hardware('Windows', 'AMD64', 'CPU', 8, 32768, 22000, 50000, [])
        rec = recommend(hw)
        self.assertEqual(verdict(rec), 'CPU local trial only')
        self.assertEqual(mode_label(rec), 'CPU')

    def test_partial_offload_on_smaller_vram(self):
        hw = Hardware('Windows', 'AMD64', 'CPU', 8, 32768, 22000, 50000,
                      [GPU(0, 'RTX 3060 Ti', 8192, 7000, 12, 51)])
        rec = recommend(hw)
        self.assertEqual(verdict(rec), 'Ready with partial GPU offload')
        self.assertEqual(mode_label(rec), 'GPU offload')
        gpu = selected_gpu(hw, rec)
        self.assertEqual(gpu_fields(gpu)['name'], 'RTX 3060 Ti')
        self.assertEqual(gpu_fields(gpu)['utilization'], '12%')

    def test_unknown_utilization_is_not_zero(self):
        fields = gpu_fields(GPU(0, 'RTX', 8192, 7000, None, 44))
        self.assertEqual(fields['utilization'], '—')
        self.assertEqual(fields['temperature'], '44 C')

    def test_diagnostic_contains_verdict_not_secrets(self):
        hw = Hardware('Windows', 'AMD64', 'Ryzen', 8, 32768, 22000, 50000,
                      [GPU(0, 'RTX 3060 Ti', 8192, 7000, None, 44)],
                      ['NVIDIA telemetry unavailable'])
        rec = recommend(hw)
        text = diagnostic_text(hw, rec)
        self.assertIn('RTX 3060 Ti', text)
        self.assertIn('Ready with partial GPU offload', text)
        self.assertNotIn('token', text.lower())
        self.assertNotIn('password', text.lower())


if __name__ == '__main__':
    unittest.main()
