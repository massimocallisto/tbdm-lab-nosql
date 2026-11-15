"""Turn one MQTT message into the room and sensor IDs used in the lab."""

import json


def parse_message(topic, payload):
    message_json = json.loads(payload)
    raw_device_id = message_json['device_id']

    # Only a final -<number> is interpreted as a sensor number.
    parts = raw_device_id.rsplit('-', 1)
    if len(parts) == 2 and parts[1].isdigit():
        room_id, sensor_id = parts
    else:
        room_id, sensor_id = raw_device_id, '01'

    return {
        'topic': topic,
        'message_json': message_json,
        'room_id': room_id,  # parsed label; site and floor are unknown
        'sensor_id': sensor_id,
        'device_id': f'{room_id}-{sensor_id}',
    }


def observation(reading):
    """Fields shared by the three database examples."""
    message = reading['message_json']
    return {
        'topic': reading['topic'],
        'raw_device_id': message['device_id'],
        'device_id': reading['device_id'],
        'room_id': reading['room_id'],
        'sensor_id': reading['sensor_id'],
        'collected_at': message['collected_at'],
        'collected_at_tz': message['collected_at_tz'],
        'sensors': message['sensors'],
    }
