# Data agent setup

## Agent instructions

Paste this into **Agent instructions**:

```text
Use the ontology for business meaning and the materialized graph with GQL for org questions.
Worker nodes use worker_id as the unique identifier. Director X is W_DIRX.
REPORTS_TO_SOLID and REPORTS_TO_DOTTED point from worker to manager and contain only current lines.
"Headcount", "rolls up to", "organization of", and "total team" mean the full multi-hop SOLID subtree.
"Direct reports" and "reports directly to" mean exactly one SOLID hop.
Use DOTTED lines only when the user says dotted-line, matrix, or regional reporting.
For dotted-line reports, default to one DOTTED hop; use recursion only if explicitly requested.
Use both labels together only when the user explicitly requests solid plus dotted reporting.
Exclude the named manager from their own headcount. Count DISTINCT workers, never paths.
All demo workers are active. Always state direct versus full subtree and solid versus dotted.
Support group by in GQL
For follow-ups such as "break that down", retain the previous manager, scope, and line type.
Return counts or grouped summaries, not full paths. Never replace recursion with a fixed hop limit.
For "who", group by worker_id and full_name to return identities, not just a count.
After a re-org and graph refresh, execute a fresh query rather than reuse an earlier answer.
```

## Six example question -> GQL pairs

Add these as graph-source example queries (or paste as additional instructions if that
preview UI has no example editor). These are Q1-Q6 from [org_rollup.gql](../queries/org_rollup.gql).

### 1. How many direct reports does Director X have?

```gql
MATCH (e:Worker)-[:REPORTS_TO_SOLID]->(d:Worker WHERE d.worker_id = 'W_DIRX')
RETURN count(DISTINCT e) AS direct_reports;
```

### 2. How many people roll up to Director X?

```gql
MATCH ACYCLIC (e:Worker)-[:REPORTS_TO_SOLID]->+(d:Worker WHERE d.worker_id = 'W_DIRX')
RETURN count(DISTINCT e) AS total_headcount;
```

### 3. Break Director X's full organization down by management level.

```gql
MATCH ACYCLIC (e:Worker)-[:REPORTS_TO_SOLID]->+(d:Worker WHERE d.worker_id = 'W_DIRX')
LET management_level = e.management_level
RETURN management_level, count(DISTINCT e) AS headcount
GROUP BY management_level
ORDER BY management_level;
```

### 4. How many people report to Director X on a dotted line?

```gql
MATCH (e:Worker)-[:REPORTS_TO_DOTTED]->(d:Worker WHERE d.worker_id = 'W_DIRX')
RETURN count(DISTINCT e) AS dotted_reports;
```

For the live **"Who reports to Director X on a dotted line?"** question, keep Q4's
one-hop `MATCH` and replace its `RETURN` with this grouped identity summary:

```gql
LET worker_id = e.worker_id, full_name = e.full_name
RETURN worker_id, full_name, count(DISTINCT e) AS worker_count
GROUP BY worker_id, full_name
ORDER BY worker_id;
```

### 5. How many unique people reach Director X through solid or dotted lines at any level?

```gql
MATCH ACYCLIC (e:Worker)-[:REPORTS_TO_SOLID|REPORTS_TO_DOTTED]->+(d:Worker WHERE d.worker_id = 'W_DIRX')
RETURN count(DISTINCT e) AS combined_headcount;
```

### 6. What is W_TM_DEMO's solid management chain up to the CEO?

```gql
MATCH ACYCLIC (e:Worker WHERE e.worker_id = 'W_TM_DEMO')-[:REPORTS_TO_SOLID]->+(m:Worker)
LET management_level = m.management_level
RETURN management_level, count(DISTINCT m) AS ancestor_count,
       collect_list(DISTINCT m.worker_id) AS manager_ids,
       collect_list(DISTINCT m.full_name) AS manager_names
GROUP BY management_level
ORDER BY CASE management_level
    WHEN 'IS' THEN 1 WHEN 'OM' THEN 2 WHEN 'DIR' THEN 3
    WHEN 'SVP' THEN 4 WHEN 'CEO' THEN 5 ELSE 6 END;
```

This returns five small rows ordered supervisor -> CEO, not full path lists.

## Ontology rules

Add these three natural-language business rules to the ontology item:

1. A worker's organization or total headcount is every distinct descendant reached
   through one or more current SOLID reporting lines, excluding the manager.
2. Direct reports are workers connected to the manager by exactly one current
   SOLID line; every worker except the CEO has exactly one such manager.
3. DOTTED relationships represent separate cross-region matrix reporting and are
   included only when explicitly requested; they never replace SOLID relationships.
