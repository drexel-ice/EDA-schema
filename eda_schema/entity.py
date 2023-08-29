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
                "worst_slack": {"type": "number"},
                "no_of_slack_violations": {"type": "number"},
                "worst_negative_slack": {"type": "number"},
                "total_negative_slack": {"type": "number"},
                "no_of_hold_violations": {"type": "number"},
                "worst_hold_violation": {"type": "number"},
                "total_hold_violation": {"type": "number"},
            },
        },
    }
