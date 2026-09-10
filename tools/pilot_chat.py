"""Interactive local pilot consumer; prompts never enter provider desktop events."""
import argparse
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from provider.control import ControlClient


def main():
    parser = argparse.ArgumentParser(description='Share4AI pilot client')
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    parser.add_argument('--model-sha256')
    parser.add_argument('--state-dir', type=Path, default=Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'Share4AI')
    args = parser.parse_args()
    token = os.environ.get('SHARE4AI_CLIENT_TOKEN', '')
    if not token:
        parser.error('Set SHARE4AI_CLIENT_TOKEN in this terminal')
    client = ControlClient(args.url, token)
    model = args.model_sha256
    if not model:
        try:
            model = json.loads((args.state_dir / 'installed.json').read_text(encoding='utf-8'))['model']['artifact']['sha256']
        except (OSError, ValueError, KeyError):
            parser.error('Install a model first or provide --model-sha256')
    prompt = input('Your message: ').strip()
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
                    print('\nRequest stopped. Retry after checking provider readiness.')
        if not terminal:
            print('\nConnection interrupted; response is incomplete.')
    except urllib.error.HTTPError as error:
        code = error.code; error.close()
        print(f'Request rejected ({code}). Check credentials, model and provider availability.')
    except (OSError, ValueError, KeyboardInterrupt):
        print('\nRequest interrupted.')
    print()


if __name__ == '__main__':
    main()
