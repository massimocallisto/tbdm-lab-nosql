"""MongoDB: keep every received observation as a document."""

from .config import port, setting
from .model import observation


def connect_mongo():
    """
    Create a MongoDB database connection from application configuration.

    Initializes a MongoDB client using configured host, port, credentials, and the admin
    authentication source. Selects the configured database name, falling back to the
    default database name when no explicit configuration value is available.

    Returns:
        pymongo.database.Database: Selected MongoDB database handle.

    Raises:
        ImportError: If the pymongo package cannot be imported.
        pymongo.errors.ConfigurationError: If the MongoDB client configuration is invalid.
    """
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
    """
    Store reading observations in a MongoDB collection.

    Provides a MongoDB-backed persistence component for collected readings. The store
    uses the configured Mongo connection, selects the readings collection, and ensures
    an index optimized for device-based lookup ordered by collection time.

    Raises:
        ImportError: If the MongoDB driver cannot be imported.
        KeyError: If the configured Mongo connection does not provide the readings
            collection.
        pymongo.errors.PyMongoError: If MongoDB collection access or index creation
            fails.
    """
    def __init__(self):
        from pymongo import ASCENDING, DESCENDING

        self.readings = connect_mongo()['readings']
        self.readings.create_index([('device_id', ASCENDING),
                                    ('collected_at', DESCENDING)])

    def save(self, reading):
        self.readings.insert_one(observation(reading))
