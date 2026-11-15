"""Optional student starter: receive MQTT readings and add a database."""

import paho.mqtt.client as mqtt

from iot_lab.config import load_settings, port, setting
from iot_lab.model import parse_message


def main():
    load_settings()

    # TODO: create one RedisStore, MongoStore or ArangoStore here.
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(setting('MQTT_USERNAME'), setting('MQTT_PASSWORD'))

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            client.subscribe(setting('MQTT_TOPIC_FILTER', '/sensors/+/data'), qos=1)
            print('Subscribed to MQTT sensor messages', flush=True)

    def on_message(client, userdata, mqtt_message):
        reading = parse_message(mqtt_message.topic, mqtt_message.payload)
        print(reading)
        # TODO: save reading in the selected database.

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(setting('MQTT_HOST', '127.0.0.1'), port('MQTT_PORT', 1883))
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        client.disconnect()


if __name__ == '__main__':
    main()
