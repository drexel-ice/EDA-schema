## Multimodal Datamodel Schema

EDA-Schema is a multimodal data schema used to represent digital circuits throughout the RTL to GDSII physical design flow. Data is extracted from design tools after each stage of the EDA flow, including structural netlists, physical layout information, timing reports, parasitic extraction, power delivery analysis, and quality-of-results metrics. These artifacts are organized into a unified schema that captures both the structural composition and performance characteristics of a circuit as it progresses through the design flow. While later stages provide complete physical and analytical information, earlier stages still contain partial yet valuable structural representations and estimated performance metrics. The representation becomes progressively richer and more accurate at each stage.

A circuit in EDA-Schema is represented using multiple complementary modalities. Graph representations capture logical and physical connectivity through heterogeneous netlist graphs, clock network graphs, and timing path graphs. Spatial image representations capture placement, routing, clock tree structure, and power delivery networks as binary layout maps. Scalar spatial maps capture analyzed circuit features such as IR drop, electromigration, and routability congestion heatmaps. These multimodal representations are complemented by structured metric entities that store timing, power, area, cell composition, and routability metrics, providing a complete representation of both circuit structure and design quality.

Presented is the entity relationship diagram (ERD) of EDA-Schema. Organizational entities define the design flow hierarchy, structural entities represent circuit topology and physical composition, and metric entities capture quality-of-results measurements. Together, these entities provide a unified multimodal representation of digital physical design for analysis and machine learning applications. For each circuit, stage resolved snapshots are available for the following design phases:

- Post floorplan: `floorplan`
- Post global placement: `global_place`
- Post placement resize: `place_resize`
- Post detailed placement: `detailed_place`
- Post clock tree synthesis: `cts`
- Post global routing: `global_route`
- Post detailed routing: `detailed_route`
- Final design stage: `final`

![Alt text](images/schema.png)

The primary graph entities of the circuit and schema include:

### Netlist

The **Netlist** entity represents the complete logical and physical composition of a digital circuit and serves as the primary structural representation in EDA-Schema-V2. It is modeled as a heterogeneous graph where nodes correspond to circuit components and edges capture logical and physical connectivity between those components.

- **Nodes represent**:
  - **Input/output ports (IO):** External circuit interfaces that define signal entry and exit points.
  - **Gates (G):** Placed instances of standard cells that implement circuit functionality.
  - **Pins (P):** Input and output terminals of gates that define connection and timing endpoints.
  - **Nets (N):** Electrical interconnections that connect ports and gate pins.

- **Edges denote**:
  - Logical connectivity between ports, gates, pins, and nets.
  - Physical connectivity established through placement and routing throughout the design flow.

- **Gate entities** extend **Standard Cell** library definitions with design specific attributes such as placement coordinates, power characteristics, timing information, and physical layout properties.

- **Net entities** capture both logical wiring relationships and physical interconnect characteristics, including routing geometry, resistance, capacitance, and parasitic coupling.

<p><img src="images/netlist_graph.png" width="768"/></p>


In addition to its graph representation, the Netlist entity includes **spatial image representations** that model:

- Combinational cell placement: <p><img src="images/cell_placement_combinational.png" width="192" height="192" /></p>
- Sequential cell placement: <p><img src="images/cell_placement_sequential.png" width="192" height="192" /></p>
- Filler cell placement: <p><img src="images/cell_placement_fill.png" width="192" height="192" /></p>
- Pin placement: <p><img src="images/pin_placement.png" width="192" height="192" /></p>
- Routing layout: <p><img src="images/routing.png" width="192" height="192" /></p>
- Routing by individual metal layers
  - metal layer 1: <p><img src="images/routing_m1.png" width="192" height="192" /></p>
  - metal layer 5: <p><img src="images/routing_m5.png" width="192" height="192" /></p>

Together, these graph and image modalities provide a unified representation of circuit structure, physical implementation, and layout topology.


| Feature | Data Type | Unit | Source |
|---|---|---|---|
| **Netlist** |  |  |  |
| width | num | μm | DEF file |
| height | num | μm | DEF file |
| no_of_inputs | num | # | DEF file |
| no_of_outputs | num | # | DEF file |
| no_of_cells | num | # | DEF file |
| no_of_nets | num | # | DEF file |
| no_of_pins | num | # | DEF file |
| utilization | num | ratio | Calculated |
| total_wirelength | num | μm | DEF / Routed DEF |
| total_hpwl | num | μm | Calculated |
| cell_placement | binary map | spatial | Generated |
| cell_placement_combinational | binary map | spatial | Generated |
| cell_placement_sequential | binary map | spatial | Generated |
| cell_placement_filler | binary map | spatial | Generated |
| pin_placement | binary map | spatial | Generated |
| routing | binary map | spatial | DEF / Generated |
| routing_by_metal_layers | list[binary map] | spatial | DEF / Generated |
| **Standard Cell** |  |  |  |
| name | str |  | Liberty / LEF |
| function | str |  | Liberty |
| width | num | μm | LEF file |
| height | num | μm | LEF file |
| no_of_input_pins | num | # | LEF file |
| no_of_output_pins | num | # | LEF file |
| is_sequential | boolean |  | Calculated |
| is_inverter | boolean |  | Calculated |
| is_buffer | boolean |  | Calculated |
| is_filler | boolean |  | Calculated |
| is_diode | boolean |  | Calculated |
| drive_strength | num |  | Calculated |
| input_capacitance_min | num | fF | Liberty file |
| input_capacitance_max | num | fF | Liberty file |
| output_capacitance_min | num | fF | Liberty file |
| output_capacitance_max | num | fF | Liberty file |
| leakage_power_min | num | μW | Liberty file |
| leakage_power_max | num | μW | Liberty file |
| **Gate (G)** |  |  |  |
| name | str |  | DEF file |
| standard_cell | str |  | DEF file |
| x_min | num | μm | DEF file |
| y_min | num | μm | DEF file |
| x_max | num | μm | DEF file |
| y_max | num | μm | DEF file |
| no_of_inputs | num | # | DEF file |
| no_of_outputs | num | # | DEF file |
| internal_power | num | μW | QoR reports |
| switching_power | num | μW | QoR reports |
| leakage_power | num | μW | QoR reports |
| total_power | num | μW | Calculated |
| ir_drop_vdd | num | mV | PDNSim |
| ir_drop_vss | num | mV | PDNSim |
| **Pin (P)** |  |  |  |
| name | str |  | DEF / STA |
| direction | str |  | DEF file |
| x_min | num | μm | DEF file |
| y_min | num | μm | DEF file |
| x_max | num | μm | DEF file |
| y_max | num | μm | DEF file |
| is_startpoint | boolean |  | STA reports |
| is_endpoint | boolean |  | STA reports |
| setup_rise_slew | num | ns | STA reports |
| setup_fall_slew | num | ns | STA reports |
| hold_rise_slew | num | ns | STA reports |
| hold_fall_slew | num | ns | STA reports |
| setup_rise_slack | num | ns | STA reports |
| setup_fall_slack | num | ns | STA reports |
| hold_rise_slack | num | ns | STA reports |
| hold_fall_slack | num | ns | STA reports |
| load_capacitance | num | fF | STA / SPEF |
| switching_activity | num |  | Activity / Calculated |
| **Net (N)** |  |  |  |
| name | str |  | DEF file |
| is_special_net | boolean |  | DEF file |
| no_of_fanouts | num | # | DEF file |
| x_min | num | μm | DEF file |
| y_min | num | μm | DEF file |
| x_max | num | μm | DEF file |
| y_max | num | μm | DEF file |
| length | num | μm | Routed DEF |
| hpwl | num | μm | Calculated |
| resistance | num | ohm | SPEF file |
| capacitance | num | fF | SPEF file |
| total_coupling_capacitance | num | fF | SPEF file |
| **Port (IO)** |  |  |  |
| name | str |  | DEF file |
| direction | str |  | DEF file |
| x | num | μm | DEF file |
| y | num | μm | DEF file |

### Power Delivery Network

The **Power Delivery Network (PDN)** entity represents the physical and electrical network responsible for distributing power throughout the circuit. It models the routing structures used to deliver supply voltage (**VDD**) and ground (**VSS**) across the design while capturing spatial electrical analysis such as **IR drop** and **electromigration (EM)**. This representation enables joint analysis of power routing topology and localized electrical integrity.

- **Physical power network representation**
  - Captures dedicated **VDD routing**
  - Captures dedicated **VSS routing**
  - Models **power source locations**

- **Electrical analysis representation**
  - **IR drop maps** represent localized voltage drop across the layout
  - **Electromigration maps** represent current density related reliability stress
  - Spatial heatmaps enable localized power integrity analysis

These representations provide both structural and electrical visibility into the power distribution network, enabling ML models to learn relationships between routing topology, congestion, and power integrity.

In addition to electrical metrics, the PDN includes **spatial image representations** of:

- VSS routing: <p><img src="images/pdn_vss.png" width="192" height="192" /></p>
- VDD routing: <p><img src="images/pdn_vdd.png" width="192" height="192" /></p>
- Voltage source locations: <p><img src="images/pdn_power_source.png" width="192" height="192" /></p>
- IR drop heatmap: <p><img src="images/ir_drop.png" width="192" height="192" /></p>
- Electromigration heatmap: <p><img src="images/em.png" width="192" height="192" /></p>

| Feature | Data Type | Unit | Source |
|---|---|---|---|
| **Power Delivery Network** |  |  |  |
| pdn_routing_vdd | binary map | spatial | DEF / Generated |
| pdn_routing_vss | binary map | spatial | DEF / Generated |
| voltage_source | binary map | spatial | PDNSim / Generated |
| ir_drop_vdd | scalar map | mV | PDNSim |
| ir_drop_vss | scalar map | mV | PDNSim |
| em_vdd | scalar map | current density | PDNSim |
| em_vss | scalar map | current density | PDNSim |

### Clock Network

The **Clock Network** entity represents the clock distribution structure within a circuit, modeling how the clock signal propagates from its source to sequential elements throughout the design. It is derived as a subgraph of the Netlist and captures both the logical connectivity and physical implementation of the clock tree after clock tree synthesis and routing.

- **Clock Network is a substructure of the Netlist**
  - Follows the same heterogeneous graph representation
  - Captures the dedicated clock propagation network

- **Nodes represent**:
  - **Input/output ports (IO):** Clock source ports and external clock interfaces
  - **Gates (G):** Clock buffers, inverters, and sequential sink cells
  - **Pins (P):** Input and output terminals involved in clock propagation
  - **Nets (N):** Clock routing interconnections between clock elements

- **Edges denote**:
  - Logical clock connectivity
  - Physical routed connections of the clock tree

<p><img src="images/clock_network_graph.png" width="296" height="296" /></p>

In addition to its graph representation, the Clock Network includes **spatial image representations** of:

- Clock buffer placement: <p><img src="images/ct_combinational.png" width="192" height="192" /></p>
- Sequential cell placement: <p><img src="images/ct_sequential.png" width="192" height="192" /></p>
- Clock routing layout: <p><img src="images/ct_routing.png" width="192" height="192" /></p>
- Routing by metal layers

These multimodal representations enable structural, spatial, and routing analysis of clock distribution networks.


| Feature | Data Type | Unit | Source |
|---|---|---|---|
| **Clock Network** |  |  |  |
| clock_source | str |  | DEF / Clock definition |
| no_of_buffers | num | # | DEF file |
| no_of_clock_sinks | num | # | DEF file |
| cell_placement | binary map | spatial | Generated |
| cell_placement_combinational | binary map | spatial | Generated |
| cell_placement_sequential | binary map | spatial | Generated |
| pin_placement | binary map | spatial | Generated |
| routing | binary map | spatial | DEF / Generated |
| routing_by_metal_layers | list[binary map] | spatial | DEF / Generated |


### Timing Path

The **Timing Path** entity represents signal propagation paths extracted from Static Timing Analysis (STA), capturing the sequence of circuit elements traversed by a signal and the timing characteristics accumulated along that path. Timing Paths are modeled as directed subgraphs derived from the Netlist, enabling detailed path level timing analysis across the circuit.

- **Static Timing Analysis (STA) Timing Path**
  - Represents a signal path from a startpoint to an endpoint
  - Captures propagation through logic cells and interconnect networks
  - Includes both critical and non critical paths

- **Timing Path graphs are subgraphs of the Netlist**
  - Modeled as directed graphs
  - Represent timing propagation relationships between successive path elements

- **Nodes represent**:
  - **Pins (P):** Input and output pin endpoints along the path
  - **Input/output ports (IO):** External path startpoints or endpoints
  - **Cell Arcs (GA):** Propagation through logic gates
  - **Net Arcs (NA):** Propagation through routed interconnects

- **Edges denote**:
  - Ordered signal propagation from one timing element to the next
  - Timing dependencies between successive path components

This representation separates **cell delay propagation** from **interconnect delay propagation**, allowing timing behavior to be modeled structurally and electrically.

<p><img src="images/timing_path_graph.png" width="512"/></p>

| Feature | Data Type | Unit | Source |
|---|---|---|---|
| **Timing Path** |  |  |  |
| startpoint | str |  | STA reports |
| endpoint | str |  | STA reports |
| path_type | str |  | STA reports |
| arrival_time | num | ns | STA reports |
| required_time | num | ns | STA reports |
| slack | num | ns | STA reports |
| no_of_pins | num | # | STA reports |
| is_critical_path | boolean |  | STA reports |
| **Cell Arc (GA)** |  |  |  |
| gate | ref |  | STA reports |
| delay | num | ns | STA reports |
| arrival_time | num | ns | STA reports |
| slew | num | ns | STA reports |
| **Net Arc (NA)** |  |  |  |
| net | ref |  | STA / SPEF |
| delay | num | ns | STA reports |
| arrival_time | num | ns | STA reports |
| slew | num | ns | STA reports |
| capacitance | num | fF | SPEF file |

### Quality Metrics

Quality Metrics capture the quality-of-results (QoR) of a circuit at each design stage. In EDA-Schema-V2, these metrics are organized into structured metric entities that summarize circuit composition, area utilization, power consumption, timing performance, and routability characteristics.

| Feature | Data Type | Unit | Source |
|---|---|---|---|
| **Cell Metrics** |  |  |  |
| no_of_combinational_cells | num | # | QoR reports |
| no_of_sequential_cells | num | # | QoR reports |
| no_of_buffers | num | # | QoR reports |
| no_of_inverters | num | # | QoR reports |
| no_of_fillers | num | # | QoR reports |
| no_of_tap_cells | num | # | QoR reports |
| no_of_diodes | num | # | QoR reports |
| no_of_macros | num | # | QoR reports |
| no_of_total_cells | num | # | QoR reports |
| **Area Metrics** |  |  |  |
| combinational_cell_area | num | μm² | QoR reports |
| sequential_cell_area | num | μm² | QoR reports |
| buffer_area | num | μm² | QoR reports |
| inverter_area | num | μm² | QoR reports |
| filler_area | num | μm² | QoR reports |
| tap_cell_area | num | μm² | QoR reports |
| diode_area | num | μm² | QoR reports |
| macro_area | num | μm² | QoR reports |
| cell_area | num | μm² | QoR reports |
| total_area | num | μm² | QoR reports |
| **Power Metrics** |  |  |  |
| combinational_power | num | μW | QoR reports |
| sequential_power | num | μW | QoR reports |
| macro_power | num | μW | QoR reports |
| internal_power | num | μW | QoR reports |
| switching_power | num | μW | QoR reports |
| leakage_power | num | μW | QoR reports |
| total_power | num | μW | QoR reports |
| **Timing Metrics** |  |  |  |
| total_negative_slack | num | ns | STA reports |
| worst_slack | num | ns | STA reports |
| worst_arrival_time | num | ns | STA reports |
| worst_required_time | num | ns | STA reports |
| critical_path_startpoint | str |  | STA reports |
| critical_path_endpoint | str |  | STA reports |
| no_of_endpoints | num | # | STA reports |
| no_of_violating_endpoints | num | # | STA reports |
| **Routability Metrics** |  |  |  |
| rudy_net | scalar map | spatial | Calculated |
| rudy_pin | scalar map | spatial | Calculated |
| rudy_net_long | scalar map | spatial | Calculated |
| rudy_net_short | scalar map | spatial | Calculated |

The multimodal spatial representations include:

- Net based RUDY map: <p><img src="images/rudy_net.png" width="192" height="192" /></p>
- Pin based RUDY map: <p><img src="images/rudy_pin.png" width="192" height="192" /></p>
- Long range routing demand map: <p><img src="images/rudy_net_long.png" width="192" height="192" /></p>
- Short range routing demand map: <p><img src="images/rudy_net_short.png" width="192" height="192" /></p>
