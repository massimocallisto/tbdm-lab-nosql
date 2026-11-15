"""ArangoDB: observations plus an edge from device to parsed room label."""

from .config import setting
from .model import observation


def connect_arango():
    from arango import ArangoClient

    client = ArangoClient(hosts=setting('ARANGO_URL', 'http://127.0.0.1:8529'))
    password = setting('ARANGO_ROOT_PASSWORD')
    system = client.db('_system', username='root', password=password)
    name = setting('ARANGO_DATABASE', 'tbdm_iot')
    if not system.has_database(name):
        system.create_database(name)
    return client.db(name, username='root', password=password)


class ArangoStore:
    def __init__(self):
        self.db = connect_arango()
        for name in ('devices', 'room_labels', 'readings'):
            if not self.db.has_collection(name):
                self.db.create_collection(name)
        if not self.db.has_collection('has_room_label'):
            self.db.create_collection('has_room_label', edge=True)
        self.devices = self.db.collection('devices')
        self.rooms = self.db.collection('room_labels')
        self.edges = self.db.collection('has_room_label')
        self.readings = self.db.collection('readings')

    def save(self, reading):
        room = reading['room_id']
        device = reading['device_id']
        self.rooms.insert({'_key': room, 'label': room,
                           'location_verified': False}, overwrite_mode='ignore')
        self.devices.insert({'_key': device, 'device_id': device,
                             'sensor_id': reading['sensor_id']}, overwrite_mode='ignore')
        self.edges.insert({'_key': device,
                           '_from': f'devices/{device}',
                           '_to': f'room_labels/{room}'}, overwrite_mode='ignore')
        self.readings.insert(observation(reading))
