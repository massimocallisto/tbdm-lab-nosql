# Lab: run PySpark in Jupyter

## Goal

Use JupyterLab to run a few Spark computations on your own computer. First, check that Spark starts and observe the difference between a transformation and an action. Then continue with the IoT exercises in [README_pyspark.md](README_pyspark.md).

This lab runs Spark in **local mode**. It does not require a Spark cluster, a separate Spark download, Hadoop, or Docker. The `pyspark` Python package includes what is needed to start Spark locally, but Spark also needs a compatible Java installation.



## 1. Before you start

To run this lab locally, you need Python, PySpark (`pip install pyspark`), and a compatible Java Development Kit (JDK). **Java 17 is a suitable choice** for Spark 3.5 and Spark 4.x. Make sure Java is available through `JAVA_HOME` or your system `PATH`. You do not need to install a separate Spark distribution when using PySpark installed with `pip`.

If you want to run the examples in Jupyter on macOS or Windows, follow [README_pyspark.md](README_pyspark.md) to set up the environment. Start Jupyter from the project directory so that `examples/device_data-example.jsonl` can be found at the path used below.

```bash
python -m pip install jupyterlab ipykernel
python -m ipykernel install --user --name tbdm-spark --display-name "Python (TBDM Spark)"
jupyter lab
```

## 2. Open a notebook and start Spark

JupyterLab opens in your browser. Create a new notebook and select the **Python (TBDM Spark)** kernel. Put each example below in a separate code cell and run cells in order with **Shift+Enter**. Keep JupyterLab and the notebook kernel running while inspecting Spark's UI.

**Cell 1 — Start Spark on your computer.** `local[2]` allows Spark to run up to two tasks at the same time on this machine; it does not create a two-node cluster.

```python
import sys
import pyspark
from pyspark.sql import SparkSession

print("Python:", sys.executable)
print("PySpark:", pyspark.__version__)

spark = SparkSession.builder.master("local[2]").appName("Jupyter Spark introduction").getOrCreate()
print("Spark UI:", spark.sparkContext.uiWebUrl)
```

If `import pyspark` fails, check that the notebook is using the **Python (TBDM Spark)** kernel. If Spark cannot find Java, check `JAVA_HOME` or the Java installation, restart JupyterLab from the terminal, and restart the notebook kernel.

**Cell 2 — Create data without downloading a dataset.** Spark builds a DataFrame containing the integers 0–11, divided into two partitions. `filter()` describes a transformation; `show()` is an action that makes Spark execute it.

```python
numbers = spark.range(0, 12, 1, numPartitions=2)
even_numbers = numbers.filter("id % 2 = 0")

even_numbers.show()
```

**Cell 3 — Aggregate the data.** Add a group number (0, 1, or 2), then count rows per group. `explain()` prints Spark's execution plan; `show()` runs the computation. Each group should contain four rows.

```python
from pyspark.sql.functions import col

counts = numbers.withColumn("group_id", col("id") % 3).groupBy("group_id").count()

counts.explain()
counts.orderBy("group_id").show()
```

**Cell 4 — Inspect the application.** Open the URL printed in Cell 1 (usually `http://localhost:4040`). In **Jobs**, select a completed job; inspect **Stages** and **SQL** as well. Try to locate the tasks that ran and the aggregation. The exact number of jobs or stages may vary with the Spark version and the execution plan. The UI is available while the Spark application in your notebook is running.

## 3. Continue with the IoT exercises

Open [README_pyspark.md](README_pyspark.md) and continue in the **same notebook and kernel**:

1. Confirm that your project directory contains `examples/device_data-example.jsonl`. In a notebook cell, `from pathlib import Path; print(Path.cwd(), Path("examples/device_data-example.jsonl").exists())` prints the working directory and whether Spark can find the file. If the result is `False`, move to the project directory or correct the file path before continuing.
2. Copy the imports from **Start a Spark session** into a cell. You can skip its `SparkSession.builder...getOrCreate()` line because the `spark` session from Cell 1 is already running.
3. Begin with **Load the IoT readings**; copy each example into its own cell and run them in order. **Example 1–6** focus on selection, filters, and timestamps. **Example 7–11** introduce aggregation and SQL; **Example 12** writes and rereads Parquet.
4. After an aggregation, try `df_stats.explain()` (Example 7) and inspect the **SQL**, **Jobs**, and **Stages** tabs again. What changed compared with the first `show()`? The six-row dataset teaches the operations; it cannot establish a performance advantage for distributed processing.

The README is a Markdown document: you **copy its Python examples into notebook cells**; it is not a Python module to import.

When you have finished the lab, you may release Spark's resources with `spark.stop()`. Do this only after inspecting the application in the Spark UI.

## Further reading

- [Apache Spark: install PySpark](https://spark.apache.org/docs/latest/api/python/getting_started/install.html)
- [Apache Spark: Web UI](https://spark.apache.org/docs/latest/web-ui)
- [JupyterLab installation](https://jupyterlab.readthedocs.io/en/stable/getting_started/installation.html)
