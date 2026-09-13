"""Interactive local pilot consumer; prompts never enter provider desktop events."""
from provider.i18n import tr, BilingualParser
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from provider.control import ControlClient, ControlError


def main():
    parser = BilingualParser(description=tr('Share4AI pilot client'))
    parser.add_argument('--url', default='http://127.0.0.1:8000', help='عنوان خادم التحكم / Control Plane URL')
    parser.add_argument('--model-sha256', help='بصمة النموذج / model SHA256')
    parser.add_argument('--state-dir', type=Path, default=Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'Share4AI', help='مجلد الحالة المحلية / local state directory')
    args = parser.parse_args()
    token = os.environ.get('SHARE4AI_CLIENT_TOKEN', '')
    if not token:
        parser.error(tr('Set SHARE4AI_CLIENT_TOKEN in this terminal'))
    try:
        client = ControlClient(args.url, token)
    except ControlError as error:
        parser.error(str(error))
    model = args.model_sha256
    if not model:
        try:
            model = json.loads((args.state_dir / 'installed.json').read_text(encoding='utf-8'))['model']['artifact']['sha256']
        except (OSError, ValueError, KeyError):
            parser.error(tr('Install a model first or provide --model-sha256'))
    prompt = input(tr('Your message:') + ' ').strip()
    if not prompt:
        return
    req = urllib.request.Request(client.base_url + '/v1/chat/stream', data=json.dumps(dict(
        messages=[{'role': 'user', 'content': prompt}], max_tokens=256, model_sha256=model)).encode(),
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    terminal = False
    try:
        with client.opener.open(req, timeout=130) as response:
            for line in response:
                if not line.startswith(b'data: '):
                    continue
                event = json.loads(line[6:])
                if event['kind'] == 'token':
                    print(event['text'], end='', flush=True)
                elif event['kind'] == 'done':
                    terminal = True
                elif event['kind'] == 'error':
                    terminal = True
                    print('\n' + tr('Request stopped. Retry after checking provider readiness.'))
        if not terminal:
            print('\n' + tr('Connection interrupted; response is incomplete.'))
    except urllib.error.HTTPError as error:
        code = error.code; error.close()
        print(tr('Request rejected ({code}). Check credentials, model and provider availability.', code=code))
    except (OSError, ValueError, KeyboardInterrupt):
        print('\n' + tr('Request interrupted.'))
    print()


if __name__ == '__main__':
    main()
