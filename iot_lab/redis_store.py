"""Redis: keep the last message received for each device."""

import json

from .config import port, setting
from .model import observation


def connect_redis():
    import redis

    return redis.Redis(
        host=setting('REDIS_HOST', '127.0.0.1'),
        port=port('REDIS_PORT', 6379),
        password=setting('REDIS_PASSWORD'),
        decode_responses=True,
    )


class RedisStore:
    def __init__(self):
        self.db = connect_redis()

    def save(self, reading):
        device_id = reading['device_id']
        self.db.set(f'latest:{device_id}', json.dumps(observation(reading)))
        self.db.sadd('iot:devices', device_id)
        self.db.sadd(f"iot:room_label:{reading['room_id']}", device_id)
