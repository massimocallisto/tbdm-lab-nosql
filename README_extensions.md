# Optional NoSQL lab extensions

These scripts are **reference solutions**, not required starting material.
Each imports the same six JSONL readings. The CSV has 15 device placements
across 10 physical rooms. The code assumes the repository's `.env`, Python
dependencies and Docker Compose services have already been prepared.

From the root of the existing repository:

```bash
docker compose up -d mongo arango redis
python -m extensions.mongo_example
python -m extensions.arango_example
python -m extensions.redis_example
```

Run them separately in any order. The first command starts the three databases;
the other commands use the credentials from the repository's `.env`.
The sample scripts write only into collections beginning with `exercise_`
and Redis keys beginning with `exercise:`; they leave the live MQTT
collections and keys alone. Re-running the scripts updates the sample readings.


To load the JSON-NL check this as example:

```
python -m iot_lab.publish_nl  # uses default file example/device_data-example.jsonl
python -m iot_lab.publish_nl --file path/to/your/file.jsonl
```

## Extension 1: MongoDB (documents plus an inventory join)

`mongo_example.py` imports the JSONL into `exercise_readings` and the CSV
into `exercise_topology`. It performs an aggregation by physical
building/floor/room and reports readings without a matched device in the CSV.

**Check:** TeamLab has two example readings with mean CO2 = 477. The example
device `AB1-02` is listed as **unmapped**, even though the CSV includes
`AB1-01`. The join compares the **original** device ID in the JSONL
(`raw_device_id`) with the CSV's `device` column; this also makes
`StanzaCulmone` match correctly.

**Student questions:** What changes if you group by `room` alone rather than
building, floor and room? Why would an hourly trend be uninformative when the
sample has only one reading per device?

## Extension 2: ArangoDB (building hierarchy)

`arango_example.py` creates a separate graph:

```text
building -> floor -> physical room -> device
```

These links come from the CSV inventory, not from the room label inferred from
the device name. The graph traversal finds devices with readings on
`polo_a / ground_floor`, then looks up their latest reading documents. A
second query finds devices that reported a reading but have no verified
placement in the CSV.

**Check:** `AA1-02`, `TeamLab-01` and `TeamLab-02` have example readings
on `polo_a / ground_floor`. `AB1-02` has a reading but no placement edge.
`StanzaCulmone` is normalized to the database device key
`StanzaCulmone-01` while keeping its original CSV name.

The CSV contains **no adjacency data**. It supports hierarchy and device
placement queries, but cannot answer which rooms are adjacent or find a
shortest route between rooms. Such exercises would need a new, explicit list
of physical links between rooms.

## Extension 3: Redis (current state and ranking)

`redis_example.py` stores the last received reading for every sensor and
maintains a sorted set of their CO2 values. It prints the three highest
values and lists the two devices whose parsed room label is TeamLab.

**Check:** With only the supplied JSONL, the top three are `B1-01` (518),
`StanzaCulmone-01` (488) and `TeamLab-01` (481). This is a ranking of
**latest received readings**, not a historical aggregate. Running the script
again with updated readings updates each device's score.
