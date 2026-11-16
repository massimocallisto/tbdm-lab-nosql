"""Build a small building > floor > room > device graph and traverse it."""

from pprint import pprint

from iot_lab.arango_store import connect_arango
from iot_lab.config import load_settings

from .common import normalize_device_id, readings, topology_rows


def insert_once(collection, document):
    collection.insert(document, overwrite_mode="ignore")


def main():
    load_settings()
    db = connect_arango()
    names = ("exercise_buildings", "exercise_floors", "exercise_rooms",
             "exercise_devices", "exercise_readings")
    for name in names:
        if not db.has_collection(name):
            db.create_collection(name)
    if not db.has_collection("exercise_contains"):
        db.create_collection("exercise_contains", edge=True)

    buildings = db.collection("exercise_buildings")
    floors = db.collection("exercise_floors")
    rooms = db.collection("exercise_rooms")
    devices = db.collection("exercise_devices")
    samples = db.collection("exercise_readings")
    edges = db.collection("exercise_contains")

    for row in topology_rows():
        building = row["building"]
        floor_key = f"{building}__{row['floor']}"
        room_key = f"{floor_key}__{row['room']}"
        device_key = normalize_device_id(row["device"])

        insert_once(buildings, {"_key": building, "name": building})
        insert_once(floors, {"_key": floor_key, "name": row["floor"]})
        insert_once(rooms, {"_key": room_key, "name": row["room"]})
        insert_once(devices, {"_key": device_key, "raw_device_id": row["device"]})
        insert_once(edges, {
            "_key": "floor_" + floor_key,
            "_from": "exercise_buildings/" + building,
            "_to": "exercise_floors/" + floor_key,
        })
        insert_once(edges, {
            "_key": "room_" + room_key,
            "_from": "exercise_floors/" + floor_key,
            "_to": "exercise_rooms/" + room_key,
        })
        insert_once(edges, {
            "_key": "device_" + device_key,
            "_from": "exercise_rooms/" + room_key,
            "_to": "exercise_devices/" + device_key,
        })

    for number, reading in enumerate(readings(), start=1):
        # A reporting device is kept even when it is absent from the CSV.
        insert_once(devices, {"_key": reading["device_id"],
                              "raw_device_id": reading["raw_device_id"]})
        samples.insert({"_key": f"sample_{number:05d}", **reading},
                       overwrite_mode="replace")

    print("\nLatest readings on the ground floor of polo_a:")
    query = """
    WITH exercise_buildings, exercise_floors, exercise_rooms, exercise_devices
    FOR device, edge, path IN 3..3 OUTBOUND
        CONCAT("exercise_buildings/", @building) exercise_contains
      FILTER path.vertices[1].name == @floor
      LET latest = FIRST(
        FOR reading IN exercise_readings
          FILTER reading.device_id == device._key
          SORT reading.collected_at DESC
          LIMIT 1
          RETURN reading
      )
      FILTER latest != null
      SORT path.vertices[2].name, device._key
      RETURN {
        room: path.vertices[2].name,
        device: device._key,
        co2: latest.sensors.co2
      }
    """
    for item in db.aql.execute(query, bind_vars={
        "building": "polo_a", "floor": "ground_floor"
    }):
        pprint(item)

    print("\nReporting devices with no room in the CSV:")
    query = """
    WITH exercise_buildings, exercise_floors, exercise_rooms, exercise_devices
    FOR device IN exercise_devices
      LET parent = FIRST(
        FOR room IN 1..1 INBOUND device._id exercise_contains
          RETURN room
      )
      FILTER parent == null
      RETURN device._key
    """
    for device in db.aql.execute(query):
        print(device)


if __name__ == "__main__":
    main()
