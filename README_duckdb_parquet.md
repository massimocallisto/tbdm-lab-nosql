# Optional extension: JSONL, DuckDB and Parquet

In this activity, you will use the same IoT readings in two file formats.
DuckDB reads the original newline-delimited JSON (`.jsonl`), extracts values
from `sensors`, stores the transformed readings in a DuckDB table and exports
them to a Parquet file. You will then ask the **same questions** of the raw
JSONL and of the Parquet file.

The activity runs locally. MQTT, MongoDB, Redis, ArangoDB and Docker are not
needed. The included `examples/device_data-example.jsonl` is enough to start;
you can later use a larger JSONL export with the same fields.

## Dataset

Use the JSONL already present in `examples/` or supply the path to another JSONL file.

From the repository root, activate your existing Python environment and run:

```bash
python -m pip install duckdb
python extensions/duckdb_parquet_lab.py \
  --input examples/device_data-example.jsonl \
  --device StanzaCulmone
```

On Windows PowerShell, put the command on one line (omit the backslashes).
The script writes `generated/duckdb_parquet/iot.duckdb` and
`generated/duckdb_parquet/readings.parquet`. It recreates its `readings` table
and replaces its Parquet output when run again. You can choose another output
directory with `--output-dir`.

## What to look for

1. **Read JSONL.** Examine how the fields under `sensors` become separate
   columns (for example, `co2` and `temperature`) in the DuckDB table. The original
   `collected_at` is a Unix timestamp in seconds; the example keeps that
   integer so that both files represent the same values.
2. **Export Parquet.** Find the new file `readings.parquet`. It holds the
   device, time and sensor columns in a columnar file format, not a separate database.
3. **Query both sources.** Compare the most recent readings for one device
   and the hourly averages across all devices. The results should agree.
4. **Inspect the plans (optional).** Add `--explain` to print DuckDB's plans
   for the hourly query on JSONL and Parquet. Look for the columns used by the
   Parquet scan. A plan shows how DuckDB intends to execute a query; it is not
   a benchmark.

Try the same steps with your own exported readings:

```bash
python extensions/duckdb_parquet_lab.py \
  --input path/to/my_readings.jsonl \
  --device AB1-01 \
  --explain
```

The input is a JSONL file with **one JSON object per line** and fields like:

```json
{"device_id":"AB1-01","collected_at":1761955195,"collected_at_tz":"2025-10-31T23:59:55","sensors":{"light":0,"co2":488,"temperature":21.62,"humidity":59.45,"tvoc":0,"eco2":400,"people_count":0}}
```

The device name is used exactly as it appears in the input. For instance,
`StanzaCulmone` is not renamed to `StanzaCulmone-01` in this activity.


## Further reading

- [DuckDB: Loading JSON](https://duckdb.org/docs/stable/data/json/loading_json)
- [DuckDB: Reading and Writing Parquet](https://duckdb.org/docs/stable/data/parquet/overview)
- [Apache Parquet: Concepts](https://parquet.apache.org/docs/concepts/)
