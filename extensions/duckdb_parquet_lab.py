"""Compare the same IoT queries on JSONL and a Parquet export."""

import argparse
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parent.parent


def sql_path(path: Path) -> str:
    """Quote a local filename as a DuckDB SQL string literal."""
    return "'" + str(path.resolve()).replace("'", "''") + "'"


def show_rows(title, rows):
    print(f"\n{title}")
    for row in rows:
        print("  " + " | ".join(str(value) for value in row))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "examples" / "device_data-example.jsonl",
        help="JSONL readings exported from the IoT sensors",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "generated" / "duckdb_parquet",
        help="Where to write the DuckDB database and Parquet file",
    )
    parser.add_argument(
        "--device",
        help="Device to inspect; defaults to the first device in the input",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Print the two physical plans for the hourly query",
    )
    args = parser.parse_args()

    input_file = args.input.resolve()
    if not input_file.is_file():
        parser.error(f"Input file not found: {input_file}")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    parquet_file = output_dir / "readings.parquet"
    database_file = output_dir / "iot.duckdb"

    # The same transformation is used for the stored table and the JSONL queries.
    json_source = f"""
        SELECT device_id, collected_at, collected_at_tz,
               sensors.light AS light,
               sensors.co2 AS co2,
               sensors.temperature AS temperature,
               sensors.humidity AS humidity,
               sensors.tvoc AS tvoc,
               sensors.eco2 AS eco2,
               sensors.people_count AS people_count
        FROM read_ndjson({sql_path(input_file)})
    """
    parquet_source = f"SELECT * FROM read_parquet({sql_path(parquet_file)})"

    with duckdb.connect(str(database_file)) as con:
        con.execute("SET TimeZone = 'UTC'")
        con.execute("CREATE OR REPLACE TABLE readings AS " + json_source)
        con.execute(
            f"COPY readings TO {sql_path(parquet_file)} "
            "(FORMAT PARQUET, OVERWRITE_OR_IGNORE TRUE)"
        )

        count = con.execute("SELECT count(*) FROM readings").fetchone()[0]
        if count == 0:
            print("The input contains no readings.")
            return

        device = args.device or con.execute(
            "SELECT device_id FROM readings LIMIT 1"
        ).fetchone()[0]
        print(f"Imported {count} readings into {database_file}")
        print(f"Exported Parquet file: {parquet_file}")

        # Query 1: one device, latest readings. This query is identical on
        # both sources; only the source format changes.
        history = """
            SELECT device_id, collected_at, co2, temperature
            FROM ({source}) AS readings
            WHERE device_id = ?
            ORDER BY collected_at DESC
            LIMIT 5
        """

        # Query 2: an analytical scan over all devices and hours.
        hourly = """
            SELECT date_trunc('hour', to_timestamp(collected_at)) AS hour,
                   count(*) AS readings,
                   round(avg(co2), 2) AS avg_co2,
                   round(avg(temperature), 2) AS avg_temperature
            FROM ({source}) AS readings
            GROUP BY 1
            ORDER BY 1
        """

        for label, source in (("JSONL", json_source), ("Parquet", parquet_source)):
            show_rows(
                f"{label}: latest readings for {device}",
                con.execute(history.format(source=source), [device]).fetchall(),
            )
            show_rows(
                f"{label}: hourly averages (UTC)",
                con.execute(hourly.format(source=source)).fetchall(),
            )
            if args.explain:
                plan = con.execute("EXPLAIN " + hourly.format(source=source)).fetchone()
                print(f"\n{label}: plan for hourly averages\n{plan[-1]}")


if __name__ == "__main__":
    main()
