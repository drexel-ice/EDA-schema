from copy import deepcopy
from eda_schema.base import BaseEntity, GraphEntity

KEY_COLUMNS = ["circuit", "netlist_id", "phase"]
PHASES = ["floorplan", "place", "cts", "route"]


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
                "cell_density": {"type": ["number", "null"]},
                "pin_density": {"type": ["number", "null"]},
                "net_density": {"type": ["number", "null"]},
            },
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cell_metrics = None
        self.area_metrics = None
        self.power_metrics = None
        self.critical_path_metrics = None
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
                "macro_area": {"type": "number"},
                "cell_area": {"type": "number"},
                "net_area": {"type": ["number", "null"]},
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


class CriticalPathMetricsEntity(BaseEntity):
    """Class for representing critical path metric data using a JSON schema."""

    title = "critical_path_metrics"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "startpoint": {"type": "string"},
                "endpoint": {"type": "string"},
                "worst_arrival_time": {"type": "number"},
                "worst_slack": {"type": "number"},
                "total_negative_slack": {"type": "number"},
                "no_of_timing_paths": {"type": "number"},
                "no_of_slack_violations": {"type": "number"},
            },
        },
    }


class IOPortEntity(BaseEntity):
    """Class for representing input/output port data using a JSON schema."""

    title = "io_port"
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
                "capacitance": {"type": ["number", "null"]},
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
                "x": {"type": ["number", "null"]},
                "y": {"type": ["number", "null"]},
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
                "no_of_inputs": {"type": "number"},
                "no_of_outputs": {"type": "number"},
                "x_min": {"type": ["number", "null"]},
                "y_min": {"type": ["number", "null"]},
                "x_max": {"type": ["number", "null"]},
                "y_max": {"type": ["number", "null"]},
                "hwpl": {"type": ["number", "null"]},
                "rudy": {"type": ["number", "null"]},
                "resistance": {"type": ["number", "null"]},
                "capacitance": {"type": ["number", "null"]},
            },
        },
    }


class InterconnectSegmentEntity(BaseEntity):
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
                "sort_index": {"type": "number"},
                "arrival_time": {"type": "number"},
                "required_time": {"type": "number"},
                "slack": {"type": "number"},
                "no_of_gates": {"type": "number"},
                "is_critical_path": {"type": "boolean"},
            },
        },
    }


class TimingPointEntity(BaseEntity):
    """Class for representing timing path point data using a JSON schema."""

    title = "timing_point"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "cell_delay": {"type": "number"},
                "arrival_time": {"type": "number"},
                "slew": {"type": "number"},
                "is_rise_transition": {"type": "boolean"},
                "is_fall_transition": {"type": "boolean"},
                "node_depth": {"type": "number"},
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
                "no_of_buffers": {"type": "number"},
                "no_of_clock_sinks": {"type": "number"},
            },
        },
    }

    def load_from_netlist(self, netlist, clock_source, dffs):
        """
        Load clock tree data from a netlist.

        Args:
            netlist: Netlist data.
            clock_source: Clock source information.
            dffs: D flip-flop information.
        """
        self._netlist = netlist
        self._dffs = dffs
        self.source = clock_source

        self._no_of_clock_sinks = 0
        self._no_of_buffers = 0

        cts_nodes = self.traverse_cts(clock_source)
        cts_netlist_dict = deepcopy(self._netlist.subgraph(cts_nodes).__dict__)

        super().__init__({
            "no_of_clock_sinks": self._no_of_clock_sinks,
            "no_of_buffers": self._no_of_buffers,
        })
        self.__dict__.update(cts_netlist_dict)

    def traverse_cts(self, node):
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
                    if output not in self._dffs:
                        stack.append(output)
                    else:
                        self._no_of_clock_sinks += 1

        return traversed_nodes
