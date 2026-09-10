import hashlib
import io
from pathlib import Path
import tempfile
import threading
import unittest
import zipfile
from provider.artifacts import download, extract_archives, ArtifactError, Cancelled, validate_url, verify_signature
from provider.catalog import recommend
from provider.hardware import Hardware, GPU, parse_nvidia


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def artifact(self, data=b'GGUFtest'):
        return dict(url='https://huggingface.co/test/model.gguf', size=len(data), sha256=hashlib.sha256(data).hexdigest())

    def test_digest_verified_and_corrupt_retry_preserves_good(self):
        good = download(self.artifact(), self.root, opener=lambda *a, **k: io.BytesIO(b'GGUFtest'))
        self.assertEqual(good.read_bytes(), b'GGUFtest')
        bad_artifact = self.artifact(b'another!')
        with self.assertRaises(ArtifactError):
            download(bad_artifact, self.root, opener=lambda *a, **k: io.BytesIO(b'corrupt!'))
        self.assertTrue(good.exists())
        self.assertEqual(list(self.root.glob('*.part')), [])

    def test_cancelled_and_oversized_download_never_activates(self):
        event = threading.Event(); event.set()
        with self.assertRaises(Cancelled):
            download(self.artifact(), self.root, event, opener=lambda *a, **k: io.BytesIO(b'GGUFtest'))
        with self.assertRaises(ArtifactError):
            download(self.artifact(), self.root, opener=lambda *a, **k: io.BytesIO(b'x' * 20))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_untrusted_urls_and_unsupported_signature(self):
        for url in ['http://github.com/a', 'https://evil.test/a', 'https://user@github.com/a', 'https://github.com:444/a']:
            with self.assertRaises(ArtifactError):
                validate_url(url)
        with self.assertRaises(ArtifactError):
            verify_signature(self.root / 'x', {'type': 'unknown'})

    def archive(self, names):
        path = self.root / 'runtime.zip'
        with zipfile.ZipFile(path, 'w') as z:
            for name in names:
                z.writestr(name, b'test')
        return path

    def test_zip_traversal_and_windows_ambiguity(self):
        for name in ['../outside', '/absolute', 'C:/escape', 'safe/file:stream', 'CON.txt', 'bad./x']:
            archive = self.archive([name, 'llama-server.exe'])
            with self.assertRaises(ArtifactError):
                extract_archives([archive], self.root / 'runtime')
            self.assertFalse((self.root / 'runtime').exists())

    def test_archive_limit_and_success(self):
        archive = self.archive(['bin/llama-server.exe', 'bin/ggml.dll'])
        with self.assertRaises(ArtifactError):
            extract_archives([archive], self.root / 'small', max_bytes=2)
        binary = extract_archives([archive], self.root / 'runtime')
        self.assertEqual(binary.read_bytes(), b'test')

    def test_nvidia_unknown_is_not_zero(self):
        gpu = parse_nvidia('0, RTX Test, 8192, 7000, N/A, 44\n')[0]
        self.assertIsNone(gpu.utilization)
        self.assertEqual(gpu.temperature, 44)

    def test_recommendation_uses_free_memory_and_selected_gpu(self):
        hw = Hardware('Windows', 'AMD64', 'CPU', 8, 32768, 20000, 50000,
                      [GPU(0, 'busy', 24000, 200, 90, 70), GPU(1, 'free', 12000, 10000, 0, 40)])
        r = recommend(hw)
        self.assertEqual(r.gpu_index, 1)
        self.assertIn('9b', r.model['id'])
        hw.gpus = []
        self.assertEqual(recommend(hw).runtime_key, 'windows-cpu')
        hw.available_ram_mb = 100
        self.assertIsNone(recommend(hw).model)


if __name__ == '__main__':
    unittest.main()
