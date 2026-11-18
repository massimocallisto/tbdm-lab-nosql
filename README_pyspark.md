# PySpark lab: exploring IoT sensor data

## Context and goal

In the previous labs, we collected IoT readings and considered how to store and query them with different NoSQL models. This exercise looks at a different question: **how can we process a collection of stored readings to produce an analytical result?**

We will use PySpark DataFrames to read JSON Lines, select and filter measurements, calculate summaries, express a query in Spark SQL, and save the result as Parquet. The final Parquet dataset can be read again by Spark or explored with DuckDB. The example file has only six readings: it helps us understand the operations, but it cannot demonstrate a performance advantage from distributed processing.

The sections build on one another. Run the setup first, then execute the examples in order in a PySpark shell or notebook. Paths are relative to the project directory.

```text
project/
├── examples/
│   └── device_data-example.jsonl
└── output/                        # Created when we write the result
```

Each line of `device_data-example.jsonl` contains one reading, including `device_id`, `collected_at_tz`, and a nested `sensors` object. Spark reads these JSON Lines into a DataFrame and infers a schema. The text in `collected_at_tz` has no explicit timezone offset; this lab uses its displayed date and time without claiming a verified timezone.

## Start a Spark session

If your PySpark shell or notebook already provides a `spark` session, use that session and run only the imports. Otherwise, create one locally:

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, count, max, min, round, to_timestamp

spark = SparkSession.builder.master("local[*]").appName("IoT batch lab").getOrCreate()
```

### Optional warm-up: select, filter, summarize

This independent example uses `examples/accounts.csv` **only if that separate file was provided**. It selects two columns, keeps accounts with a positive balance, and displays summary statistics. It introduces the same DataFrame operations that we will apply to the IoT readings. Skip it if you only have the IoT file.

```python
accounts = spark.read.csv("examples/accounts.csv", header=True, inferSchema=True)

filtered_accounts = (
    accounts.select("AccountBalance", "CountOfDependents")
    .filter(col("AccountBalance") > 0)
)

filtered_accounts.summary().show()
```

## Load the IoT readings

Read the JSON Lines file once and reuse the resulting DataFrame in the examples below. `printSchema()` reveals that the measurement fields are inside the `sensors` structure.

```python
df = spark.read.json("examples/device_data-example.jsonl")
df.printSchema()
```

### Example 1 — Select a column

`select()` keeps only `device_id` and `show()` displays the result. Each output row still represents a reading: if a device has several readings, its identifier can appear several times. Use `distinct()` only when you specifically want a list of unique devices.

```python
devices = df.select("device_id")
devices.show()
```

### Example 2 — Filter one device

`filter()` keeps only readings whose `device_id` matches `TeamLab-02`. This is the basic pattern for inspecting one sensor's history. In our small sample there is one matching reading.

```python
dev1 = df.filter(col("device_id") == "TeamLab-02")
dev1.show()
```

### Example 3 — Filter several devices

`isin()` selects readings from either `AB1-02` or `AA1-02`. Unlike the previous example, a single condition can name several devices without repeating the comparison.

```python
rooms = ["AB1-02", "AA1-02"]
df_rooms = df.filter(col("device_id").isin(rooms))
df_rooms.show()
```

These identifiers name **devices** in the data. A verified physical location would require the topology information used in the earlier lab.

### Example 4 — Filter a nested measurement

`sensors.co2` accesses the `co2` field inside the nested `sensors` object. The filter keeps readings above 500. With the provided six-row file, this returns the reading from `B1-01`.

```python
df_co2_high = df.filter(col("sensors.co2") > 500)
df_co2_high.show()
```

### Example 5 — Combine conditions

The `&` operator requires **all three** conditions to be true: the device is `TeamLab-02`, CO₂ exceeds 400, and temperature exceeds 22.0. Parentheses around each comparison are required when combining Spark column expressions.

```python
df_warning = df.filter(
    (col("device_id") == "TeamLab-02")
    & (col("sensors.co2") > 400)
    & (col("sensors.temperature") > 22.0)
)
df_warning.show()
```

The thresholds here are **exercise conditions**, not an operational air-quality alert policy.

### Example 6 — Work with a time window

`to_timestamp()` converts the time string into a Spark timestamp column. The filter selects readings from 23:00 on 31 October up to, but not including, midnight. All six supplied readings fall within this interval, so this example illustrates the syntax rather than a selective result.

```python
df_temp = df.withColumn("timestamp", to_timestamp(col("collected_at_tz")))

df_evening = df_temp.filter(
    (col("timestamp") >= "2025-10-31 23:00:00")
    & (col("timestamp") < "2025-11-01 00:00:00")
)
df_evening.show()
```

### Example 7 — Aggregate by device

`groupBy()` collects readings for the same device into one group. `agg()` then calculates its mean and highest CO₂ reading, together with mean temperature. Because the sample contains only one reading per device, each mean currently equals that reading's value; multiple readings per device would make the aggregation more informative.

```python
df_stats = df.groupBy("device_id").agg(
    avg("sensors.co2").alias("mean_co2"),
    max("sensors.co2").alias("highest_co2"),
    avg("sensors.temperature").alias("mean_temperature"),
)
df_stats.show()
```

### Example 8 — Query nested data with Spark SQL

`createOrReplaceTempView()` gives the DataFrame a name for SQL queries in the current Spark session. This query selects the time and two nested measurements, filters CO₂ readings above 500, and sorts them from highest to lowest. It expresses the same kind of selection as Example 4 using SQL.

```python
df.createOrReplaceTempView("readings")

spark.sql("""
    SELECT device_id, collected_at_tz, sensors.co2, sensors.temperature
    FROM readings
    WHERE sensors.co2 > 500
    ORDER BY sensors.co2 DESC
""").show()
```

### Example 9 — Flatten the sensor structure

`sensors.*` selects every field from the nested `sensors` object as a top-level column. The resulting table has columns such as `co2`, `temperature`, and `humidity`, which are easier to use in aggregations and downstream analysis. `printSchema()` lets you compare the flattened schema with the original one.

```python
df_flat = df.select(
    col("device_id"),
    col("collected_at_tz"),
    col("sensors.*"),
)

df_flat.printSchema()
df_flat.show(5)
```

### Example 10 — Summarize with the DataFrame API

Starting from `df_flat`, this aggregation counts readings per device and calculates CO₂ and temperature statistics. The aliases name the output columns. `show()` triggers execution and displays the resulting summary.

```python
df_stats_api = df_flat.groupBy("device_id").agg(
    count("*").alias("total_readings"),
    round(avg("co2"), 2).alias("mean_co2"),
    max("co2").alias("max_co2"),
    min("co2").alias("min_co2"),
    round(avg("temperature"), 2).alias("mean_temperature"),
)

df_stats_api.show()
```

### Example 11 — Write the equivalent summary in Spark SQL

Create a temporary view from the flattened data and compute the same statistics in SQL. Compare its values with Example 10: the DataFrame API and SQL express the same analysis, while this query also sorts devices by mean CO₂.

```python
df_flat.createOrReplaceTempView("sensors_flat")

df_stats_sql = spark.sql("""
    SELECT
        device_id,
        COUNT(*) AS total_readings,
        ROUND(AVG(co2), 2) AS mean_co2,
        MAX(co2) AS max_co2,
        MIN(co2) AS min_co2,
        ROUND(AVG(temperature), 2) AS mean_temperature
    FROM sensors_flat
    GROUP BY device_id
    ORDER BY mean_co2 DESC
""")

df_stats_sql.show()
```

### Example 12 — Save to Parquet and read the result back

`write.parquet()` saves the summary in a **directory** containing one or more Parquet part files; the path is not the name of a single Parquet file. `mode("overwrite")` replaces an earlier result at that path. Reading the directory back checks that the saved dataset is available for later queries, including queries with DuckDB.

```python
output_path = "output/device_stats_parquet"
df_stats_sql.write.mode("overwrite").parquet(output_path)

df_verifica = spark.read.parquet(output_path)
df_verifica.show()
```

## What to discuss after running the examples

- Which operations only describe a new DataFrame, and which ones trigger execution?
- Why can two interfaces, DataFrame operations and Spark SQL, produce the same summary?
- Why does writing a distributed DataFrame produce a directory of Parquet files?
- How would the results change if we added more readings from the same device?

For further reading, see the Apache Spark documentation on [JSON data sources](https://spark.apache.org/docs/latest/sql-data-sources-json.html), [DataFrames and Spark SQL](https://spark.apache.org/docs/latest/sql-programming-guide.html), and [Parquet data sources](https://spark.apache.org/docs/latest/sql-data-sources-parquet.html).
