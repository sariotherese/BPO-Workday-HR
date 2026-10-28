# Fabric PySpark: use the same default Lakehouse as notebook 01; run once per reset.
from datetime import date

from delta.tables import DeltaTable
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()
director_id, om_id, target_id = "W_DIRX", "W_DIRX_OM1", "W_DIR002"
today = date.today()
lines = spark.table("reporting_line").cache()
lines.count()  # Materialize the pre-merge snapshot for before/after checks.
solid = lines.filter("line_type = 'SOLID' AND is_current").select("worker_id", "manager_id")


def subtree(root_id, edges):
    visited = spark.createDataFrame([(root_id,)], "worker_id string")
    frontier = visited
    while frontier.limit(1).count():
        frontier = (edges.alias("e").join(frontier.alias("f"),
                    F.col("e.manager_id") == F.col("f.worker_id"))
                    .select(F.col("e.worker_id").alias("worker_id")).distinct()
                    .join(visited, "worker_id", "left_anti").localCheckpoint(eager=True))
        visited = visited.union(frontier).localCheckpoint(eager=True)
    return visited.filter(F.col("worker_id") != root_id)


current = lines.filter((F.col("worker_id") == om_id)
                       & (F.col("line_type") == "SOLID") & F.col("is_current")).collect()
if len(current) != 1 or current[0]["manager_id"] != director_id:
    raise ValueError("Re-org already applied or unexpected hierarchy. Run notebook 01 to reset.")
target = spark.table("worker").filter((F.col("worker_id") == target_id)
                                    & (F.col("management_level") == "DIR")).count()
assert target == 1, "The destination Director is missing."
before = subtree(director_id, solid).count()
moved = subtree(om_id, solid).count() + 1  # Include the OM, not just their descendants.
old = current[0].asDict()
assert old["effective_from"] <= today, "Re-org date precedes the existing line."
closed = dict(old, effective_to=today, is_current=False)
opened = dict(old, line_id=f"S_REORG_{om_id}", manager_id=target_id,
              effective_from=today, effective_to=None, is_current=True)
assert lines.filter(F.col("line_id") == opened["line_id"]).count() == 0
staged = spark.createDataFrame([closed, opened], lines.schema)

# One atomic Delta merge closes the old line and inserts the replacement.
(DeltaTable.forName(spark, "reporting_line").alias("target")
 .merge(staged.alias("source"), "target.line_id = source.line_id")
 .whenMatchedUpdateAll().whenNotMatchedInsertAll().execute())
lines.unpersist()
spark.catalog.refreshTable("reporting_line")
current_lines = spark.table("reporting_line").filter("is_current")
for line_type in ("SOLID", "DOTTED"):
    edges = current_lines.filter(F.col("line_type") == line_type).select("worker_id", "manager_id")
    edges.write.format("delta").mode("overwrite").saveAsTable(f"edge_reports_to_{line_type.lower()}")

new_solid = spark.table("edge_reports_to_solid")
after = subtree(director_id, new_solid).count()
assert new_solid.count() == 9999
assert new_solid.groupBy("worker_id").count().filter("count != 1").count() == 0
assert subtree("W_CEO", new_solid).count() == 9999
assert after == before - moved
assert new_solid.filter("manager_id = 'W_DIRX'").count() == 2
print(f"EXPECTED full SOLID subtree of W_DIRX: before={before}, after={after}, moved={moved}")
print(f"Moved {om_id} and its descendants to {target_id}; DOTTED lines are unchanged.")
print("Refresh the materialized graph, wait for success, then rerun the GQL and agent question.")
