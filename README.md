# Fabric org-chart rollup demo

10,000 synthetic workers; CEO > SVP > DIR > OM > IS > TM. No external packages
or Fabric APIs. All counts exclude the manager; all workers are active.

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