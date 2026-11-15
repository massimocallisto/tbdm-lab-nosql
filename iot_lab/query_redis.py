"""Query the Redis latest-state projection, not a historical archive."""

from __future__ import annotations

import argparse
import json

from .config import load_settings
from .redis_store import connect_redis


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group()
    group.add_argument('--device', help='device ID, e.g. StanzaCulmone-01')
    group.add_argument('--room-label', help='parsed label, e.g. AB1 (site unknown)')
    group.add_argument('--all', action='store_true', help='all current device states')
    args = ap.parse_args()
    load_settings()
    db = connect_redis()
    if args.device:
        device_ids = [args.device]
    elif args.room_label:
        device_ids = sorted(db.smembers(f'iot:room_label:{args.room_label}'))
    else:
        device_ids = sorted(db.smembers('iot:devices'))
    for device_id in device_ids:
        value = db.get(f'latest:{device_id}')
        if value:
            print(json.dumps(json.loads(value), ensure_ascii=False, indent=2))
    print(f'{len(device_ids)} device ID(s); only latest state is kept.')


if __name__ == '__main__':
    main()
