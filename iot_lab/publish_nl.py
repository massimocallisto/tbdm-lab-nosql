
"""Publish JSON objects from a JSONL file; each line is published as a separate message."""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

from .config import ROOT, load_settings, port, setting


def main() -> None:
    import paho.mqtt.client as mqtt

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--file', type=Path, default=ROOT / 'examples' / 'device_data-example.jsonl')
    args = ap.parse_args()
    load_settings()
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id=f'tbdm-nl-publisher-{uuid.uuid4().hex[:8]}')
    client.username_pw_set(setting('MQTT_USERNAME'), setting('MQTT_PASSWORD'))
    client.connect(setting('MQTT_HOST', '127.0.0.1'), port('MQTT_PORT', 1883))
    client.loop_start()
    
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            message_count = 0
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    obj = json.loads(line)
                    payload = json.dumps(obj)
                    topic = f"/sensors/{obj['device_id']}/data"
                    
                    info = client.publish(topic, payload, qos=1, retain=False)
                    info.wait_for_publish(timeout=10)
                    
                    if not info.is_published():
                        print(f'Warning: Publish not confirmed for line {line_num}')
                    else:
                        message_count += 1
                        print(f'Published message {message_count} to {topic}')
                
                except json.JSONDecodeError as e:
                    print(f'Error: Invalid JSON on line {line_num}: {e}')
                except KeyError:
                    print(f'Error: Missing device_id on line {line_num}')
                except Exception as e:
                    print(f'Error publishing line {line_num}: {e}')
        
        print(f'\nSuccessfully published {message_count} messages from {args.file}')
    
    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == '__main__':
    main()
