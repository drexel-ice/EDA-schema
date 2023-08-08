from eda_schema.base import BaseSchema


class NetlistPowerProfile(BaseSchema):
    """Class for representing power metric data using a JSON schema."""
    title = "netlist_power_profile"
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                'internal_io_pad': {"type": "number"},
                'switching_io_pad': {"type": "number"},
                'leakage_io_pad': {"type": "number"},
                'total_io_pad': {"type": "number"},
                'internal_memory': {"type": "number"},
                'switching_memory': {"type": "number"},
                'leakage_memory': {"type": "number"},
                'total_memory': {"type": "number"},
                'internal_black_box': {"type": "number"},
                'switching_black_box': {"type": "number"},
                'leakage_black_box': {"type": "number"},
                'total_black_box': {"type": "number"},
                'internal_clock_network': {"type": "number"},
                'switching_clock_network': {"type": "number"},
                'leakage_clock_network': {"type": "number"},
                'total_clock_network': {"type": "number"},
                'internal_register': {"type": "number"},
                'switching_register': {"type": "number"},
                'leakage_register':{"type": "number"},
                'total_register': {"type": "number"},
                'internal_sequential': {"type": "number"},
                'switching_sequential': {"type": "number"},
                'leakage_sequential': {"type": "number"},
                'total_sequential': {"type": "number"},
                'internal_combinational': {"type": "number"},
                'switching_combinational': {"type": "number"},
                'leakage_combinational': {"type": "number"},
                'total_combinational': {"type": "number"},
            }
        }
    }
