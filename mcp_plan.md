# EDA-Schema MCP Server — Implementation Plan

Status: **phase 1 implemented** (see §7) · Branch: `mcp` · Target: `eda_schema/mcp/` (optional extra `eda-schema[mcp]`)

User guide: [docs/mcp.rst](docs/mcp.rst) · Tool reference: [docs/mcp_tools.rst](docs/mcp_tools.rst) · Examples: [examples/08_mcp](examples/08_mcp)

## 1. Goal and scope

Expose one EDA-Schema dataset to LLM agents (Claude Code, Claude Desktop, Cursor, …) through the
Model Context Protocol, so a user can ask questions like *"why does `aes_core` lose slack between
`cts` and `global_route` at a 1.5 ns clock?"* without writing Parquet or pandas code.

**In scope**

- Read-only access to **one per-PDK dataset per server session** (layout identical to
  [`dataset/test`](dataset/test)).
- Summaries, bounded queries, rendered images and file exports that are safe for a model's context.

**Out of scope (explicitly)**

- **Cross-PDK analysis.** There is no facility for it yet. Units, cell libraries and timing scales
  differ between PDKs, so the server never mixes datasets and never accepts a `pdk` argument.
- Writing or modifying the dataset, or running OpenROAD.
- Multi-dataset sessions (see §10 for how this could be added later).

## 2. The dataset a session binds to

A session is bound to exactly one dataset root, which holds one PDK's flows:

```
<root>/                          e.g. dataset/test  (SKY130, 1 flow)  · full PDK ≈ 70–90 GB, 1,944 flows
├── design_flows/table.parquet   flow_id, design, run_status
├── constraints/table.parquet    flow_id, clock_period, clock_uncertainty, …, aspect_ratio, core_utilization
├── design_stages/table.parquet  flow_id, stage, run_status
├── {area,cell,power,timing}_metrics/table.parquet     1 row per (flow_id, stage)
├── netlists/{table,graph}.parquet + images/*.npz
├── timing_paths/{table,graph}.parquet                 key: flow_id, stage, startpoint, endpoint, path_type
├── clock_trees/{table,graph}.parquet + images/*.npz   key: flow_id, stage, clock_source
├── gates/ pins/ nets/ ports/ net_arcs/ cell_arcs/     element tables (large)
├── power_delivery_networks/  routability_metrics/     keys only in table + images/*.npz (scalar maps)
├── standard_cells/table.parquet                       PDK library (no flow_id)
├── <hash>.pkl                                         Liberty cache
└── openroad_dataloader.log                            contains LEF/Liberty paths → PDK name
```

Image files are named `{image}__flow_id={id}__stage={stage}[__clock_source={clk}].npz` with the
array in `arr_0`. Binary maps are `uint8` at one pixel per M1 width (695² for `gcd`). Scalar maps
(IR drop, EM, RUDY) are `float64` at 50× coarser resolution (14² for `gcd`).

### PDK identity

The server must know which PDK it is serving, because every response carries it (§5). In order of
preference:

1. A `dataset.json` manifest at the root (new, written by the data generator; see §9, item 1):
   `{"pdk": "sky130hd", "schema_version": "2.0.0", "units": {...}, "generated": "..."}`.
2. Infer it from `openroad_dataloader.log` (`.../platforms/<pdk>/lef/...`).
3. Infer it from the `standard_cells.name` prefix (`sky130_fd_sc_hd__*`, …).
4. Otherwise the server still starts, but reports `pdk: "unknown"` and logs a warning.

## 3. Session model

| Transport | Session ⇔ dataset binding | Phase |
|---|---|---|
| **stdio** (default) | One process = one MCP session = one dataset. The root comes from `--dataset PATH` or `EDA_SCHEMA_DATASET`. The `DatasetContext` is built at startup and stays fixed for the process's lifetime. | 1 |
| **Streamable HTTP** | Several sessions per process. Each session calls `open_dataset(name)`, choosing from a server-side allowlist (`--dataset-root NAME=PATH`, repeatable). Contexts are cached per root and shared read-only; each session holds a reference to its context, keyed by MCP session id. Calling any other tool before `open_dataset` returns a clear error. | 4 |

Several PDKs in one client are just several server entries. The client namespaces their tools, and
nothing is shared between them:

```jsonc
// .mcp.json
{
  "mcpServers": {
    "eda-sky130": { "command": "eda-schema-mcp", "args": ["--dataset", "/data/eda-schema-v2/sky130hd"] },
    "eda-ng45":   { "command": "eda-schema-mcp", "args": ["--dataset", "/data/eda-schema-v2/nangate45"] }
  }
}
```

The server instructions (MCP `instructions` field) state: *"This server serves the `<pdk>`
dataset only. Do not compare its numbers with other eda-schema servers; cross-PDK comparison is not
supported."*

## 4. Architecture

```
eda_schema/mcp/
├── __init__.py
├── __main__.py          # `python -m eda_schema.mcp` → server.main()
├── server.py            # FastMCP app, CLI args, transport selection, registration
├── context.py           # DatasetContext: root, ParquetDB, manifest/PDK, catalog, image index, caches
├── catalog.py           # in-memory join of flows + constraints + stages + all *_metrics tables
├── envelope.py          # response envelope, row/char budget, truncation, hints
├── render.py            # npz → downsampled PNG (max-pool binary, mean-pool scalar), stats, hotspots
├── tools/
│   ├── catalog.py  qor.py  timing.py  netlist.py  clock.py
│   ├── power.py    images.py  cells.py  ml.py  sql.py
├── resources.py
└── prompts.py
```

- **SDK:** the official `mcp` Python SDK, **2.x** (`mcp.server.mcpserver.MCPServer`; v1's `FastMCP`
  was renamed). The optional extra is `mcp = ["mcp>=2.3,<3", "pillow>=10.0"]`, plus `duckdb` for
  `sql` in phase 4. The console script is `eda-schema-mcp`. Core installs stay unchanged.
- **Data access:** reuse `ParquetDB` (`get_table_data` with filter pushdown and column selection,
  `get_graph_data`, `get_image`) and `utils/netlist_diff.py`. Do not duplicate the readers.
- **Startup work (`DatasetContext`)**
  - Load the **catalog**: design_flows ⨝ constraints ⨝ design_stages ⨝ {area, cell, power,
    timing}_metrics ⨝ netlists table. That is about 1,944 × 8 ≈ 16k rows per PDK. Keep it in one
    pandas frame. Every QoR, discovery and aggregation tool runs on it with no further I/O.
  - Build the **image index**: one `os.scandir` per `images/` directory, with filenames parsed into
    `{(entity, image, flow_id, stage, clock?) → path}`. About 300k entries per PDK; it replaces
    per-call globbing.
  - Do **not** load the element tables (gates, pins, nets, arcs, paths). Read them on demand, always
    filtered by `flow_id` + `stage`.
- **Caching:** an LRU on `(entity, flow_id, stage)` for element tables, with a small byte cap.
  `_load_arrow_table` already uses `lru_cache(maxsize=128)` by entry count. On a full PDK, 128
  filtered `pins` tables can exhaust RAM, so the server needs a byte bound (§9, item 4).
- **Concurrency:** tools are sync and CPU/IO-bound. The SDK already runs sync tools on a worker
  thread, so one slow netlist read doesn't block the session.
- **Tool binding:** tool logic is plain functions `fn(ctx, **args)` in `tools/`. `server.bind()`
  strips `ctx` from the signature so the SDK builds the input schema from the original
  `Annotated[..., Field(...)]` parameters.

## 5. Response contract (applies to every tool)

```jsonc
{
  "dataset":  {"pdk": "sky130hd", "root_id": "sky130hd@<short-hash>"},
  "data":     { ... },               // or [ ... ]
  "returned": 20,
  "total":    287,                   // when known
  "truncated": true,
  "next_cursor": "…",                // for paginated tools
  "hint": "Use slack_histogram or get_timing_summary for the full distribution."
}
```

Rules, enforced centrally in `envelope.py`:

1. **Row cap:** every list tool has a default `limit` (20–50) and a hard maximum (200).
2. **Character budget:** a serialized response may not exceed `--max-response-chars` (default
   40,000, about 10k tokens). Rows beyond the budget are dropped and `truncated` is set. This is the
   backstop when a row cap isn't enough, e.g. wide pin rows.
3. **Rounding:** floats are rounded to 6 significant digits by default (`--precision`). 4 digits
   hid real differences between flows, e.g. in areas such as 12345.67 vs 12346.1.
4. **No raw graphs or arrays inline:** graphs become summaries or subgraphs with `max_nodes`; images
   become PNG content (≤512 px) or statistics; full data goes to files (§6.10).
5. **Actionable errors:** `DataNotFoundError` maps to a tool error that lists valid values (stages
   for this flow, nearest flow_ids, entity names).
6. **Units:** numbers are returned in dataset units, and a `units` block is published once in
   `eda://dataset` instead of on every row.

Size labels used in §6, measured on `gcd` (final stage) and scaled with the paper's figures
(~35k gates and ~4.8k paths per flow on average; `ethernet` and `jpeg` far larger):

- 🟢 Always small.
- 🟡 Needs a limit, filter or downsampling.
- 🔴 Never inline; summarize or export.

## 6. Tool and resource catalog (per-PDK)

Compared with the earlier draft, every `pdk` argument and `group_by=pdk` option is removed. `pdk`
is a property of the session.

### 6.0 Session and dataset (new)

| Name | Kind | Returns | Size | Phase |
|---|---|---|---|---|
| `eda://dataset` | resource | PDK, root id, schema version, units, flow/design/stage counts, entities present, image kinds present | 🟢 | 1 |
| `get_dataset_info()` | tool | Same as `eda://dataset`, for clients that don't read resources | 🟢 | 1 |
| `open_dataset(name)` | tool | Binds an HTTP session to an allowlisted root | 🟢 | 4 |

### 6.1 Resources

| URI | Content | Size | Phase |
|---|---|---|---|
| `eda://schema` | Entities with primary keys, fields and types (`SchemaMetadata`) | 🟢 | 1 |
| `eda://schema/{entity}` | One entity's fields and graph node types; fields **absent in this dataset** are marked | 🟢 | 1 |
| `eda://stages` | The 8 stages in order, with the entities and images available at each one | 🟢 | 1 |
| `eda://dataset/summary` | Designs, flow counts, run-status breakdown | 🟢 | 1 |
| `eda://flows/{flow_id}` | Design, run status, constraints, per-stage status | 🟢 | 1 |
| `eda://flows/{flow_id}/{stage}/qor` | Area, power, timing, cell metrics and netlist summary | 🟢 | 1 |
| `eda://image/{entity}/{name}/{flow_id}/{stage}` | PNG, ≤512 px | 🟡 | 1 |

### 6.2 Discovery and catalog

| Tool | Returns | Size | Phase |
|---|---|---|---|
| `list_designs()` | Designs with flow counts and pass/fail counts | 🟢 | 1 |
| `list_flows(design?, clock_period?, core_utilization?, aspect_ratio?, run_status?, sort?, limit, cursor)` | flow_ids with constraints; ranges are allowed (`{"min":…, "max":…}`) | 🟡 108 per design, 1,944 per PDK; paginate | 1 |
| `get_flow(flow_id)` | Flow, constraints, stage statuses | 🟢 | 1 |
| `find_flows_by_qor(metric, op, value, stage="final", design?, limit)` | Flows that match a QoR condition | 🟡 | 2 |
| `get_operating_points(design)` | Barely Pass / Barely Fail clock periods and slack-to-clock-period ratio (SCPR), **computed from this dataset** (final `worst_slack / clock_period`) | 🟢 | 3 |
| `describe_entity(entity)` | Fields, meanings and presence in this dataset | 🟢 | 1 |

### 6.3 QoR metrics (served from the in-memory catalog)

| Tool | Returns | Size | Phase |
|---|---|---|---|
| `get_qor(flow_id, stage, categories?)` | Area / power / timing / cell / netlist metrics | 🟢 | 1 |
| `get_stage_evolution(flow_id, metrics[])` | Each metric at the 8 stages, with deltas between stages | 🟢 | 1 |
| `compare_flows(flow_ids[≤20], stage, metrics[])` | Side-by-side table | 🟢 | 1 |
| `aggregate_metrics(metric, group_by[design,stage,clock_period,core_utilization,aspect_ratio], aggs[mean,min,max,std,p50], filters?)` | Grouped statistics | 🟢 | 1 |
| `query_metrics(entity, filters, columns, sort, limit=50)` | Raw metric rows | 🟡 ≤16k rows per PDK | 2 |
| `metric_correlation(x, y, stage, filters?)` | Pearson and Spearman r, n, slope | 🟢 | 3 |
| `parameter_sensitivity(metric, param, design?, stage="final")` | Metric against a swept constraint (grouped means) | 🟢 | 3 |
| `timing_closure_status(flow_id)` | Pass/fail, SCPR, first stage with negative slack | 🟢 | 2 |
| `get_baseline_error(metric, from_stage, design?)` | MAE / MAPE / R² of the stage-k estimate against the final value, mirroring [baseline_analysis](research/eda-schema-v2/baseline_analysis) | 🟢 | 3 |

### 6.4 Timing

| Tool | Returns | Size | Phase |
|---|---|---|---|
| `get_timing_summary(flow_id, stage, path_type="setup")` | WNS, TNS, violating/total endpoints, critical start and end points | 🟢 | 1 |
| `slack_histogram(flow_id, stage, path_type, bins=20)` | Binned counts | 🟢 | 2 |
| `list_timing_paths(flow_id, stage, path_type, only_violating?, sort="slack", limit=20)` | Path rows (no graphs) | 🟡 ~290 per stage on gcd, thousands on large designs | 1 |
| `get_timing_path(flow_id, stage, startpoint, endpoint, path_type)` | Ordered pins with cell and net arcs | 🟢 one path ≈ 750 tokens | 1 |
| `path_delay_breakdown(...)` | Cell / net / clock delay split | 🟢 | 2 |
| `track_path_across_stages(flow_id, startpoint, endpoint, path_type)` | Slack and arrival time per stage | 🟢 | 2 |
| `get_endpoint_slack(flow_id, stage, pin)` | Setup and hold slack, rise and fall | 🟢 | 2 |
| `worst_endpoints(flow_id, stage, k≤50)` | Top-k pins by slack | 🟡 | 2 |
| `query_arcs(flow_id, stage, kind, gate?/net?, sort, limit)` | Arc rows; **a gate, net or sort+limit is required** | 🔴 if unfiltered (127k–146k tokens on gcd) | 2 |
| `arc_statistics(flow_id, stage, kind, group_by="standard_cell")` | Delay and slew statistics per cell type | 🟢 | 2 |

### 6.5 Netlist and physical design

| Tool | Returns | Size | Phase |
|---|---|---|---|
| `get_netlist_summary(flow_id, stage)` | Cells, nets, pins, IO, utilization, die size, wirelength | 🟢 | 1 |
| `cell_usage(flow_id, stage, top_k=20, group_by=cell\|function\|drive_strength)` | Histogram | 🟢 | 2 |
| `get_gate(flow_id, stage, name)` | Gate, its pins and its nets (one hop) | 🟢 | 2 |
| `get_net(flow_id, stage, name, max_sinks=50)` | Net, driver, sinks, RC | 🟡 high-fanout nets | 2 |
| `query_gates / query_nets / query_pins(flow_id, stage, filters, columns, sort, limit)` | Element rows; flow_id and stage are **required** | 🔴 if unfiltered (pins 138k tokens on gcd) | 2 |
| `gates_in_region(flow_id, stage, bbox, limit)` | Spatial query | 🟡 | 2 |
| `get_neighborhood(flow_id, stage, node, depth≤3, direction, max_nodes=100)` | Subgraph | 🟡 grows exponentially with depth | 2 |
| `netlist_graph_stats(flow_id, stage)` | Degree / fanout percentiles, logic depth, components | 🟢 computed on the server | 2 |
| `diff_stages(flow_id, stage_a, stage_b, examples=20)` | Cells added and removed, buffers, resizes (`netlist_diff`) | 🟡 counts + examples | 2 |
| `get_ports(flow_id, stage, limit)` | IO ports | 🟡 | 2 |
| `export_netlist_graph(flow_id, stage, format=json\|graphml)` | Writes a file and returns path, node and edge counts | 🔴 28k tokens on gcd | 4 |

### 6.6 Clock tree

| Tool | Returns | Size | Phase |
|---|---|---|---|
| `list_clock_sources(flow_id, stage)` | Clock names | 🟢 | 2 |
| `get_clock_tree_summary(flow_id, stage, clock)` | Buffers, sinks, depth, insertion delay and skew if computable | 🟢 | 2 |
| `get_clock_tree_graph(flow_id, stage, clock, max_nodes=200)` | Topology | 🟡 91 nodes on gcd, ~10k sinks on `ethernet` | 2 |

### 6.7 Power, power delivery and routability

| Tool | Returns | Size | Phase |
|---|---|---|---|
| `get_power_breakdown(flow_id, stage)` | Internal, switching and leakage power; combinational vs sequential | 🟢 | 1 (part of `get_qor`) |
| `get_ir_drop_summary(flow_id, stage, rail)` | Max / mean / p99 and top-k hotspot coordinates (from `.npz`) | 🟢 | 2 |
| `get_em_summary(flow_id, stage, rail)` | Same statistics for EM maps | 🟢 | 2 |
| `get_congestion_summary(flow_id, stage, kind=net\|net_long\|net_short\|pin)` | RUDY statistics and hotspots | 🟢 | 2 |
| `top_ir_drop_gates(flow_id, stage, rail, k≤50)` | From the `gates.ir_drop_*` columns | 🟡 | 2 |
| `get_heatmap_values(entity, name, flow_id, stage, max_dim=32)` | Downsampled grid | 🟡 | 2 |

### 6.8 Images

| Tool | Returns | Size | Phase |
|---|---|---|---|
| `list_images(flow_id, stage)` | Available image names per entity (from the index) | 🟢 | 1 |
| `render_image(entity, name, flow_id, stage, max_px=512, colormap?)` | PNG `ImageContent`. Binary maps use max-pooling so thin wires survive; scalar maps are colour-mapped (mean-pooled when large, enlarged when tiny); min/max/mean are returned as text instead of a colorbar | 🟡 ~1–2k vision tokens | 1 |
| `image_stats(entity, name, flow_id, stage)` | Shape, occupancy, centroid, min/max/mean | 🟢 | 2 |
| `export_image(..., format=npz\|png)` | Path to a full-resolution file | 🔴 | 4 |

### 6.9 Standard cells (this PDK's library)

| Tool | Returns | Size | Phase |
|---|---|---|---|
| `get_standard_cell(name)` | One cell record | 🟢 | 2 |
| `search_standard_cells(name_contains?, is_sequential?, is_buffer?, drive_strength?, limit=30)` | Matching cells | 🟡 441 cells ≈ 48k tokens | 2 |
| `standard_cell_summary()` | Counts by type and drive strength | 🟢 | 2 |

### 6.10 ML, benchmarks and escape hatch

| Tool | Returns | Size | Phase |
|---|---|---|---|
| `list_benchmark_tasks()` | The 12 paper tasks, with their targets and baseline stage | 🟢 | 3 |
| `sample_flows(n, stratify_by?, seed)` | flow_ids | 🟢 | 3 |
| `build_task_dataset(task, designs?, input_stage, split, out_dir)` | Writes Parquet; returns path, shape and label statistics | 🔴 by design | 4 |
| `sql(query, limit=100)` | Read-only DuckDB over this root's Parquet files (views per entity), with a timeout | 🟡 hard row cap | 4 |
| `export_query(query, out_path)` | Writes the full result to a file | 🔴 by design | 4 |

Exports write only under `--export-dir` (default `<cwd>/eda_mcp_exports`). Paths outside it are
rejected.

### 6.11 Prompts

| Prompt | Chain | Phase |
|---|---|---|
| `analyze_timing_closure(flow_id)` | `get_timing_summary` → `list_timing_paths(limit=5)` → `get_timing_path` → `path_delay_breakdown` → `track_path_across_stages` | 2 |
| `explain_stage_change(flow_id, metric)` | `get_stage_evolution` → `diff_stages` around the biggest jump → congestion / IR summaries | 2 |
| `debug_hotspot(flow_id, stage)` | `render_image` (heatmap) → `get_congestion_summary` / `get_ir_drop_summary` → `gates_in_region` | 2 |
| `design_space_overview(design)` | `list_flows` → `aggregate_metrics` by constraint → `get_operating_points` | 3 |

## 7. Phases

### Phase 0 — prerequisites (no MCP code yet)

- [ ] Decide the PDK identity mechanism and add `dataset.json` to the generator (§2). Implement
      log and cell-prefix inference as the fallback.
- [ ] On one **full** PDK root, measure: catalog load time, image index build time, and
      `get_table_data("pins", flow_id=…, stage=…)` latency. This shows whether row-group pruning
      works (§9, item 3).
- [ ] Record per-PDK units (time, power, capacitance, distance) for the `units` block.
- [x] Add a `[mcp]` extra and the `eda-schema-mcp` entry point to `setup.py`.

### Phase 1 — MVP (stdio, about 14 tools) — ✅ done

Delivered: the 14 tools and 8 resources below; `DatasetContext`, the envelope, the PNG renderer; the
`docker/mcp/Dockerfile` dev image; 144 tests at 100% line coverage of `eda_schema.mcp`, including a
real stdio subprocess test and the exit criteria; three examples; docs (`docs/mcp.rst` plus the
generated `docs/mcp_tools.rst`). Prompts moved to phase 2 as planned. Phase 0 is still open: there
is no full PDK root available to measure against.

`get_dataset_info`, `list_designs`, `list_flows`, `get_flow`, `get_qor`, `get_stage_evolution`,
`compare_flows`, `aggregate_metrics`, `get_timing_summary`, `list_timing_paths`,
`get_timing_path`, `get_netlist_summary`, `list_images`, `render_image`, plus the §6.1 resources.

The MVP also includes `DatasetContext`, the catalog, the image index and `envelope.py`; every later
tool depends on them.

**Exit criteria:** on `dataset/test`, Claude Code can answer, using only the MCP:
*"How does WNS of gcd-000001 evolve across stages, which path is worst at `final`, and show me the
routing map"*, and every response stays under the character budget.

### Phase 2 — depth on one flow

Timing deep-dive (§6.4), netlist and graph tools (§6.5), clock tree (§6.6), PDN and routability
summaries (§6.7), image stats, standard cells, `find_flows_by_qor`, `query_metrics`,
`timing_closure_status` and the first three prompts.

### Phase 3 — analytics across the dataset (within the PDK)

`metric_correlation`, `parameter_sensitivity`, `get_operating_points`, `get_baseline_error`,
`list_benchmark_tasks`, `sample_flows` and `design_space_overview`.

### Phase 4 — power users and HTTP

Exports, `build_task_dataset`, `sql` / `export_query` (DuckDB), and the Streamable HTTP transport
with `open_dataset` and an allowlist.

## 8. Testing

- **Fixture:** `dataset/test` (gcd, SKY130) through a `DatasetContext` fixture in
  `tests/mcp/conftest.py`.
- **Unit:** each tool function is called directly (they are plain Python functions underneath
  FastMCP).
- **Protocol:** an in-process MCP client session (SDK memory transport). Assert that tools,
  resources and prompts are listed and that a few calls round-trip.
- **Budget tests:** for every tool at default arguments, the serialized output is under
  `max_response_chars`. Also run with an artificially tiny budget and limit, and assert
  `truncated`, `total` and `hint` are set correctly. Because gcd is tiny, this second run is what
  exercises truncation.
- **Error tests:** an unknown flow_id or stage, or a missing image, produces an error that lists
  valid values.
- **Isolation test:** no tool signature accepts `pdk`, and every response carries `dataset.pdk`.
- **Manual smoke test:** a `.mcp.json` example in `docs/mcp.rst`, tried in Claude Code against
  `dataset/test`.

## 9. Known data issues to resolve or handle

1. **No PDK column or manifest.** `design_flows` holds only `flow_id`, `design` and `run_status`.
   See §2 for the manifest and fallbacks.
2. **Schema/data drift.** `GateEntity` defines `internal_power`, `switching_power`,
   `leakage_power` and `total_power`, and `NetlistEntity` defines `total_wirelength` and
   `total_hpwl`. None of them are in the sample tables. `describe_entity` and `eda://schema/{entity}`
   must report the *present* columns, and tools must not assume optional columns exist.
3. **Image-only entities.** The `power_delivery_networks` and `routability_metrics` tables contain
   only keys, so all their summaries come from `.npz` files through the image index.
4. **Filter pushdown at scale.** Element tables are single Parquet files per entity (multi-GB on a
   full PDK). Pushdown on `flow_id`/`stage` only helps if row groups are clustered by flow. Verify
   this in Phase 0; if they aren't, rewrite with sorted row groups or hive-partition by `flow_id`.
   Also bound `_load_arrow_table`'s cache by bytes, not by its `maxsize=128` entry count.
5. **Placement-density sweep not recorded.** The paper sweeps placement density as well, giving
   108 configurations per design, but `constraints` has no density column. Flows with identical
   (clock, utilization, aspect ratio) can't be told apart. Either add the column or document that
   `list_flows` may return several flows per constraint tuple.
6. **Failed or partial flows.** `run_status` can be non-`Complete`. Tools must treat missing stages
   as "not available", not as an error, and `aggregate_metrics` should exclude incomplete flows by
   default (`include_incomplete=false`).
7. **Arc delay attribution (found in phase 1).** In the sample, cell-arc delays are about 0.001 and
   net-arc delays carry most of the path delay; e.g. the net after a clock buffer reports 0.137. The
   driver's cell delay seems to be stored on the following net arc. `get_timing_path` reports the
   stored values unchanged. Verify against the OpenSTA reports before `path_delay_breakdown`
   (phase 2) interprets the split.
8. **Stale reads after rewrites.** `_load_arrow_table`'s `lru_cache` is keyed by path, so a table
   rewritten in place is served from the cache. This is harmless for the read-only server, but it
   matters for tests and for any future write tool.

## 10. Future work (not planned)

- **Cross-PDK analysis**, once there is a facility for it: a separate aggregator server or tool
  that holds several `DatasetContext`s and normalizes units, so it isn't bolted onto the per-PDK
  server. All per-PDK tools stay unchanged.
- Server-side caching of rendered PNGs; MCP resource subscriptions (not useful while the data is
  read-only).
