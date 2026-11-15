# MQTT and NoSQL: introductory IoT laboratory

This project shows the **same IoT readings** in three NoSQL models:

| Database | What we store | Example question |
| --- | --- | --- |
| Redis (key–value) | Last message received from each sensor | What was its last received reading? |
| MongoDB (documents) | All received readings | What is the sensor's history? |
| ArangoDB (graph + documents) | Device → room-label links and readings | Which devices have the label AB1? |

Python 3.11+ and Docker Compose v2 are needed. Python runs on the host;
Compose starts an authenticated MQTT broker and the databases on localhost.
There is no continuous simulator. A small program can publish **one message**
when you explicitly run it. The files in `examples/` include the supplied
real reading (`message.json`) and three **invented teaching examples**.

## Start in five steps

Open a terminal in the directory containing `app.py`.

1. Copy `.env.example` to `.env` and change the four example passwords
   (MQTT, Redis, MongoDB and ArangoDB). On macOS/Linux:

   ```bash
   cp .env.example .env
   ```

2. Create the MQTT password file and start the services:

   ```bash
   docker compose --profile setup run --rm broker-init
   docker compose up -d
   ```

3. Prepare Python:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

   On Windows, activate with `.venv\Scripts\activate`. If a database has
   not finished starting, wait a moment and retry the command that connects.

4. **Keep this terminal open** and run the application:

   ```bash
   python app.py --model console
   ```

5. In a **second terminal**, activate the same Python environment and publish
   the included example once:

   ```bash
   python -m iot_lab.publish_once
   ```

The received message prints its MQTT topic, JSON message, parsed room label,
and sensor number. The publisher sends non-retained messages: start
`app.py` before publishing.

## Try one storage model at a time

Stop `app.py` with Ctrl+C, then run a model and publish a message again:

| Model | Start receiver | Ask a question |
| --- | --- | --- |
| Redis | `python app.py --model redis` | `python -m iot_lab.query_redis --all` |
| MongoDB | `python app.py --model mongo` | `python -m iot_lab.query_mongo --device StanzaCulmone-01` |
| ArangoDB | `python app.py --model arango` | `python -m iot_lab.query_arango --room-label StanzaCulmone` |

You can also run `python app.py --model all` to write each received message
to every database. To compare two sensors carrying the same room label,
publish these **invented** messages one at a time while `app.py` runs:

```bash
python -m iot_lab.publish_once --file examples/ab1_01.json
python -m iot_lab.publish_once --file examples/ab1_02.json
```

Then try `python -m iot_lab.query_arango --room-label AB1` if the ArangoDB
model was running, or `python -m iot_lab.query_redis --room-label AB1` for
Redis.

For the history of a single sensor over a time interval (Unix seconds):

```bash
python -m iot_lab.query_redis --device AB1-01
python -m iot_lab.query_mongo --device AB1-01 --start 1761955100 --end 1761955300
python -m iot_lab.query_arango --device AB1-01 --start 1761955100 --end 1761955300
```

Each query accepts `--help`. To see how Redis differs from MongoDB, publish
the original `examples/message.json` and then the invented
`examples/stanza_culmone_later.json`. Redis retains **only the last message
received** for this sensor; MongoDB retains both.

## The four values returned by the MQTT parser

`iot_lab/model.py` has one short function, `parse_message(topic, payload)`.
It returns a Python dictionary containing:

```python
{
    "topic": "/sensors/AB1-01/data",
    "message_json": {"device_id": "AB1-01", "...": "..."},
    "room_id": "AB1",
    "sensor_id": "01",
    "device_id": "AB1-01"
}
```

The fifth field is a convenient normalized key for the databases.
`AB1-02` becomes room label `AB1`, sensor `02`. A name without a numbered
suffix, such as `StanzaCulmone`, gets sensor number `01` and the normalized
device key `StanzaCulmone-01`. The original `device_id` is kept in the
JSON and in each stored observation.

The parser assumes messages on the lab topics are well formed. It does not
check the topic against `device_id` or validate every measurement. This
keeps the first exercise focused on the data models. The MQTT subscriber
is in **`app.py`**; 

### The starter file

The file **`app_starter.py`** is a smaller optional starting point
with TODOs for adding persistence. The `iot_lab/*_store.py` modules and
`app.py` are working reference examples.

### What the room label does *not* tell us

In the course scenario, `AB1` can occur in different sites. Its parsed
label alone does **not** identify the physical room, site or floor. The
ArangoDB edge means *device has parsed room label*, and the label vertex has
`location_verified: false`. It does not mean *installed in this verified
room*. More location information would be needed for that relationship.

## Short activity

1. Run `app_starter.py` and identify the four main parsed values.
2. Add one store from `iot_lab/` and save a received reading.
3. Run the corresponding query under `iot_lab/` and explain what the model makes easy.
4. Try a second model and compare its answer. Why can Redis not return
   the complete history? What is the limit of the graph's room label?

Optional activities
A. Stream the dataset from the JSON-NL file available at the [following link](https://unicamit-my.sharepoint.com/:u:/g/personal/dtmassimo_callisto_unicam_it/IQANovbf79LNRrSjjpK4BwbCAabOHgyMuLVJOSXD9n0u6Ts?e=kXEASz). 
B. Use the file [examples/building_topology.csv](examples/building_topology.csv) to handle relations in the graph database storage.
B. Implement a simple simulator to stream live data over MQTT.

## Notes

- The receiver is deliberately small. It assumes correct input and does not
  provide durable retries or exactly-once database writes. Publishing the
  same reading again produces another document in MongoDB and ArangoDB.
- Redis is the **last arrival**, not necessarily the reading with the newest
  `collected_at` timestamp. That distinction can be discussed in class.
- `collected_at_tz` is stored exactly as received. Its text has no explicit
  offset, so it should not be interpreted as a verified timezone.
- Run `python -m unittest discover -s tests -v` for the local parser and
  database-shape tests. `docker compose down` stops containers while
  preserving volumes; `docker compose down -v` also deletes local lab data.
- If you change MQTT credentials, run `broker-init` again and restart the
  broker. ArangoDB initializes its root password on a fresh data volume.
  Keep `.env` and `mosquitto/passwords` private; neither is in this ZIP.
