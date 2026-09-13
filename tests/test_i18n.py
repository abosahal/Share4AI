import ast
import contextlib
import io
from pathlib import Path
import string
import unittest
from unittest.mock import patch

from provider.i18n import TEXT, tr, display_message, BilingualParser


class BilingualTests(unittest.TestCase):
    def test_catalog_templates_preserve_values_and_both_languages(self):
        formatter = string.Formatter()
        for source, arabic in TEXT.items():
            with self.subTest(source=source):
                fields = {field for _, field, _, _ in formatter.parse(source) if field}
                self.assertEqual(fields, {field for _, field, _, _ in formatter.parse(arabic) if field})
                self.assertRegex(arabic, r'[\u0600-\u06ff]')
                values = dict.fromkeys(fields, 'model-{literal}-123')
                self.assertTrue(tr(source, **values).endswith(source.format(**values)))
        self.assertIn('Runtime 42%', display_message('Runtime 42%'))
        self.assertIn('42', display_message('Model 42%'))
        self.assertIn('Qwen-{test}', display_message('Downloading and verifying Qwen-{test}'))
        self.assertEqual(display_message('unknown diagnostic'), 'unknown diagnostic')

    def test_all_owned_exception_messages_have_translations(self):
        root = Path(__file__).resolve().parents[1]
        for path in (root / 'provider').glob('*.py'):
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) and node.exc.args:
                    message = node.exc.args[0]
                    if isinstance(message, ast.Constant) and isinstance(message.value, str):
                        self.assertIn(message.value, TEXT, f'{path.name}:{node.lineno}')

    def test_cli_help_and_input_errors_are_bilingual(self):
        parser = BilingualParser(prog='test')
        help_text = parser.format_help()
        self.assertIn('الخيارات', help_text)
        self.assertIn('--help', help_text)
        error = io.StringIO()
        with contextlib.redirect_stderr(error), self.assertRaises(SystemExit):
            parser.error('Invalid Control Plane address')
        self.assertIn('عنوان خادم التحكم غير صالح', error.getvalue())
        self.assertIn('Invalid Control Plane address', error.getvalue())

    def test_pilot_stream_keeps_model_text_unchanged(self):
        from tools import pilot_chat
        from types import SimpleNamespace
        import json
        model_text = 'OFFLINE العربية {model} Start Sharing'
        response = io.BytesIO(('data: ' + json.dumps({'kind': 'token', 'text': model_text}) + '\n' +
                               'data: {"kind":"done"}\n').encode())
        client = SimpleNamespace(base_url='http://127.0.0.1:8000', opener=SimpleNamespace(open=lambda *a, **k: response))
        output = io.StringIO()
        with patch('sys.argv', ['pilot_chat', '--model-sha256', 'a' * 64]), \
                patch.dict('os.environ', SHARE4AI_CLIENT_TOKEN='test'), \
                patch.object(pilot_chat, 'ControlClient', return_value=client), \
                patch('builtins.input', return_value='private prompt'), contextlib.redirect_stdout(output):
            pilot_chat.main()
        self.assertEqual(output.getvalue(), model_text + '\n')


if __name__ == '__main__':
    unittest.main()
