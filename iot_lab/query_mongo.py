"""Query MongoDB history by device and interval, or show its newest reading."""

from __future__ import annotations

import argparse
import json

from .config import load_settings
from .mongo_store import connect_mongo


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--device', help='device ID, e.g. StanzaCulmone-01')
    ap.add_argument('--start', type=int, help='inclusive Unix timestamp in seconds')
    ap.add_argument('--end', type=int, help='inclusive Unix timestamp in seconds')
    ap.add_argument('--latest', action='store_true', help='return the newest matching reading')
    args = ap.parse_args()
    if args.start is not None and args.end is not None and args.start > args.end:
        ap.error('--start must be less than or equal to --end')
    load_settings()
    collection = connect_mongo()['readings']
    query = {}
    if args.device:
        query['device_id'] = args.device
    interval = {}
    if args.start is not None:
        interval['$gte'] = args.start
    if args.end is not None:
        interval['$lte'] = args.end
    if interval:
        query['collected_at'] = interval
    cursor = collection.find(query, {'_id': 0}).sort('collected_at', -1).limit(
        1 if args.latest else 50
    )
    count = 0
    for doc in cursor:
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        count += 1
    print(f'{count} reading(s) printed (max 50).')


if __name__ == '__main__':
    main()
