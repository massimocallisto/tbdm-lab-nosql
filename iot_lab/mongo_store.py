"""MongoDB: keep every received observation as a document."""

from .config import port, setting
from .model import observation


def connect_mongo():
    from pymongo import MongoClient

    client = MongoClient(
        host=setting('MONGO_HOST', '127.0.0.1'),
        port=port('MONGO_PORT', 27017),
        username=setting('MONGO_USERNAME'),
        password=setting('MONGO_PASSWORD'),
        authSource='admin',
    )
    return client[setting('MONGO_DATABASE', 'tbdm_iot')]


class MongoStore:
    def __init__(self):
        from pymongo import ASCENDING, DESCENDING

        self.readings = connect_mongo()['readings']
        self.readings.create_index([('device_id', ASCENDING),
                                    ('collected_at', DESCENDING)])

    def save(self, reading):
        self.readings.insert_one(observation(reading))
