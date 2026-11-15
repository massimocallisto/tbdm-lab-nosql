"""Query ArangoDB reading documents and device → room-label graph edges."""

from __future__ import annotations

import argparse
import json

from .arango_store import connect_arango
from .config import load_settings


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--device', help='canonical device ID for reading history')
    ap.add_argument('--room-label', help='devices with parsed label, not verified colocated devices')
    ap.add_argument('--start', type=int, help='inclusive Unix timestamp in seconds')
    ap.add_argument('--end', type=int, help='inclusive Unix timestamp in seconds')
    args = ap.parse_args()
    if args.start is not None and args.end is not None and args.start > args.end:
        ap.error('--start must be less than or equal to --end')
    load_settings()
    db = connect_arango()
    if args.room_label:
        # The edge points from Device to RoomLabel; query it in reverse.
        query = '''WITH devices, room_labels
        FOR room IN room_labels
          FILTER room._key == @room
          FOR device IN 1..1 INBOUND room._id has_room_label
            RETURN {device: device.device_id,
                    room_label: room.label, location_verified: room.location_verified}'''
        results = db.aql.execute(query, bind_vars={'room': args.room_label})
    else:
        query = '''FOR reading IN readings
          FILTER @device == null OR reading.device_id == @device
          FILTER @start == null OR reading.collected_at >= @start
          FILTER @end == null OR reading.collected_at <= @end
          SORT reading.collected_at DESC
          LIMIT 50
          RETURN UNSET(reading, "_id", "_key", "_rev")'''
        results = db.aql.execute(query, bind_vars={
            'device': args.device, 'start': args.start, 'end': args.end,
        })
    count = 0
    for item in results:
        print(json.dumps(item, ensure_ascii=False, indent=2))
        count += 1
    print(f'{count} result(s). A room label alone does not identify a site or floor.')


if __name__ == '__main__':
    main()
