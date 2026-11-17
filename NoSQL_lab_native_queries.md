# NoSQL lab: native queries for the IoT dataset

This optional activity uses the three databases already running in the IoT lab.
The commands are **read-only**: they let you inspect the same example readings
through MongoDB's document queries, ArangoDB's AQL, and Redis commands.

## Prepare the example data

From the root of `tbdm-lab-nosql`, after configuring `.env` and installing the
project's Python dependencies:

```bash
docker compose up -d mongo arango redis
python -m extensions.mongo_example
python -m extensions.arango_example
python -m extensions.redis_example
```

Copy `extensions/` and the example JSONL and topology CSV into the lab repository
first if they are not there. The commands above populate collections beginning
with `exercise_` and keys beginning with `exercise:`. You can run them again.
They do not require MQTT messages. If you use only the original MQTT receiver,
the collections and keys have different names: these queries then need adapting.

| Database | Client you can use | Local connection |
| --- | --- | --- |
| MongoDB | `mongosh` or MongoDB Compass | Host `127.0.0.1`, port from `MONGO_PORT` (default `27017`), username/password from `.env`, **authentication database `admin`**, data database `tbdm_iot` (or `MONGO_DATABASE`) |
| ArangoDB | Built-in web interface | `http://127.0.0.1:8529`, user `root`, password `ARANGO_ROOT_PASSWORD`, select database `tbdm_iot` (or `ARANGO_DATABASE`) |
| Redis | Redis Insight Workbench or `redis-cli` | Host `127.0.0.1`, port from `REDIS_PORT` (default `6379`), password `REDIS_PASSWORD` |

For `mongosh`, connect using the same settings, then type `use tbdm_iot`.
In MongoDB Compass, use **Documents** for filters; for an aggregation,
paste its stages into **Aggregations** rather than pasting the entire
`db.collection.aggregate(...)` command. Run the AQL examples in ArangoDB's
**Queries** editor. In Redis Insight, send one command at a time in **Workbench**.

The original JSONL contains `StanzaCulmone`, but the database scripts normalize
this key to **`StanzaCulmone-01`**. They retain `raw_device_id: "StanzaCulmone"`
in the stored reading. A label such as `AB1` alone does not establish a
physical location; only the separate CSV inventory provides a verified
building, floor and room association.

## MongoDB: documents and aggregations

Run these in `mongosh` after `use tbdm_iot`.

**1. Last reading for one sensor.** This query can return more than one
document if the source contains a longer history.

```javascript
db.exercise_readings.find(
  { device_id: "TeamLab-01" },
  { _id: 0, device_id: 1, collected_at: 1, "sensors.co2": 1 }
).sort({ collected_at: -1 }).limit(1)
```

**2. Readings whose CO2 value is at least 480.** The number is an exercise
filter, not a health or ventilation threshold.

```javascript
db.exercise_readings.find(
  { "sensors.co2": { $gte: 480 } },
  { _id: 0, device_id: 1, "sensors.co2": 1 }
).sort({ "sensors.co2": -1 })
```

**3. Average CO2 by parsed room label.** The `room_id` field is parsed from
the device name, so this grouping does *not* verify a physical location.

```javascript
db.exercise_readings.aggregate([
  { $group: {
      _id: "$room_id",
      readings: { $sum: 1 },
      average_co2: { $avg: "$sensors.co2" }
  } },
  { $sort: { _id: 1 } }
])
```

**4. Device readings absent from the CSV inventory.** Here MongoDB joins the
stored reading to `exercise_topology` using the *raw* ID from the JSONL.

```javascript
db.exercise_readings.aggregate([
  { $lookup: {
      from: "exercise_topology",
      localField: "raw_device_id",
      foreignField: "device",
      as: "placement"
  } },
  { $match: { placement: { $size: 0 } } },
  { $project: { _id: 0, raw_device_id: 1, device_id: 1 } }
])
```

With the supplied six readings, `TeamLab` has two readings and mean CO2 **477**;
`AB1-02` appears as unmapped because the CSV contains `AB1-01` but no `AB1-02`.

## ArangoDB: AQL on documents and graph edges

Run each query separately in the **Queries** editor of database `tbdm_iot`.

**1. Read the latest documents for a sensor.** AQL uses `FOR`, `FILTER`,
`SORT`, `LIMIT` and `RETURN` rather than MongoDB's cursor methods.

```aql
FOR reading IN exercise_readings
  FILTER reading.device_id == "TeamLab-01"
  SORT reading.collected_at DESC
  LIMIT 5
  RETURN {
    device: reading.device_id,
    time: reading.collected_at,
    co2: reading.sensors.co2
  }
```

**2. Follow a physical placement from the CSV.** The direction is `INBOUND`
because `exercise_contains` points from a room *to* its devices.

```aql
WITH exercise_rooms, exercise_devices
FOR room IN 1..1 INBOUND "exercise_devices/TeamLab-01" exercise_contains
  RETURN { room: room.name, room_id: room._id }
```

**3. Walk from a building to devices on the ground floor.** The traversal
passes through `building → floor → room → device`.

```aql
WITH exercise_buildings, exercise_floors, exercise_rooms, exercise_devices
FOR device, edge, path IN 3..3 OUTBOUND
    "exercise_buildings/polo_a" exercise_contains
  FILTER path.vertices[1].name == "ground_floor"
  SORT path.vertices[2].name, device._key
  RETURN {
    room: path.vertices[2].name,
    device: device._key
  }
```

This query lists *inventory placements*; some listed sensors have no reading
in the six-row JSONL. To see only sensors that reported, add a lookup of
`exercise_readings`, as in `extensions/arango_example.py`.

**4. Find reporting devices with no verified placement.** A `null` parent
means that the CSV provides no room edge for that sensor.

```aql
WITH exercise_rooms, exercise_devices
FOR device IN exercise_devices
  LET parent = FIRST(
    FOR room IN 1..1 INBOUND device._id exercise_contains
      RETURN room
  )
  LET reported = FIRST(
    FOR reading IN exercise_readings
      FILTER reading.device_id == device._key
      LIMIT 1
      RETURN reading
  )
  FILTER parent == null
  FILTER reported != null
  RETURN device._key
```

Expected from the sample: `AB1-02`. A similarly named sensor is **not**
automatically assigned the placement of `AB1-01`.

## Redis: commands on current state

Send these commands one by one in **Redis Insight Workbench** or an authenticated
`redis-cli` session. These keys are created by `extensions/redis_example.py`.

**1. Read a sensor's most recently received message.** `GET` returns a
JSON-encoded **string** in this lab; the Docker image does not include a
RedisJSON module.

```redis
GET exercise:latest:StanzaCulmone-01
```

**2. List devices with the parsed label `TeamLab`.** Set members have no
guaranteed output order.

```redis
SMEMBERS exercise:room_label:TeamLab
```

**3. Rank the three highest last-received CO2 readings.** A sorted set holds
one score per device. `REV` sorts from the highest score to the lowest.

```redis
ZRANGE exercise:co2:latest 0 2 REV WITHSCORES
```

Expected ranking: `B1-01` (**518**), `StanzaCulmone-01` (**488**) and
`TeamLab-01` (**481**). It is a ranking of **current state**, not an average
of historical measurements. The six-row example has one reading per device;
with a longer input, the script keeps the last *received* reading, which need
not have the newest `collected_at`.

**4. Inspect the stored data types.** Contrast a string, a set and a sorted
set (run each line separately).

```redis
TYPE exercise:latest:StanzaCulmone-01
TYPE exercise:room_label:TeamLab
TYPE exercise:co2:latest
```

## Questions to try

1. Which database answers “What was the last reading from `TeamLab-01`?”
   Which ones can answer “What were all its readings last week?”
2. Find the two `TeamLab` sensors in Redis; then find their *verified*
   placement through ArangoDB's CSV graph. What makes those answers different?
3. Locate `AB1-02` in MongoDB and ArangoDB. Why must you avoid assigning it
   to the room of `AB1-01`?
4. After adding a later reading for a device, compare the current Redis score
   with MongoDB's historical documents.

## Documentation

- [MongoDB: querying documents](https://www.mongodb.com/docs/manual/tutorial/query-documents/)
- [MongoDB: aggregation pipelines](https://www.mongodb.com/docs/manual/core/aggregation-pipeline/)
- [ArangoDB 3.12: graph traversals in AQL](https://docs.arango.ai/arangodb/3.12/aql/graph-queries/traversals/)
- [Redis: `GET`](https://redis.io/docs/latest/commands/get/), [`SMEMBERS`](https://redis.io/docs/latest/commands/smembers/) and [`ZRANGE`](https://redis.io/docs/latest/commands/zrange/)
