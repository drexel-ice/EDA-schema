from eda_schema.base import BaseEntity


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
