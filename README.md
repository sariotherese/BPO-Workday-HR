# Fabric org-chart rollup demo

10,000 synthetic workers; CEO > SVP > DIR > OM > IS > TM. No external packages
or Fabric APIs. All counts exclude the manager; all workers are active.

## Local CSV dataset

The [baseline CSV dataset](data/baseline) contains the full 10,000-worker company
and matches the **before re-org** view in [org_structure.md](org_structure.md).
Regenerate it from the repository root with standard Python; Spark is not needed:

```powershell
python .\notebooks\01_generate_workday_data.py --csv-dir .\data\baseline
```

This overwrites four UTF-8, header-bearing CSV files:

| File | Data rows |
|---|---:|
| [worker.csv](data/baseline/worker.csv) | 10,000 |
| [reporting_line.csv](data/baseline/reporting_line.csv) | 10,499 |
| [edge_reports_to_solid.csv](data/baseline/edge_reports_to_solid.csv) | 9,999 |
| [edge_reports_to_dotted.csv](data/baseline/edge_reports_to_dotted.csv) | 500 |

Dates use `YYYY-MM-DD`, null `effective_to` values are empty fields, and booleans
are `true`/`false`. When loading CSV into Fabric, set IDs and descriptive columns
to string, flags to boolean, and effective dates to date (the entirely empty
`effective_to` column must be explicitly typed). Uploading CSV to Lakehouse Files
alone does not create Delta tables; load each file to its matching table name
before binding the ontology. Alternatively, use notebook 01 without `--csv-dir`
as described below to create typed Delta tables directly.

### Flattened Director X CSV for SQL-based data agents

[director_x_solid_org.csv](data/director_x_solid_org.csv) contains **88 rows**:
**Director X + 3 OMs + 10 ISs + 74 TMs**, matching the full SOLID organization in
[org_structure.md](org_structure.md) **before the re-org**, including its director.
The three external dotted-line reports are excluded. Names and worker
attributes come from the baseline CSVs above.

Each row represents one worker, with their direct manager, `director_id`,
`director_name`, OM, IS, and a director-to-worker `hierarchy_path`. The OM
columns identify the branch OM (including the OM's own row); the IS columns
identify the supervisor (including the IS's own row) and are empty for OMs.
Director X has empty OM and IS fields, `hierarchy_path` = `W_DIRX`, and retains
his actual direct manager, SVP `W00002` (outside this CSV).
`reporting_depth_from_director` is 0 for Director X, 1 for OM, 2 for IS, and 3 for TM.
`org_snapshot` is `baseline_before_reorg`; this is a static export, not a live
hierarchy, and must be rebuilt from updated source data after any re-org.

Load this CSV into a Lakehouse table named `director_x_solid_org`, then select
that table in the data agent's Lakehouse source. Uploading to Files alone is
not enough. Use strings for IDs, names, paths, and other descriptive fields;
boolean for `is_active` and `is_direct_report_to_director`; integer for
`reporting_depth_from_director`.

For this table, add these source instructions to the data agent:

> Each row is one member of Director X's full SOLID organization, including
> Director X himself. For "full organization including the director", filter
> director_id = 'W_DIRX' (88 employees). For "everyone reporting to" or "roll up
> to Director X", also filter reporting_depth_from_director > 0 (87 reports)
> and include ALL report management levels (OM, IS, TM).
> Only filter is_direct_report_to_director = true when
> the question explicitly asks for DIRECT reports. Do not filter
> direct_manager_id = 'W_DIRX' for a full-organization question. Order full
> lists by hierarchy_path. This table is the before-re-org baseline only
> and does not contain dotted-line reports.

Example SQL for **"List everyone reporting to Director X, including indirect
reports, from OM through IS to TM"**:

```sql
SELECT worker_id, full_name, management_level, direct_manager_id,
       direct_manager_name, om_id, om_name, is_id, is_name,
       reporting_depth_from_director, hierarchy_path
FROM director_x_solid_org
WHERE director_id = 'W_DIRX'
  AND reporting_depth_from_director > 0
ORDER BY hierarchy_path;
```

Verify the query returns **87 reports**, not just the three OMs. Remove the
depth filter to return **88 employees including Director X**. The flattened
columns avoid recursive SQL for this slice, but do not override the agent's
response-size limits; inspect the executed query and request a full list.

### EPMS sample CSV: 100 employees

[epms_sample_100_employees.csv](data/epms_sample_100_employees.csv) is a separate
synthetic sample with the exact **98 columns**, in their original order, from
`epms_sample_columns.xlsx`. It preserves all 88 employees and SOLID reporting
paths from the Director X baseline, then adds 12 dummy TMs under the existing
ISs: **1 Director + 3 OMs + 10 ISs + 86 TMs = 100 employees**.
Director X therefore has **99 reportees: 3 direct and 96 indirect** in this
sample. The original 88-row CSV and live Fabric sources are not changed.
See the [EPMS organization chart](epms_org_chart.md) for a hierarchy overview,
branch headcounts, and the complete 100-employee reporting tree.

Each employee has one row. `employee_id` corresponds to the baseline `worker_id`;
`od`/`od_id` identify Director X, `om`/`om_id` identify the branch OM, and
`is_name`/`is_id` identify the branch IS. OM and IS fields include their own
manager row, as in the baseline. Exclude the selected manager's `employee_id`
when counting their reportees. `hierarchy_code` contains the SOLID
director-to-employee ID path separated by ` > `; the penultimate ID is the
immediate manager, except for Director X, whose path contains only his own ID.
`job_management_level` uses DIR, OM, IS, and TM; `management_type` is SOLID.
Unused SOM/SOD levels, secondary client emails, and RC2 fields are blank.

All employees are active; other attributes are simple dummy values, with
reserved `example.com` email domains. Dates use `YYYY-MM-DD`, timestamps use
UTC ISO 8601, and the snapshot date is **2026-11-06**. The file is UTF-8 with a
BOM for Excel compatibility. Preserve IDs and hierarchy paths as text when
importing. This file uses the separate EPMS artifacts below, not the original
88-person semantic model or agent.

### EPMS Fabric demo

The EPMS demo uses these items in the
[Task Us HR Demo folder](https://app.fabric.microsoft.com/groups/6d6350e8-6f22-4a8b-b06a-eb4a3b68dd23/list?experience=fabric-developer&subfolderId=105248)
of the `smec-dataplatform-e5` workspace:

| Artifact | Purpose |
|---|---|
| [epms_hr_lakehouse](https://app.fabric.microsoft.com/groups/6d6350e8-6f22-4a8b-b06a-eb4a3b68dd23/lakehouses/57bdc899-3e11-4ea3-8120-bb050ba6080e) | Stores the uploaded CSV and its one Delta table, `dbo.epms_solid_org`. |
| [epms_hr_semantic_model](https://app.fabric.microsoft.com/groups/6d6350e8-6f22-4a8b-b06a-eb4a3b68dd23/modeling/cf8d7b27-7799-433c-b1ee-95a562600a94/modelView?experience=fabric-developer) | Direct Lake on OneLake; only `epms_solid_org`, with descriptions on all 98 columns. |
| [epms_hr_ontology](https://app.fabric.microsoft.com/groups/6d6350e8-6f22-4a8b-b06a-eb4a3b68dd23/ontologies/0a4f37ad-0f96-4e94-bc95-10166fd4e1f7?experience=fabric-developer) | One Worker entity with all 98 properties, bound to the semantic model, plus a full-descendant business rule. |
| [epms_hr_agent](https://app.fabric.microsoft.com/groups/6d6350e8-6f22-4a8b-b06a-eb4a3b68dd23/aiskills/982ce2b1-6a77-4791-b0a6-0efb9f05f8d7?experience=fabric-developer) | Draft agent using the ontology and its inherited semantic-model source. |

Data flow: CSV -> Lakehouse Delta table -> single-table semantic model ->
Worker ontology -> data agent. Neither the ontology nor the agent has a direct
Lakehouse binding. Fabric-generated ontology Eventhouse/KQL and graph
infrastructure is not an agent data source. There are no Managers or
ReportingEdges tables and no reporting relationships in this EPMS ontology.

The model has six described measures:

- `Employee Headcount`: distinct employees in the current filter context.
- `Total SOLID Reports`, `Direct SOLID Reports`, `Indirect SOLID Reports`:
  counts for one selected `employee_id`, defaulting to `W_DIRX` when no single
  employee key is selected. These intentionally restore the full employee table
  before counting the selected manager's descendants. Resolve a manager first;
  do not rely on the default for an unknown or ambiguous name.
- `Duplicate Employee Keys`, `Blank Employee Keys`: data-quality checks.

For attribute-filtered reportee subsets, explicitly filter descendant rows
and use `Employee Headcount`, rather than assuming the three reportee measures
retain employee attribute filters.

For Director X, the complete reportee filter is
`od_id = "W_DIRX" AND employee_id <> "W_DIRX"`. For other managers, convert
`hierarchy_code` to a DAX path with `SUBSTITUTE(hierarchy_code, " > ", "|")`
and use token-aware `PATHCONTAINS`, excluding the manager's own row. Direct
reports have the manager as the penultimate path token; indirect reports are
total descendants minus direct reports. No recursive relationship traversal
or additional model table is needed.

Run [epms_validation.dax](queries/epms_validation.dax) in the model's DAX query
view. Live model checks returned 100 employees, 99 Director X reportees,
3 direct, 96 indirect, zero duplicate/blank keys, one model table, 98 described
columns, and six described measures. The full-list query returned 99 rows
without `TOPN`. OM1/OM2/OM3 reportee totals were 30/36/30; their direct counts
were 3/4/3.

Agent regression prompts:

1. "How many reportees does Director X have?" (all descendants, not just 3 OMs).
2. "How many are direct and indirect? Include Director X in the headcount too."
3. "Break down Director X's reportees by job management level."
4. "How many reportees does OM2 have, direct and indirect?"
5. "List every reportee under Director X with employee ID and name."

Inspect the executed semantic-model queries and reconcile the complete list
against the count. The agent instructions prohibit silent sampling or list
truncation; check actual response limits again after changing data or prompts.

The draft agent was tested against the live model: the unqualified Director X
question returned **99 total, 3 direct, 96 indirect**. Additional tests returned
**100 including Director X**, the **3 OM / 10 IS / 86 TM** reportee breakdown,
and **36 total / 4 direct / 32 indirect** for OM2. Its complete-list response
displayed **99 distinct employees**; every employee ID, full name, and level
matched the CSV exactly. The executed DAX used the flattened Director X filter,
excluded the director, and had no `TOPN` row cap. Model checks were also rerun
successfully after reopening. The agent remains a draft; it was not published.

### Live Director X ontology

The separate [director_x_solid_ontology](https://app.fabric.microsoft.com/groups/6d6350e8-6f22-4a8b-b06a-eb4a3b68dd23/ontologies/54a558dd-d7fa-4269-8a2c-6706f1723e4b?experience=fabric-developer)
now queries [director_x_solid_semantic_model](https://app.fabric.microsoft.com/groups/6d6350e8-6f22-4a8b-b06a-eb4a3b68dd23/modeling/0c403560-73bf-42e0-ab1f-591b4ba469d3/modelView?experience=fabric-developer),
not a direct Lakehouse binding. Worker uses the model's `director_x_solid_org`
table, and the reporting relationship uses its `ReportingEdges` table. Both
ontology bindings are DirectQuery to the semantic model; the model itself is
Direct Lake on OneLake over the CSV-derived Delta tables.
The existing ontology ID, Worker ID/key, reporting relationship ID, and full-scope
rule were preserved. The company-wide ontology and agent are unchanged.

- **Worker**: entity key `worker_id`; all 21 source columns are bound properties.
- **REPORTS_TO_SOLID**: Worker -> Worker, directed from employee to manager.
  Use semantic-model table `ReportingEdges` as the mapping table: origin entity key
  `worker_id` maps to column `worker_id`; target entity key `worker_id` maps
  to column `direct_manager_id`. Its 87 edges exclude Director X's edge to the
  external SVP; both endpoints exist among the 88 Workers. ReportingEdges is
  a relationship source, not a second employee entity.
- **Business rule**: "Full SOLID organization and direct report scope" defines
  full reports as all distinct descendants over one or more SOLID hops,
  direct reports as exactly one hop, and root inclusion only when requested.
- The [materialized graph](https://app.fabric.microsoft.com/groups/6d6350e8-6f22-4a8b-b06a-eb4a3b68dd23/graph/38d1ffb9-f994-4030-afe9-382a0173e2f0?experience=fabric-developer)
  was previously verified with **88 Worker nodes**, **3 direct reports**, and **87 recursive
  reports: 3 OM, 10 IS, 74 TM**. The full-list query returned 87 rows and included
  `W_TM_DEMO`. Director X's external manager is not an additional Worker node.
  These results belong to the earlier Lakehouse-backed snapshot.
- **Graph preview limitation:** [semantic-model-bound entities are not currently
  supported for graph projection](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-use-ontology-graph#limitations).
  Fabric marks Worker **Ineligible**. The old graph was not refreshed or
  recreated after the source migration. Use semantic-model queries and the
  flattened director/depth/path fields for current full-organization answers,
  not the historical materialized graph. The business rule includes this guidance.
- Open [director_x_solid_validation](https://app.fabric.microsoft.com/groups/6d6350e8-6f22-4a8b-b06a-eb4a3b68dd23/graph-queryset/72168518-d2d0-48f9-a179-8ed771f9cef4?experience=fabric-developer)
  for saved queries against that earlier graph snapshot.
- The separate [director_x_solid_agent](https://app.fabric.microsoft.com/groups/6d6350e8-6f22-4a8b-b06a-eb4a3b68dd23/aiskills/4cd1f18f-2ecf-4fd3-8479-0584f82015bd?experience=fabric-developer)
  has this ontology attached and instructions distinguishing full from direct
  reports. Its full-list test retrieved and displayed **87 distinct worker IDs**,
  with the correct level counts. The inspected execution used the bound
  Lakehouse table via SQL, not graph traversal. Subsequent agent requests
  encountered service CORS errors, and reopening the agent returned HTTP 404
  ("Artifact not found") despite its workspace listing remaining visible.
  Reopening succeeded after the workspace capacity was resumed. The agent
  remains an unpublished draft. After the semantic-model migration, its source
  browser shows `director_x_solid_semantic_model`. A fresh natural-language
  count test returned **DIR 1, OM 3, IS 10, TM 74**, **88 employees**, **87 total
  reports**, **3 direct**, and **84 indirect**, identifying the semantic model
  rather than the old graph as its source.

Historical GQL for the earlier graph snapshot (not a query against the new
semantic-model binding; run as one query without a trailing semicolon):

```gql
MATCH ACYCLIC (e:Worker)-[:REPORTS_TO_SOLID]->+(d:Worker WHERE d.worker_id = 'W_DIRX')
RETURN DISTINCT e.worker_id AS worker_id, e.full_name AS full_name,
       e.management_level AS management_level, e.direct_manager_id AS direct_manager_id,
       e.om_id AS om_id, e.is_id AS is_id,
       e.reporting_depth_from_director AS depth, e.hierarchy_path AS hierarchy_path
ORDER BY hierarchy_path
```

Example agent question: **"List everyone reporting to Director X across all SOLID
levels, from OM through IS to TM. Include indirect reports and show every worker
ID and name, ordered by hierarchy_path, without truncation."**

For the earlier direct-Lakehouse setup, if a new Delta table is visible but the agent reports
`Invalid object name`, open its SQL analytics endpoint and use **Sync metadata
from the Lakehouse**, then verify `SELECT` succeeds before retesting the agent.
Wait for graph data loading to complete before running historical GQL. This ontology and
agent remain a static before-re-org slice; they do not follow the original
demo's re-org tables automatically.

If the ontology reports **"The requested Ontology (preview) does not exist"**
while its workspace entry is still present, check the workspace's Fabric
capacity before recreating anything. A paused capacity produced this misleading
message and HTTP 404 metadata responses in this demo. Resuming the capacity
and reloading restored the same Director X ontology, with its Worker entity and
REPORTS_TO_SOLID relationship intact.

### Live Director X semantic model

The [director_x_solid_semantic_model](https://app.fabric.microsoft.com/groups/6d6350e8-6f22-4a8b-b06a-eb4a3b68dd23/modeling/0c403560-73bf-42e0-ab1f-591b4ba469d3/modelView?experience=fabric-developer)
is saved in the **BPO-Workday-HR** workspace folder. All three tables use
**Direct Lake on OneLake**:

- `director_x_solid_org`: the original 88 employees, including Director X.
- `Managers`: 15 unique immediate manager references, derived from that source
  into `workday_hr_demo.dbo.director_x_solid_managers`. This includes Director X's
  actual external manager `W00002`, without adding him to employee headcount.
- `ReportingEdges`: 87 internal employee-to-manager pairs, derived into
  `workday_hr_demo.dbo.director_x_solid_reporting_edges` from rows at depth > 0.
  Director X's external-manager edge is excluded, so both endpoints reference
  employees in this slice. This separate table backs the ontology relationship.
- `Employee_Immediate_Manager`: active many-to-one relationship from
  `director_x_solid_org.direct_manager_id` to `Managers.manager_id`, with single
  direction filtering from Managers to employees. Its validated state is `Ready`.
- `ReportingEdge_Worker` and `ReportingEdge_Manager`: many-to-one relationships
  from the two edge columns to `director_x_solid_org.worker_id`, with single
  direction filtering from employees to edges. The worker relationship is
  active; the manager relationship is inactive to avoid competing filter paths.
  All three model relationships were validated in state `Ready`.
- Descriptions cover all three tables, all **25 columns**, and all **8 measures**.
  Headcount measures distinguish employees including the Director, all reports,
  direct reports, and indirect reports. Data Quality measures check missing
  manager references and duplicate employee/manager keys.

The manager relationship represents **one immediate reporting hop**, not
recursive traversal. For everyone under Director X, use `director_id = "W_DIRX"`
and `reporting_depth_from_director > 0`, or **Total SOLID Reports**. Use `om_id`,
`is_id`, and `hierarchy_path` for branch rollups and complete reporting paths.
Do not filter `Managers.manager_id = "W_DIRX"` for the full organization:
that intentionally returns only the three direct OMs.

Live DAX validation after saving, reopening, and refreshing returned:

| Check | Result |
|---|---:|
| Employees including Director X | 88 |
| All reports / direct / indirect | 87 / 3 / 84 |
| DIR / OM / IS / TM | 1 / 3 / 10 / 74 |
| Manager lookup rows / unique keys | 15 / 15 |
| Missing manager references | 0 |
| Duplicate employee / manager keys | 0 / 0 |
| Blank employee / employee-manager / lookup keys | 0 / 0 / 0 |
| Reporting edges / unique employee endpoints | 87 / 87 |
| Missing edge employee / manager endpoints | 0 / 0 |
| Blank edge endpoint keys | 0 |

Manager filters were also tested: Director X returns 3 employees, OM2 returns
4 immediate IS reports, and external manager `W00002` returns Director X only.
Referential integrity was checked against actual keys, not assumed via a
relationship optimization flag. No database foreign-key enforcement is claimed.

This remains a static before-re-org slice. After replacing the organization
source, rebuild the lookup with
[director_x_solid_managers.sql](queries/director_x_solid_managers.sql) in the
Lakehouse **Spark SQL** editor, and rebuild the internal edges with
[director_x_solid_reporting_edges.sql](queries/director_x_solid_reporting_edges.sql).
Then refresh all three semantic model tables and run
[director_x_solid_validation.dax](queries/director_x_solid_validation.dax).
Recheck key integrity before using the updated model.

To rebind an existing ontology relationship, open its relationship details,
use the mapping-table menu's **Browse available sources**, select the semantic
model and `ReportingEdges`, and map the two endpoints before saving. The manual
editor saved this migration after the ontology agent's in-place patch failed.
Verify the saved bindings and remove any unused projected entity left by an
unsuccessful agent attempt; keep only Worker as the employee entity.

A DAX calculated lookup was initially blocked at refresh because Fabric requires
an explicit granular-access connection for calculated tables referencing Direct
Lake. The saved model instead uses the derived Delta lookup above; connection
security settings were not changed.

## Runbook

1. **Workspace and Lakehouse.** Open the supplied [Fabric workspace folder](https://app.fabric.microsoft.com/groups/6d6350e8-6f22-4a8b-b06a-eb4a3b68dd23/list?experience=fabric-developer&subfolderId=103420)
   and use **BPO-Workday-HR** for the demo items. Reuse this workspace; create a
   Fabric-capacity-backed workspace only if starting elsewhere. Ensure Graph,
   Ontology, Data agent, and required Copilot/Azure OpenAI tenant settings are enabled.
   Create a dedicated Lakehouse named `workday_hr_demo`.
   Create a PySpark notebook, attach it to this Lakehouse as **default**, paste
   [notebook 01](notebooks/01_generate_workday_data.py) into a Python cell, and run it.
   Save it as `01_generate_workday_data`. This creates four Delta tables:
   `worker`, `reporting_line`, `edge_reports_to_solid`, `edge_reports_to_dotted`.
   Record the printed expected answers. **Rerunning notebook 01 overwrites these
   tables and resets the re-org. Do not use a production Lakehouse.**

2. **Ontology.** In the same folder, select **New item > Ontology**, name it
   `workday_hr_ontology`, and create entity type **Worker**. Bind it to the Lakehouse
   `worker` table; use `worker_id` as the entity key. Include all worker properties,
   especially `full_name` and `management_level`.
   Create and bind these self-relationships:

   | Relationship type | Lakehouse table | Source Worker key | Target Worker key |
   |---|---|---|---|
   | REPORTS_TO_SOLID | edge_reports_to_solid | worker_id | manager_id |
   | REPORTS_TO_DOTTED | edge_reports_to_dotted | worker_id | manager_id |

   Both endpoints reference `Worker.worker_id`; direction is **worker -> manager**.
   Optionally ask the ontology agent to draft the entity, properties, and
   relationships, then review the names, keys, bindings, and direction yourself.
   Do not bind relationships directly to the historical `reporting_line` table.

3. **Rules.** Add the three **Ontology rules** from
   [data_agent_setup.md](agent/data_agent_setup.md) to the ontology item and save.

4. **Graph.** In the ontology, select **Manage graph**, select **Worker** and both
   relationships, then **Continue > Materialize**. Wait for successful data loading.
   Open the associated graph model (also accessible from the workspace).
   Verify node label `Worker`, edge labels `REPORTS_TO_SOLID` and
   `REPORTS_TO_DOTTED`, properties, and edge direction before querying.

5. **GQL baseline.** Create/open a queryset attached to that graph model. Paste
   [org_rollup.gql](queries/org_rollup.gql), running **one statement at a time**.
   Compare Q1-Q4 with notebook 01's direct, full-subtree, grouped, and dotted counts.
   Q1 must be **3**; Q2 must include OM + IS + TM, not just the OMs. The sum of
   Q3 must equal Q2. Q5 deduplicates workers reachable through either relationship.
   Q6 returns five ancestor-level summaries up to the CEO.
   Seed 42 baseline: **87 total = 3 OM + 10 IS + 74 TM**, **3 direct SOLID**,
   and **3 direct DOTTED**. The notebook's PySpark results are the runtime oracle.

6. **Data agent.** Select **New item > Data agent**, name it `workday_hr_agent`.
   Select **Add a data source** and add **both** `workday_hr_ontology` and its
   associated **Graph model**. Select Worker and both relationships where offered.
   Paste the **Agent instructions** and add the six question/GQL examples from
   [data_agent_setup.md](agent/data_agent_setup.md).
   Use graph-source instructions/examples if available; otherwise include them
   in agent instructions. Inspect generated queries to confirm the agent uses
   GQL against the graph for recursive questions, not a one-hop SQL join.

7. **Live demo, in order.**
   1. Ask **"How many direct reports does Director X have?"** Expected: **3**,
      one-hop SOLID.
   2. Ask **"How many people roll up to Director X?"** Compare with notebook 01's
      full SOLID subtree, excluding Director X.
   3. Ask **"Break that down by management level."** Expect OM, IS, TM groups
      whose sum equals the previous answer.
   4. Ask **"Who reports to Director X on a dotted line?"** Expect worker IDs/names,
      not a SOLID rollup. Compare with notebook 01's dotted identity output;
      the grouped-identity variant is in [data_agent_setup.md](agent/data_agent_setup.md).
   5. Create a second PySpark notebook attached to the **same default Lakehouse**.
      Paste and run [notebook 02](notebooks/02_simulate_reorg.py), saving it as
      `02_simulate_reorg`. It moves `W_DIRX_OM1` and its descendants to `W_DIR002`,
      closes the old SOLID line, inserts a new current line, and rebuilds both
      edge tables. Record its printed **before / after / moved** counts.
      In the workspace, open the graph model's **... > Schedule > Refresh now**.
      Wait for refresh success (configure a recurring schedule here if wanted).
      Rerun GQL Q2 and compare with notebook 02's **after** count.
      Then ask **"How many people roll up to Director X?"** again; inspect the
      newly executed GQL. The decrease must equal **moved**, including the OM.
      Seed 42 expectation: **87 -> 61**, moving **26** people.
      Q1 is now **2**; dotted reporting is unchanged.
      Notebook 02 refuses a repeat move; rerun notebook 01 and refresh the graph
      to reset the entire demo.

8. **Optional sharing.** Publish the data agent, then connect it from Copilot
   Studio / Microsoft 365 Copilot using the supported integration available in
   your tenant. Consumers need the appropriate permissions and licensing.

## Known limitations

- Ontology, Graph, and related data-agent integrations are **in preview**; UI,
  supported sources, tenant settings, regions, and availability can change.
- Bind this ontology to **Lakehouse tables, not semantic models**; semantic-model
  bindings have a documented data-agent compatibility limitation.
- A graph is a **materialized snapshot**, not a live Delta query. Refresh reloads
  bound data on a schedule or via **Refresh now**; wait for success after a re-org.
  Rebuilding the edge tables alone does not update the graph.
- Natural-language responses are not guaranteed: verify the executed GQL and
  compare with the notebook oracle. If the refreshed GQL is correct but the agent
  repeats an old answer, start a new conversation and ask the full question again.
- Query results have size caps. Counts and grouped summaries avoid returning full
  path lists. Unbounded `ACYCLIC` traversal terminates but can be costly on dense
  graphs; this six-level demo is intentionally small.
- Effective periods use `[effective_from, effective_to)`; `is_current` selects
  the graph edges. This demo performs one re-org, not scheduled future changes.

## Fabric references

- [Materialize and refresh an ontology graph](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-use-ontology-graph)
- [Graph patterns and ACYCLIC mode](https://learn.microsoft.com/en-us/fabric/graph/write-graph-pattern-queries)
- [GQL aggregation and grouping](https://learn.microsoft.com/en-us/fabric/graph/filter-aggregate-graph-data)
- [Create a data agent with ontology context](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-create-data-agent)
- [Supported data-agent sources](https://learn.microsoft.com/en-us/fabric/data-science/data-agent-add-datasources)