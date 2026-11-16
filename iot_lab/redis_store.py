"""Redis: keep the last message received for each device.

This module provides a Redis-based storage solution for IoT device readings.
It maintains the latest sensor observation for each device and organizes
devices by room for efficient querying.
"""

import json

from .config import port, setting
from .model import observation


def connect_redis():
    """Establish a connection to the Redis server.
    
    Connects to Redis using configuration from environment settings with fallback
    defaults. The connection is configured to automatically decode responses as
    UTF-8 strings instead of returning bytes.
    
    Configuration parameters are retrieved from:
    - REDIS_HOST: The Redis server hostname (default: '127.0.0.1')
    - REDIS_PORT: The Redis server port (default: 6379)
    - REDIS_PASSWORD: The Redis server password (optional)
    
    Returns:
        redis.Redis: A connected Redis client instance with response decoding enabled.
    """
    import redis

    return redis.Redis(
        host=setting('REDIS_HOST', '127.0.0.1'),
        port=port('REDIS_PORT', 6379),
        password=setting('REDIS_PASSWORD'),
        decode_responses=True,
    )


class RedisStore:
    """A Redis-based storage backend for IoT device readings.
    
    This class manages storage of the most recent sensor observations from IoT devices
    in Redis. It maintains:
    - Latest readings for each device (using device_id as key)
    - A set of all active devices
    - Device grouping by room for efficient room-based queries
    
    Attributes:
        db (redis.Redis): The Redis client connection instance.
    """

    def __init__(self):
        """Initialize the RedisStore with a Redis connection.
        
        Establishes a connection to the Redis server using the configuration
        retrieved from environment settings.
        """
        self.db = connect_redis()

    def save(self, reading):
        """Store or update the latest sensor reading for a device.
        
        Persists the most recent observation from a device to Redis and maintains
        device inventory indices for efficient querying. This method performs three
        Redis operations:
        1. Stores the processed observation as a JSON string
        2. Registers the device in the global device set
        3. Associates the device with its room
        
        Args:
            reading (dict): The sensor reading data containing at minimum:
                - device_id (str): Unique identifier for the device
                - room_id (str): Identifier for the room where the device is located
                - Additional fields as defined by the observation model
        
        Note:
            The reading is processed through the observation() function to extract
            and format only relevant sensor data before storage.
        
        Example:
            >>> store = RedisStore()
            >>> reading = {
            ...     'device_id': 'AB1-01',
            ...     'room_id': 'room-42',
            ...     'collected_at': 1761955195,
            ...     'sensors': {'temperature': 22.5, 'humidity': 45}
            ... }
            >>> store.save(reading)
        """
        device_id = reading['device_id']
        # Store the processed observation as JSON for the device
        self.db.set(f'latest:{device_id}', json.dumps(observation(reading)))
        # Register device in the global device set
        self.db.sadd('iot:devices', device_id)
        # Associate device with its room for room-based queries
        self.db.sadd(f"iot:room_label:{reading['room_id']}", device_id)