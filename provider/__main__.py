from provider.i18n import tr, display_message, BilingualParser
from pathlib import Path
import json


def main():
    parser = BilingualParser(description=tr('Share4AI Provider'))
    parser.add_argument('--state-dir', type=Path, help='مجلد الحالة المحلية / local state directory')
    parser.add_argument('--scan', action='store_true', help=tr('Read-only hardware report'))
    args = parser.parse_args()
    if args.scan:
        from .hardware import scan
        report = scan(args.state_dir or Path('.state')).to_dict()
        report['warnings'] = [display_message(w) for w in report['warnings']]
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        from .ui import launch
        launch(args.state_dir)


if __name__ == '__main__':
    main()
