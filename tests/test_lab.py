"""Focused checks for the device naming convention and stored data."""

import json
import unittest
from pathlib import Path

from iot_lab.model import observation, parse_message

ROOT = Path(__file__).resolve().parents[1]


class ParsingTests(unittest.TestCase):
    def test_real_example_without_sensor_suffix(self):
        payload = (ROOT / 'examples' / 'message.json').read_bytes()
        reading = parse_message('/sensors/StanzaCulmone/data', payload)
        self.assertEqual((reading['room_id'], reading['sensor_id']),
                         ('StanzaCulmone', '01'))
        self.assertEqual(reading['device_id'], 'StanzaCulmone-01')
        stored = observation(reading)
        self.assertEqual(stored['raw_device_id'], 'StanzaCulmone')
        self.assertEqual(stored['sensors']['co2'], 488)

    def test_two_sensors_in_one_room_label(self):
        for number in ('01', '02'):
            payload = json.dumps({'device_id': f'AB1-{number}',
                                  'collected_at': 1761955195,
                                  'collected_at_tz': '2025-10-31T23:59:55',
                                  'sensors': {'co2': 488}})
            reading = parse_message(f'/sensors/AB1-{number}/data', payload)
            self.assertEqual(reading['room_id'], 'AB1')
            self.assertEqual(reading['sensor_id'], number)
            self.assertEqual(reading['device_id'], f'AB1-{number}')
            self.assertNotIn('site', observation(reading))


if __name__ == '__main__':
    unittest.main()
