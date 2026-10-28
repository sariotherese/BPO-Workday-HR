# Fabric PySpark: attach the demo Lakehouse as default, then run this whole file.
# WARNING: rerunning resets all four demo tables, including re-org history.
import random
from datetime import date

from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()
rng = random.Random(42)
start_date = date(2026, 1, 1)
titles = dict(CEO="CEO", SVP="Senior Vice President", DIR="Director",
              OM="Org Manager", IS="Immediate Supervisor", TM="Team Member")
rank = {level: index for index, level in enumerate(titles)}
countries = {"Americas": "USA", "EMEA": "UK", "APAC": "Philippines", "LATAM": "Brazil"}
workers, lines, other_supervisors = {}, [], []


def add_worker(level, manager=None, region="Americas", department="Operations", wid=None):
    wid = wid or f"W{len(workers) + 1:05d}"
    assert wid not in workers
    name = f"{rng.choice(['Alex', 'Sam', 'Jordan', 'Taylor'])} {wid}"
    workers[wid] = dict(worker_id=wid, full_name=name, job_title=titles[level],
                        management_level=level, department=department, region=region,
                        country=countries[region], is_active=True)
    if manager:
        lines.append((f"S_{wid}", wid, manager, "SOLID", start_date, None, True))
    return wid


ceo = add_worker("CEO", wid="W_CEO")
for s, region in enumerate(countries):
    svp = add_worker("SVP", ceo, region)
    for d in range(20):
        is_dirx = s == 0 and d == 0
        director = add_worker("DIR", svp, region,
                              wid="W_DIRX" if is_dirx else f"W_DIR{s * 20 + d + 1:03d}")
        if is_dirx:
            workers[director]["full_name"] = "Director X"
        for o in range(3):
            om = add_worker("OM", director, region,
                            wid=f"W_DIRX_OM{o + 1}" if is_dirx else None)
            for i in range(rng.randint(3, 5) if is_dirx else 4):
                supervisor = add_worker("IS", om, region)
                if not is_dirx:
                    other_supervisors.append(supervisor)
                for t in range(rng.randint(5, 10) if is_dirx else 9):
                    sample = is_dirx and o == 0 and i == 0 and t == 0
                    add_worker("TM", supervisor, region, wid="W_TM_DEMO" if sample else None)

# Reach exactly 10,000 without changing Director X's small, checkable subtree.
while len(workers) < 10000:
    supervisor = rng.choice(other_supervisors)
    add_worker("TM", supervisor, workers[supervisor]["region"])
assert len(workers) == 10000

# Exactly 5% get one cross-region matrix manager; guarantee a visible Dir X example.
eligible = [w for w in workers if rank[workers[w]["management_level"]] >= rank["OM"]]
forced = next(w for w in eligible if workers[w]["region"] != workers["W_DIRX"]["region"])
dotted_workers = [forced] + rng.sample([w for w in eligible if w != forced], 499)
managers = [w for w in workers if workers[w]["management_level"] != "TM"]
for w in dotted_workers:
    choices = [m for m in managers
               if workers[m]["region"] != workers[w]["region"]
               and rank[workers[m]["management_level"]] < rank[workers[w]["management_level"]]]
    manager = "W_DIRX" if w == forced else rng.choice(choices)
    lines.append((f"D_{w}", w, manager, "DOTTED", start_date, None, True))

worker_schema = """worker_id string, full_name string, job_title string,
management_level string, department string, region string, country string, is_active boolean"""
line_schema = """line_id string, worker_id string, manager_id string, line_type string,
effective_from date, effective_to date, is_current boolean"""
worker = spark.createDataFrame(list(workers.values()), worker_schema)
reporting_line = spark.createDataFrame(lines, line_schema)
solid = reporting_line.filter("line_type = 'SOLID' AND is_current").select("worker_id", "manager_id")
dotted = reporting_line.filter("line_type = 'DOTTED' AND is_current").select("worker_id", "manager_id")

# Fail visibly rather than persist a broken hierarchy.
assert worker.select("worker_id").distinct().count() == 10000
assert reporting_line.select("line_id").distinct().count() == 10499
assert solid.count() == 9999
assert solid.groupBy("worker_id").count().filter("count != 1").count() == 0
assert solid.filter("worker_id = 'W_CEO'").count() == 0
assert dotted.count() == dotted.select("worker_id").distinct().count() == 500
for table_name, frame in [("worker", worker), ("reporting_line", reporting_line),
                          ("edge_reports_to_solid", solid), ("edge_reports_to_dotted", dotted)]:
    frame.write.format("delta").mode("overwrite").saveAsTable(table_name)


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


descendants = subtree("W_DIRX", solid)
assert subtree("W_CEO", solid).count() == 9999
print("EXPECTED: current workers, excluding Director X himself; all workers are active.")
print("Direct SOLID reports:", solid.filter("manager_id = 'W_DIRX'").count())
print("Full SOLID subtree:", descendants.count())
print("Full SOLID subtree by management_level:")
descendants.join(worker, "worker_id").groupBy("management_level").count().orderBy("management_level").show()
print("One-hop DOTTED reports:", dotted.filter("manager_id = 'W_DIRX'").count())
print("DOTTED identities for the live 'Who' question:")
dotted.filter("manager_id = 'W_DIRX'").join(worker, "worker_id").select("worker_id", "full_name").show()
print("Sample TM for the upward-chain query: W_TM_DEMO")
