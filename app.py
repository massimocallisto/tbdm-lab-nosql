"""Start the MQTT lab: python app.py --model redis|mongo|arango|all."""

import argparse

import paho.mqtt.client as mqtt

from iot_lab.config import load_settings, port, setting
from iot_lab.model import parse_message


def main():
    parser = argparse.ArgumentParser(description='MQTT + NoSQL teaching lab')
    parser.add_argument('--model', choices=['console', 'redis', 'mongo', 'arango', 'all'],
                        default='console')
    args = parser.parse_args()
    load_settings()

    # Connect only to the database(s) selected for this exercise.
    stores = []
    if args.model in ('redis', 'all'):
        from iot_lab.redis_store import RedisStore
        stores.append(RedisStore())
    if args.model in ('mongo', 'all'):
        from iot_lab.mongo_store import MongoStore
        stores.append(MongoStore())
    if args.model in ('arango', 'all'):
        from iot_lab.arango_store import ArangoStore
        stores.append(ArangoStore())

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(setting('MQTT_USERNAME'), setting('MQTT_PASSWORD'))

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            topic = setting('MQTT_TOPIC_FILTER', '/sensors/+/data')
            client.subscribe(topic, qos=1)
            print(f'Subscribed to {topic}', flush=True)
        else:
            print(f'MQTT connection failed: {reason_code}', flush=True)

    def on_message(client, userdata, mqtt_message):
        reading = parse_message(mqtt_message.topic, mqtt_message.payload)
        print(f"topic: {reading['topic']}")
        print(f"message_json: {reading['message_json']}")
        print(f"room_id: {reading['room_id']}")
        print(f"sensor_id: {reading['sensor_id']}")
        for store in stores:
            store.save(reading)
        print('---', flush=True)

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(setting('MQTT_HOST', '127.0.0.1'), port('MQTT_PORT', 1883))
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        client.disconnect()


if __name__ == '__main__':
    main()
