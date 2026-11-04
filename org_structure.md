# Sample organizational structure: Director X

Baseline from [notebook 01](notebooks/01_generate_workday_data.py), random seed **42**,
before the re-org. This is derived from the generator, not a live Fabric workspace
snapshot. The charts focus on Director X rather than drawing all 10,000 workers.

Open this file in Markdown Preview in VS Code (`Ctrl+Shift+V`) or on GitHub.
Mermaid-enabled previews render the diagrams; the tables remain readable without it.

## Legend and headline counts

- **Solid arrow:** current SOLID reporting line.
- **Dotted arrow:** current DOTTED / cross-region matrix reporting line.
- Arrows point **worker -> manager**, matching the Fabric graph. Managers appear
  above their reports.
- Team-member boxes in the detailed chart are grouped counts, not single workers.
- Unrelated branches and dotted lines not directly connected to Director X are omitted.

| Director X metric | Before re-org | After re-org |
|---|---:|---:|
| Direct SOLID reports | 3 | 2 |
| Full SOLID subtree, excluding Director X | 87 | 61 |
| Direct DOTTED reports, counted separately | 3 | 3 |

The **87** SOLID reports are **3 OMs + 10 ISs + 74 TMs**.
The three DOTTED reports do **not** belong to that SOLID subtree.

## 1. Direct reports and dotted-line reports

```mermaid
flowchart BT
    CEO["CEO: Alex<br/>W_CEO"]
    SVP["SVP: Alex<br/>W00002 | Americas"]
    DX["Director X<br/>W_DIRX | Americas<br/>87 total SOLID reports"]
    OM1["OM: Sam<br/>W_DIRX_OM1<br/>Branch: 26 people"]
    OM2["OM: Jordan<br/>W_DIRX_OM2<br/>Branch: 33 people"]
    OM3["OM: Sam<br/>W_DIRX_OM3<br/>Branch: 28 people"]
    DOT1["OM: Jordan<br/>W02449 | EMEA"]
    DOT2["IS: Sam<br/>W08682 | LATAM"]
    DOT3["TM: Taylor<br/>W06220 | APAC"]

    SVP --> CEO
    DX --> SVP
    OM1 --> DX
    OM2 --> DX
    OM3 --> DX
    DOT1 -.-> DX
    DOT2 -.-> DX
    DOT3 -.-> DX

    classDef focus fill:#dbeafe,stroke:#1d4ed8,stroke-width:3px,color:#111827;
    classDef solid fill:#dcfce7,stroke:#15803d,color:#111827;
    classDef matrix fill:#fef3c7,stroke:#b45309,color:#111827;
    class DX focus;
    class OM1,OM2,OM3 solid;
    class DOT1,DOT2,DOT3 matrix;
```

Only the **three green OMs** are Director X's direct SOLID reports.
The yellow workers have their own SOLID managers elsewhere:

| Dotted report's full_name | Level | Region | SOLID manager's full_name | DOTTED manager |
|---|---|---|---|---|
| Jordan W02449 | OM | EMEA | Sam W_DIR021 | Director X |
| Sam W08682 | IS | LATAM | Sam W08651 | Director X |
| Taylor W06220 | TM | APAC | Taylor W06212 | Director X |

### Both reporting lines for the same workers

```mermaid
flowchart BT
    DX["Director X<br/>W_DIRX | Americas"]
    EMEA["Director: Sam<br/>W_DIR021 | EMEA"]
    LATAM["OM: Sam<br/>W08651 | LATAM"]
    APAC["IS: Taylor<br/>W06212 | APAC"]
    A["OM: Jordan<br/>W02449 | EMEA"]
    B["IS: Sam<br/>W08682 | LATAM"]
    C["TM: Taylor<br/>W06220 | APAC"]

    A --> EMEA
    B --> LATAM
    C --> APAC
    A -.-> DX
    B -.-> DX
    C -.-> DX
```

Each yellow worker in the first chart has **one SOLID manager and one separate
DOTTED manager**, not two SOLID managers.

## 2. Full SOLID organization under Director X

```mermaid
flowchart BT
    DX["Director X | W_DIRX<br/>87 reports, excluding self"]
    OM1["Sam | W_DIRX_OM1<br/>1 OM + 3 IS + 22 TM = 26"]
    OM2["Jordan | W_DIRX_OM2<br/>1 OM + 4 IS + 28 TM = 33"]
    OM3["Sam | W_DIRX_OM3<br/>1 OM + 3 IS + 24 TM = 28"]

    I05["IS: Sam | W00005"]
    I16["IS: Taylor | W00016"]
    I23["IS: Jordan | W00023"]
    I31["IS: Jordan | W00031"]
    I37["IS: Jordan | W00037"]
    I47["IS: Jordan | W00047"]
    I56["IS: Sam | W00056"]
    I64["IS: Jordan | W00064"]
    I73["IS: Sam | W00073"]
    I81["IS: Sam | W00081"]

    T05["10 TMs<br/>Includes W_TM_DEMO"]
    T16["6 TMs"]
    T23["6 TMs"]
    T31["5 TMs"]
    T37["9 TMs"]
    T47["8 TMs"]
    T56["6 TMs"]
    T64["8 TMs"]
    T73["7 TMs"]
    T81["9 TMs"]

    OM1 --> DX
    OM2 --> DX
    OM3 --> DX
    I05 --> OM1
    I16 --> OM1
    I23 --> OM1
    I31 --> OM2
    I37 --> OM2
    I47 --> OM2
    I56 --> OM2
    I64 --> OM3
    I73 --> OM3
    I81 --> OM3
    T05 --> I05
    T16 --> I16
    T23 --> I23
    T31 --> I31
    T37 --> I37
    T47 --> I47
    T56 --> I56
    T64 --> I64
    T73 --> I73
    T81 --> I81
```

### Team-member IDs behind each grouped box

Ranges below are inclusive and refer to numeric worker IDs, not generated names.

| OM | Immediate Supervisor | TM count | TM worker IDs |
|---|---|---:|---|
| W_DIRX_OM1 | W00005 | 10 | W_TM_DEMO; W00007-W00015 |
| W_DIRX_OM1 | W00016 | 6 | W00017-W00022 |
| W_DIRX_OM1 | W00023 | 6 | W00024-W00029 |
| W_DIRX_OM2 | W00031 | 5 | W00032-W00036 |
| W_DIRX_OM2 | W00037 | 9 | W00038-W00046 |
| W_DIRX_OM2 | W00047 | 8 | W00048-W00055 |
| W_DIRX_OM2 | W00056 | 6 | W00057-W00062 |
| W_DIRX_OM3 | W00064 | 8 | W00065-W00072 |
| W_DIRX_OM3 | W00073 | 7 | W00074-W00080 |
| W_DIRX_OM3 | W00081 | 9 | W00082-W00090 |
| **Total** | **10 supervisors** | **74** | |

Sample full chain, in the graph's edge direction:

```text
W_TM_DEMO -> W00005 -> W_DIRX_OM1 -> W_DIRX -> W00002 -> W_CEO
TM          IS        OM            Director  SVP        CEO
```

## 3. Re-org: move OM1's entire branch

[Notebook 02](notebooks/02_simulate_reorg.py) changes only OM1's SOLID parent.
The **3 ISs and 22 TMs** underneath OM1 stay attached to the same managers.

| Relationship | Before | After |
|---|---|---|
| W_DIRX_OM1 SOLID manager | W_DIRX | W_DIR002 |
| W_DIRX_OM2 SOLID manager | W_DIRX | W_DIRX |
| W_DIRX_OM3 SOLID manager | W_DIRX | W_DIRX |
| Three direct DOTTED reports to W_DIRX | Unchanged | Unchanged |

After the re-org:

```mermaid
flowchart BT
    SVP["SVP: Alex | W00002"]
    DX["Director X | W_DIRX<br/>2 direct SOLID reports<br/>61 total SOLID reports"]
    D2["Director: Taylor | W_DIR002<br/>Receives the 26-person branch"]
    OM1["Sam | W_DIRX_OM1<br/>26-person branch, including OM"]
    OM2["Jordan | W_DIRX_OM2<br/>33-person branch, including OM"]
    OM3["Sam | W_DIRX_OM3<br/>28-person branch, including OM"]

    DX --> SVP
    D2 --> SVP
    OM1 --> D2
    OM2 --> DX
    OM3 --> DX
```

Director X's new rollup is **33 + 28 = 61**, or **87 - 26 = 61**.
The new breakdown is **2 OMs + 7 ISs + 52 TMs**.
Director W_DIR002's pre-existing reports are omitted from this change-only chart.
Refresh the Fabric graph after running notebook 02 to make agent answers reflect this change.

## Whole-company context

| Level | Worker count |
|---|---:|
| CEO | 1 |
| SVP | 4 |
| Director | 80 |
| OM | 240 |
| IS | 958 |
| TM | 8,717 |
| **Total** | **10,000** |

There are **9,999 current SOLID lines** and **500 current DOTTED lines**
across the company. The charts above show only the Director X demo slice.
