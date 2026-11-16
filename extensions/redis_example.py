"""Maintain a current CO2 ranking and a room-label index with Redis."""

import json

from iot_lab.config import load_settings
from iot_lab.redis_store import connect_redis

from .common import readings


def main():
    load_settings()
    db = connect_redis()

    for reading in readings():
        device = reading["device_id"]
        db.set("exercise:latest:" + device, json.dumps(reading))
        db.sadd("exercise:room_label:" + reading["room_id"], device)
        db.zadd("exercise:co2:latest", {device: reading["sensors"]["co2"]})

    print("\nThree highest last-received CO2 readings:")
    for device, co2 in db.zrange(
        "exercise:co2:latest", 0, 2, desc=True, withscores=True
    ):
        print(device, co2)

    print("\nDevices with the parsed room label TeamLab:")
    for device in sorted(db.smembers("exercise:room_label:TeamLab")):
        print(device, json.loads(db.get("exercise:latest:" + device))["sensors"])


if __name__ == "__main__":
    main()
