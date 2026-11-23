MCP Server
==========

EDA-Schema ships an optional `Model Context Protocol <https://modelcontextprotocol.io>`_
(MCP) server. It lets an LLM agent, such as Claude Code, Claude Desktop or any
other MCP client, explore an EDA-Schema dataset by calling tools, without writing
Parquet or pandas code. For example, an agent can answer:

* *"How does the worst slack of gcd-000001 evolve across stages?"*
* *"Which setup path is worst at the final stage, and where does its delay come from?"*
* *"Show me the routing map and the IR-drop heatmap after detailed routing."*

The server is **read-only** and keeps every response small enough for a model's
context window. Large data (netlist graphs, raw images, element tables) is
summarized, paginated or rendered rather than returned whole.

.. note::

   This page documents **phase 1** of the plan in ``mcp_plan.md``:
   14 tools and 8 resources. Deeper per-flow analysis, dataset-wide analytics,
   exports and HTTP transport come in later phases.


One session, one PDK
--------------------

The EDA-Schema-V2 dataset is distributed as **one dataset root per PDK**
(for example ``eda-schema-v2/nangate45``), each with the same layout as the
sample in ``dataset/test``. An MCP server process is bound to exactly one such
root for its whole lifetime:

* every response carries a ``dataset`` block with the PDK and a root id;
* no tool accepts a ``pdk`` argument;
* the server instructions tell the model not to compare numbers across
  servers.

Cross-PDK comparison is **not supported**: units, standard-cell libraries and
timing scales differ between PDKs. To work with several PDKs, register one
server per PDK (see `Connecting a client`_). The client keeps their tools
separate.


Installation
------------

The server is an optional extra, so core installs are unchanged:

.. code-block:: bash

   pip install -e ".[mcp]"      # from a checkout
   # installs mcp>=2.3 and pillow, and the `eda-schema-mcp` command

A Docker image with everything preinstalled (including Graphviz for
``pygraphviz``) is defined in ``docker/mcp/Dockerfile``:

.. code-block:: bash

   docker build -f docker/mcp/Dockerfile -t eda-schema-mcp:dev .


Running the server
------------------

.. code-block:: bash

   eda-schema-mcp --dataset /path/to/eda-schema-v2/sky130hd
   # equivalent
   EDA_SCHEMA_DATASET=/path/to/eda-schema-v2/sky130hd python -m eda_schema.mcp

The server speaks MCP over **stdio**: an MCP client starts it as a subprocess.
Logs go to stderr, because stdout carries the protocol.

.. list-table:: Command-line options
   :header-rows: 1
   :widths: 28 14 58

   * - Option
     - Default
     - Meaning
   * - ``--dataset PATH``
     - ``$EDA_SCHEMA_DATASET``
     - Dataset root of one PDK. Required.
   * - ``--max-rows N``
     - ``200``
     - Hard cap for any tool's ``limit`` argument.
   * - ``--max-response-chars N``
     - ``40000``
     - Character budget of one tool response (about 4 characters per token,
       so about 10k tokens).
   * - ``--precision N``
     - ``6``
     - Significant digits for floats in responses.
   * - ``--log-level``
     - ``WARNING``
     - ``DEBUG``, ``INFO``, ``WARNING`` or ``ERROR``.

The server exits with status 2 and a message if the root is not an EDA-Schema
dataset (it must contain ``design_flows/table.parquet``).


Connecting a client
-------------------

**Claude Code.** Add the server for the current project:

.. code-block:: bash

   claude mcp add eda-sky130 -- eda-schema-mcp --dataset /data/eda-schema-v2/sky130hd

or commit a ``.mcp.json`` at the project root, with one entry per PDK:

.. code-block:: json

   {
     "mcpServers": {
       "eda-sky130": {
         "command": "eda-schema-mcp",
         "args": ["--dataset", "/data/eda-schema-v2/sky130hd"]
       },
       "eda-ng45": {
         "command": "eda-schema-mcp",
         "args": ["--dataset", "/data/eda-schema-v2/nangate45"]
       }
     }
   }

**Docker.** Any client that can start a command can run the image instead.
Mount the dataset read-only and keep ``-i`` for stdio:

.. code-block:: json

   {
     "mcpServers": {
       "eda-sky130": {
         "command": "docker",
         "args": ["run", "--rm", "-i",
                  "-v", "/data/eda-schema-v2/sky130hd:/data:ro",
                  "eda-schema-mcp:dev", "eda-schema-mcp", "--dataset", "/data"]
       }
     }
   }

Claude Desktop and other clients use the same ``command`` / ``args`` form in
their own configuration files. ``examples/08_mcp/mcp.json`` contains both
variants.


What the server offers
----------------------

Tools
^^^^^

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Tool
     - Purpose
   * - ``get_dataset_info``
     - PDK, identity, units, counts, entities and image kinds, and limits. Call first.
   * - ``list_designs``
     - Designs with flow counts, run-status breakdown and clock-period range.
   * - ``list_flows``
     - Flows with constraints; filter by design, status, constraint value or range; paginated.
   * - ``get_flow``
     - One flow's constraints and per-stage status.
   * - ``get_qor``
     - Area, cell, power, timing and netlist metrics of one stage.
   * - ``get_stage_evolution``
     - Metrics across the 8 stages, with the largest stage-to-stage change.
   * - ``compare_flows``
     - Up to 20 flows side by side at one stage.
   * - ``aggregate_metrics``
     - Grouped statistics (count, mean, std, min, max, median, p10, p90) over flows.
   * - ``get_timing_summary``
     - STA summary plus statistics computed from stored setup or hold paths.
   * - ``list_timing_paths``
     - Timing paths sorted by slack (or another column); paginated.
   * - ``get_timing_path``
     - One path as ordered cell and net arcs, with delay totals.
   * - ``get_netlist_summary``
     - Netlist counts, die size, area and the most-used standard cells.
   * - ``list_images``
     - Images stored for one stage, grouped by entity.
   * - ``render_image``
     - A stored layout image or heatmap as a PNG (at most 1024 px) plus statistics.

Every argument is documented in :doc:`mcp_tools`, which is generated from the
live tool schemas.

Resources
^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - URI
     - Content
   * - ``eda://dataset``
     - Same as ``get_dataset_info``.
   * - ``eda://dataset/summary``
     - Designs with flow counts.
   * - ``eda://schema``
     - Every entity: primary key, columns present, images, and fields that are
       defined in the schema but absent from this dataset.
   * - ``eda://schema/{entity}``
     - One entity.
   * - ``eda://stages``
     - Stages in flow order with the image kinds stored at each.
   * - ``eda://flows/{flow_id}``
     - Same as ``get_flow``.
   * - ``eda://flows/{flow_id}/{stage}/qor``
     - Same as ``get_qor``.
   * - ``eda://image/{entity}/{name}/{flow_id}/{stage}``
     - PNG (512 px) of one image.


Responses and limits
--------------------

Every tool returns the same JSON envelope, both as text and as structured
content:

.. code-block:: json

   {
     "dataset":   {"pdk": "sky130hd", "root_id": "sky130hd@244b2412"},
     "data":      [ {"startpoint": "_381_/Q", "endpoint": "_395_/D", "slack": -0.2732} ],
     "returned":  20,
     "total":     137,
     "truncated": true,
     "next_cursor": "20",
     "hint": "Use get_timing_summary for the distribution instead of paging through all paths."
   }

* **Row limit.** List tools take ``limit`` (default 20–50) and are clamped to
  ``--max-rows``.
* **Size budget.** If the serialized response would exceed
  ``--max-response-chars``, rows are dropped from the end, ``truncated`` is set
  and the ``hint`` says so.
* **Pagination.** When ``truncated`` is true, pass ``next_cursor`` back as
  ``cursor`` to get the next page.
* **Numbers.** Floats are rounded to ``--precision`` significant digits.
  Missing values are ``null``. Infinite slacks (unconstrained transitions) are
  the strings ``"inf"`` / ``"-inf"``.
* **No raw bulk data.** Graphs and image arrays are never returned inline.
  Images come back as PNGs: binary maps are max-pooled so one-pixel wires
  survive, and scalar maps are colour-mapped.

Errors are returned as tool errors the model can act on. They name the bad
value and suggest valid ones:

.. code-block:: text

   Unknown flow_id 'gcd-1'. Closest matches: gcd-000001.
   Unknown stage 'cst'. Closest matches: cts.


Example session
---------------

The sequence an agent typically uses for *"why is gcd-000001 failing timing?"*:

#. ``get_dataset_info``: which PDK, how many flows.
#. ``get_stage_evolution(flow_id="gcd-000001", metrics=["worst_slack"])``:
   worst slack is -0.0651 at floorplan, drops to -0.6051 at global_place,
   and ends at -0.2732.
#. ``list_timing_paths(flow_id="gcd-000001", limit=3)``: the worst path is
   ``_381_/Q -> _395_/D``.
#. ``get_timing_path(..., startpoint="_381_/Q", endpoint="_395_/D", stage="final")``:
   28 arcs from the launch clock to the endpoint check.
#. ``render_image(entity="netlists", name="routing", flow_id="gcd-000001")``:
   the routing map.

``examples/08_mcp/`` contains runnable scripts for this flow: in-process,
over stdio, and a renderer that saves every image of a stage.


Dataset identity
----------------

The PDK name is taken from, in order:

#. a ``dataset.json`` manifest at the dataset root (recommended);
#. the platform path in ``openroad_dataloader.log``
   (``.../platforms/<pdk>/lef/...``);
#. the prefix of the standard-cell names (``sky130_fd_sc_hd__`` gives
   ``sky130hd``, ``sg13g2_`` gives ``ihp-sg13g2``, ``AND2_X1`` gives
   ``nangate45``, and so on);
#. otherwise ``"unknown"``, with a warning in the log.

The manifest is optional but is the only way to publish **units**:

.. code-block:: json

   {
     "pdk": "sky130hd",
     "schema_version": "2.0.0",
     "units": {"time": "ns", "capacitance": "fF", "power": "uW", "distance": "um"}
   }

Without a manifest, ``get_dataset_info`` reports units as unknown, and values
are in the dataset's native units.


Known data caveats
------------------

These come from the data, not the server. Keep them in mind when you read
results:

* **Arc delay attribution.** In the sample, cell-arc delays are tiny (about
  0.001) and net-arc delays carry most of the path delay. For example, the
  net arc driven by a clock buffer reports 0.137. This suggests the driver's
  cell delay is stored on the following net arc. ``get_timing_path`` reports
  the stored values unchanged, so treat its cell/net delay split with care
  until this is confirmed against the OpenSTA reports.
* **Schema drift.** Some fields defined in the schema are not present in the
  tables. For example, ``GateEntity`` power fields and ``NetlistEntity``
  ``total_wirelength`` are absent. ``eda://schema/{entity}`` lists them under
  ``defined_but_absent``.
* **Image-only entities.** ``power_delivery_networks`` and
  ``routability_metrics`` tables contain only keys; their content is the
  images.
* **Placement-density sweep.** The paper also sweeps placement density, but
  ``constraints`` has no column for it, so several flows can have identical
  constraints.


Development
-----------

All development and testing runs in the Docker image, with the checkout
mounted. Run as your own user so files written into the checkout are not owned
by root:

.. code-block:: bash

   docker build -f docker/mcp/Dockerfile -t eda-schema-mcp:dev .
   alias edarun='docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/workspace eda-schema-mcp:dev'

   edarun pytest tests/mcp -p no:cacheprovider --cov=eda_schema.mcp --cov-report=term-missing
   edarun ruff check eda_schema/mcp tests/mcp
   edarun python examples/08_mcp/02_stdio_client.py
   edarun python scripts/gen_mcp_tool_docs.py        # regenerate docs/mcp_tools.rst

The tests use ``dataset/test`` plus a synthetic multi-flow copy built in a
temporary directory (``tests/mcp/conftest.py``), because the sample has only
one flow. They cover the context, the envelope, rendering, every tool, the MCP
protocol layer (in-process and over a real stdio subprocess), resources, the
CLI and the size budget.

**Adding a tool.**

#. Write a plain function in ``eda_schema/mcp/tools/`` whose first parameter
   is ``ctx: DatasetContext``. Describe its other parameters with
   ``Annotated[..., Field(description=...)]``, and return
   ``envelope.ok(...)`` or ``envelope.paged(...)``.
#. Raise ``McpInputError`` (or use ``ctx.require_*``) for bad input.
#. Append the function to ``TOOLS`` in ``eda_schema/mcp/server.py``.
#. Add tests, then regenerate the reference with
   ``python scripts/gen_mcp_tool_docs.py``.


API reference
-------------

The modules below do not depend on the ``mcp`` package.

.. automodule:: eda_schema.mcp.context
   :members: DatasetContext, ImageRef, parse_image_filename, STAGES, QOR_TABLES

.. automodule:: eda_schema.mcp.envelope
   :members: ok, paged, clean, round_sig, parse_cursor, Envelope

.. automodule:: eda_schema.mcp.render
   :members: to_png, downsample, stats, is_binary, load_npz

.. automodule:: eda_schema.mcp.errors
   :members:

.. toctree::
   :hidden:

   mcp_tools
