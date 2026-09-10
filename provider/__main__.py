import argparse
from pathlib import Path
import json


def main():
    parser = argparse.ArgumentParser(description='Share4AI Provider')
    parser.add_argument('--state-dir', type=Path)
    parser.add_argument('--scan', action='store_true', help='Read-only hardware report')
    args = parser.parse_args()
    if args.scan:
        from .hardware import scan
        print(json.dumps(scan(args.state_dir or Path('.state')).to_dict(), indent=2))
    else:
        from .ui import launch
        launch(args.state_dir)


if __name__ == '__main__':
    main()
