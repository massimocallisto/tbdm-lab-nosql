"""Join JSONL readings with the CSV inventory and group by physical room."""

from pprint import pprint

from iot_lab.config import load_settings
from iot_lab.mongo_store import connect_mongo

from .common import readings, topology_rows


def main():
    load_settings()
    db = connect_mongo()
    locations = db["exercise_topology"]
    samples = db["exercise_readings"]

    # Separate exercise collections keep the live MQTT readings untouched.
    for row in topology_rows():
        locations.replace_one({"_id": row["device"]},
                              {**row, "_id": row["device"]}, upsert=True)
    for number, reading in enumerate(readings(), start=1):
        samples.replace_one({"_id": f"sample_{number:05d}"},
                            {**reading, "_id": f"sample_{number:05d}"},
                            upsert=True)

    join = {
        "$lookup": {
            "from": "exercise_topology",
            "localField": "raw_device_id",
            "foreignField": "device",
            "as": "location",
        }
    }

    print("\nAverage CO2 by physical room (with unmatched readings):")
    pipeline = [
        join,
        {"$unwind": {"path": "$location", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": {
                "building": {"$ifNull": ["$location.building", "UNMAPPED"]},
                "floor": {"$ifNull": ["$location.floor", "UNMAPPED"]},
                "room": {"$ifNull": ["$location.room", "UNMAPPED"]},
            },
            "devices": {"$addToSet": "$raw_device_id"},
            "average_co2": {"$avg": "$sensors.co2"},
        }},
        {"$sort": {"_id.building": 1, "_id.floor": 1, "_id.room": 1}},
    ]
    for item in samples.aggregate(pipeline):
        pprint(item)

    print("\nReadings with no verified device placement:")
    for item in samples.aggregate([
        join,
        {"$match": {"location": {"$size": 0}}},
        {"$project": {"_id": 0, "raw_device_id": 1, "sensors.co2": 1}},
    ]):
        pprint(item)


if __name__ == "__main__":
    main()
