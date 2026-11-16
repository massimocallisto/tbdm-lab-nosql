"""Read the two example files using only the Python standard library."""

import csv
import json
from pathlib import Path

from iot_lab.model import observation, parse_message


ROOT = Path(__file__).resolve().parent.parent
TOPOLOGY = ROOT / "examples" / "building_topology.csv"
JSONL = ROOT / "examples" / "device_data-example.jsonl"


def normalize_device_id(raw_id):
    """Match the device key produced by iot_lab.model.parse_message."""
    parts = raw_id.rsplit("-", 1)
    return raw_id if len(parts) == 2 and parts[1].isdigit() else raw_id + "-01"


def topology_rows():
    # The supplied CSV uses semicolons, not commas.
    with TOPOLOGY.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file, delimiter=";"))


def readings():
    result = []
    with JSONL.open(encoding="utf-8-sig") as file:
        for line in file:
            if not line.strip():
                continue
            original = json.loads(line)
            topic = f"/sensors/{original['device_id']}/data"
            result.append(observation(parse_message(topic, line)))
    return result
