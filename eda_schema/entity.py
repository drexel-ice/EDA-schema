from eda_schema.base import BaseEntity, GraphEntity


class NetlistEntity(GraphEntity):
    """Class for representing netlist data using a JSON schema."""

    title = "netlist"
    cell_metrics = None
    area_metrics = None
    power_metrics = None
    critical_path_metrics = None
    timing_paths = {}
    clock_trees = {}

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
                "cell_density": {"type": ["number", "null"]},
                "pin_density": {"type": ["number", "null"]},
                "net_density": {"type": ["number", "null"]},
            },
        },
    }


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
                "net_area": {"type": "number"},
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
                "path_type": {"type": "string"},
                "worst_slack": {"type": "number"},
                "no_of_slack_violations": {"type": "number"},
                "worst_negative_slack": {"type": "number"},
                "total_negative_slack": {"type": "number"},
                "no_of_setup_violations": {"type": "number"},
                "worst_setup_violation": {"type": "number"},
                "total_setup_violation": {"type": "number"},
                "no_of_hold_violations": {"type": "number"},
                "worst_hold_violation": {"type": "number"},
                "total_hold_violation": {"type": "number"},
            },
        },
    }


class GateEntity(BaseEntity):
    """Class for representing standard cell data using a JSON schema."""

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
                "leakage_power": {"type": "number"},
                "input_capacitance": {"type": "number"},
                "output_capacitance": {"type": "number"},
            },
        },
    }


class InterconnectEntity(GraphEntity):
    """Class for representing standard cell data using a JSON schema."""

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
    """Class for representing standard cell data using a JSON schema."""

    title = "standard_cell"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "length": {"type": ["number", "null"]},
                "x1": {"type": ["number", "null"]},
                "y2": {"type": ["number", "null"]},
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
    """Class for representing standard cell data using a JSON schema."""

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
                "is_critical_path": {"type": "boolean"},
            },
        },
    }


class TimingPointEntity(BaseEntity):
    """Class for representing standard cell data using a JSON schema."""

    title = "timing_point"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "cell_delay": {"type": "number"},
                "arrival_time": {"type": "number"},
                "node_depth": {"type": "number"},
            },
        },
    }
