"""Publish one explicit JSON fixture as a smoke test; no message simulator."""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

from .config import ROOT, load_settings, port, setting


def main() -> None:
    import paho.mqtt.client as mqtt

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--file', type=Path, default=ROOT / 'examples' / 'message.json')
    args = ap.parse_args()
    load_settings()
    payload = args.file.read_text(encoding='utf-8')
    obj = json.loads(payload)
    topic = f"/sensors/{obj['device_id']}/data"
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id=f'tbdm-one-shot-{uuid.uuid4().hex[:8]}')
    client.username_pw_set(setting('MQTT_USERNAME'), setting('MQTT_PASSWORD'))
    client.connect(setting('MQTT_HOST', '127.0.0.1'), port('MQTT_PORT', 1883))
    client.loop_start()
    try:
        info = client.publish(topic, payload, qos=1, retain=False)
        info.wait_for_publish(timeout=10)
        if not info.is_published():
            raise RuntimeError('Publish not confirmed within 10 seconds')
        print(f'Published one message to {topic} (not retained).')
    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == '__main__':
    main()
