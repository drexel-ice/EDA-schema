from copy import deepcopy

from eda_schema.base import BaseEntity, GraphEntity

KEY_COLUMNS = ["circuit", "netlist_id", "phase"]
PHASES = ["floorplan", "global_place", "place_resized", "detailed_place", "cts", "global_route", "detailed_route"]


class FlowEntity(BaseEntity):
    """Class for representing netlist data using a JSON schema."""

    title = "flow"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "version": {"type": ["number", "null"]},
                "design_type": {"type": ["string", "null"]},
            },
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stages = {}

class StageEntity(BaseEntity):
    """Class for representing netlist data using a JSON schema."""

    title = "stage"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.netlist = {}
        self.cell_metrics = None
        self.area_metrics = None
        self.power_metrics = None
        self.timing_metrics = None

class NetlistEntity(GraphEntity):
    """Class for representing netlist data using a JSON schema."""

    title = "netlist"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "width": {"type": ["number", "null"]},
                "height": {"type": ["number", "null"]},
                "no_of_inputs": {"type": "number"},
                "no_of_outputs": {"type": "number"},
                "no_of_cells": {"type": "number"},
                "no_of_nets": {"type": "number"},
                "utilization": {"type": "number"},
            },
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cell_metrics = None
        self.area_metrics = None
        self.power_metrics = None
        self.timing_metrics = None
        self.timing_graph = {}
        self.timing_paths = {}
        self.clock_trees = {}


class CellMetricsEntity(BaseEntity):
    """Class for representing cell metric data using a JSON schema."""

    title = "cell_metrics"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "no_of_combinational_cells": {"type": "number"},
                "no_of_sequential_cells": {"type": "number"},
                "no_of_buffers": {"type": "number"},
                "no_of_inverters": {"type": "number"},
                "no_of_fillers": {"type": "number"},
                "no_of_tap_cells": {"type": "number"},
                "no_of_diodes": {"type": "number"},
                "no_of_macros": {"type": "number"},
                "no_of_total_cells": {"type": "number"},
            },
        },
    }


class AreaMetricsEntity(BaseEntity):
    """Class for representing area metric data using a JSON schema."""

    title = "area_metrics"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "combinational_cell_area": {"type": "number"},
                "sequential_cell_area": {"type": "number"},
                "buffer_area": {"type": "number"},
                "inverter_area": {"type": "number"},
                "filler_area": {"type": "number"},
                "tap_cell_area": {"type": "number"},
                "diode_area": {"type": "number"},
                "macro_area": {"type": "number"},
                "cell_area": {"type": "number"},
                "core_area": {"type": "number"},
                "die_area": {"type": "number"},
                "total_area": {"type": "number"},
            },
        },
    }


class PowerMetricsEntity(BaseEntity):
    """Class for representing power metric data using a JSON schema."""

    title = "power_metrics"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "combinational_power": {"type": "number"},
                "sequential_power": {"type": "number"},
                "macro_power": {"type": "number"},
                "internal_power": {"type": "number"},
                "switching_power": {"type": "number"},
                "leakage_power": {"type": "number"},
                "total_power": {"type": "number"},
            },
        },
    }


class TimingMetricsEntity(BaseEntity):
    """Class for representing critical path metric data using a JSON schema."""

    title = "timing_metrics"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "total_negative_slack": {"type": "number"},
                "worst_slack": {"type": "number"},
                "critical_path_arrival_time": {"type": "number"},
                "critical_path_required_time": {"type": "number"},
                "critical_path_startpoint": {"type": "string"},
                "critical_path_endpoint": {"type": "string"},
                "no_of_violating_endpoints": {"type": "number"},
            },
        },
    }


class PortEntity(BaseEntity):
    """Class for representing input/output port data using a JSON schema."""

    title = "port"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "direction": {"type": "string"},
                "x": {"type": ["number", "null"]},
                "y": {"type": ["number", "null"]},
                "load_capacitance": {"type": ["number", "null"]},
            },
        },
    }


class GateEntity(BaseEntity):
    """Class for representing gate data using a JSON schema."""

    title = "gate"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "standard_cell": {"type": "string"},
                "no_of_fanins": {"type": "number"},
                "no_of_fanouts": {"type": "number"},
                "llx": {"type": ["number", "null"]},
                "lly": {"type": ["number", "null"]},
                "urx": {"type": ["number", "null"]},
                "ury": {"type": ["number", "null"]},
                "is_sequential": {"type": "boolean"},
                "is_filler": {"type": "boolean"},
                "is_inverter": {"type": "boolean"},
                "is_buffer": {"type": "boolean"},
                "is_diode": {"type": "boolean"},
            },
        },
    }


class StandardCellEntity(BaseEntity):
    """Class for representing standard cell data using a JSON schema."""

    title = "standard_cell"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "width": {"type": "number"},
                "height": {"type": "number"},
                "no_of_input_pins": {"type": "number"},
                "no_of_output_pins": {"type": "number"},
                "is_sequential": {"type": "boolean"},
                "is_inverter": {"type": "boolean"},
                "is_buffer": {"type": "boolean"},
                "drive_strength": {"type": ["number", "null"]},
                "input_capacitance_min": {"type": ["number", "null"]},
                "input_capacitance_max": {"type": ["number", "null"]},
                "input_capacitance_mean": {"type": ["number", "null"]},
                "output_capacitance_min": {"type": ["number", "null"]},
                "output_capacitance_max": {"type": ["number", "null"]},
                "output_capacitance_mean": {"type": ["number", "null"]},
                "leakage_power_min": {"type": ["number", "null"]},
                "leakage_power_max": {"type": ["number", "null"]},
                "leakage_power_provided": {"type": "number"},
            },
        },
    }


class PinEntity(BaseEntity):
    """Class for representing pin data using a JSON schema."""

    title = "pin"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "type": {"type": "string"},
                "direction": {"type": "string"},
                "is_in_clk": {"type": "boolean"},
                "is_startpoint": {"type": "boolean"},
                "is_endpoint": {"type": "boolean"},

                "setup_rise_slew": {"type": ["number", "null"]},
                "setup_fall_slew": {"type": ["number", "null"]},
                "hold_rise_slew": {"type": ["number", "null"]},
                "hold_fall_slew": {"type": ["number", "null"]},

                "setup_rise_slack": {"type": ["number", "null"]},
                "setup_fall_slack": {"type": ["number", "null"]},
                "hold_rise_slack": {"type": ["number", "null"]},
                "hold_fall_slack": {"type": ["number", "null"]},

                "load_capacitance": {"type": ["number", "null"]},
                "ir_drop": {"type": ["number", "null"]},
                "switching_activity": {"type": ["number", "null"]},
            }
        }
    }


class InterconnectEntity(GraphEntity):
    """Class for representing interconnect data using a JSON schema."""

    title = "interconnect"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "is_special_net": {"type": "boolean"},
                "no_of_fanouts": {"type": "number"},
                "x_min": {"type": ["number", "null"]},
                "y_min": {"type": ["number", "null"]},
                "x_max": {"type": ["number", "null"]},
                "y_max": {"type": ["number", "null"]},
                "length": {"type": ["number", "null"]},
                "hpwl": {"type": ["number", "null"]},
                "rudy": {"type": ["number", "null"]},
                "resistance": {"type": ["number", "null"]},
                "capacitance": {"type": ["number", "null"]},
                "total_coupling_capacitance": {"type": ["number", "null"]},
            },
        },
    }


class WireEntity(BaseEntity):
    """Class for representing interconnect segment data using a JSON schema."""

    title = "interconnect_segment"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "length": {"type": ["number", "null"]},
                "metal_layer": {"type": "string"},
                "x1": {"type": ["number", "null"]},
                "y1": {"type": ["number", "null"]},
                "x2": {"type": ["number", "null"]},
                "y2": {"type": ["number", "null"]},
                "x": {"type": ["number", "null"]},
                "y": {"type": ["number", "null"]},
                "rudy": {"type": ["number", "null"]},
                "resistance": {"type": ["number", "null"]},
                "capacitance": {"type": ["number", "null"]},
            },
        },
    }


class TimingGraphEntity(GraphEntity):
    """Class for representing timing path data using a JSON schema."""

    title = "timing_graph"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {},
        },
    }


class TimingPathEntity(GraphEntity):
    """Class for representing timing path data using a JSON schema."""

    title = "timing_path"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "startpoint": {"type": "string"},
                "endpoint": {"type": "string"},
                "path_type": {"type": "string"},
                "arrival_time": {"type": "number"},
                "required_time": {"type": "number"},
                "slack": {"type": "number"},
                "no_of_gates": {"type": "number"},
                # "no_of_pins": {"type": "number"},
                "is_critical_path": {"type": "boolean"},
            },
        },
    }


class TimingPathPinEntity(BaseEntity):
    """Class for representing timing path point data using a JSON schema."""

    title = "timing_path_pin"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "pin": {"type": ["string", "null"]},
                "delay": {"type": "number"},
                "arrival_time": {"type": "number"},
                "slew": {"type": "number"},
                "is_rise_transition": {"type": "boolean"},
                "is_fall_transition": {"type": "boolean"},
            },
        },
    }


class ClockTreeEntity(GraphEntity):
    """Class for representing clock tree using a JSON schema."""

    title = "clock_tree"

    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "clock_source": {"type": "string"},
                "no_of_buffers": {"type": "number"},
                "no_of_clock_sinks": {"type": "number"},
            },
        },
    }

    def load_from_netlist(self, netlist, clock_source, dff_cells):
        """
        Load clock tree data from a netlist.

        Args:
            netlist: Netlist data.
            clock_source: Clock source information.
            dff_cells: D flip-flop information.
        """
        self._netlist = netlist
        self._dff_cells = dff_cells
        self.source = clock_source

        self._no_of_clock_sinks = 0
        self._no_of_buffers = 0

        cts_nodes = self._traverse_cts(clock_source)
        cts_netlist_dict = deepcopy(self._netlist.subgraph(cts_nodes).__dict__)

        super().__init__({
            "clock_source": clock_source,
            "no_of_clock_sinks": self._no_of_clock_sinks,
            "no_of_buffers": self._no_of_buffers,
        })
        self.__dict__.update(cts_netlist_dict)

    def _traverse_cts(self, node):
        """
        Traverse the clock tree structure starting from a given node.

        Args:
            node: Starting node for traversal.

        Returns:
            list: List of traversed nodes in the clock tree.
        """
        traversed_nodes = [node]
        stack = [node]

        while stack:
            current_node = stack.pop()
            for output in self._netlist.successors(current_node):
                if output not in traversed_nodes:
                    traversed_nodes.append(output)
                    output_node_data = self._netlist.nodes[output]
                    if output_node_data["type"] == "GATE" and output_node_data["entity"].standard_cell in self._dff_cells:
                        self._no_of_clock_sinks += 1
                        continue
                    stack.append(output)

        return traversed_nodes
