"""Verify the useful relationships in the two supplied teaching datasets."""

import unittest

from extensions.common import normalize_device_id, readings, topology_rows


class ExampleDataTests(unittest.TestCase):
    def test_sample_and_inventory_link_by_raw_device_id(self):
        inventory = topology_rows()
        samples = readings()
        self.assertEqual((len(inventory), len(samples)), (15, 6))
        mapped = {row["device"] for row in inventory}
        unmapped = {r["raw_device_id"] for r in samples} - mapped
        self.assertEqual(unmapped, {"AB1-02"})

    def test_room_aggregation_and_normalization(self):
        inventory = {r["device"]: r for r in topology_rows()}
        samples = readings()
        teamlab = [r["sensors"]["co2"] for r in samples
                   if inventory.get(r["raw_device_id"], {}).get("room") == "TeamLab"]
        self.assertEqual(sum(teamlab) / len(teamlab), 477)
        self.assertEqual(normalize_device_id("StanzaCulmone"), "StanzaCulmone-01")
        self.assertEqual(normalize_device_id("AB1-02"), "AB1-02")


if __name__ == "__main__":
    unittest.main()
