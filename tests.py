import pytest
from eda_schema import NetlistPowerProfile
from eda_schema.errors import ValidationError

POWER_DATA = {
    'internal_io_pad': 0.0,
    'switching_io_pad': 0.0,
    'leakage_io_pad': 0.0,
    'total_io_pad': 0.0,
    'internal_memory': 0.0,
    'switching_memory': 0.0,
    'leakage_memory': 0.0,
    'total_memory': 0.0,
    'internal_black_box': 0.0,
    'switching_black_box': 0.0,
    'leakage_black_box': 0.0,
    'total_black_box': 0.0,
    'internal_clock_network': 0.0,
    'switching_clock_network': 0.0,
    'leakage_clock_network': 0.0,
    'total_clock_network': 0.0,
    'internal_register': 0.0,
    'switching_register': 0.6675,
    'leakage_register': 270390000.0,
    'total_register': 271.0604,
    'internal_sequential': 0.0,
    'switching_sequential': 0.1011,
    'leakage_sequential': 53865000.0,
    'total_sequential': 53.9663,
    'internal_combinational': 0.0,
    'switching_combinational': 4.8589,
    'leakage_combinational': 259620000.0,
    'total_combinational': 264.4814,
}

def test_netlist_power_profile():
    """
    Test creating a NetlistPowerProfile object and accessing its attributes.
    """
    netlist_power_profile = NetlistPowerProfile(POWER_DATA)

    assert netlist_power_profile.internal_io_pad == 0
    assert netlist_power_profile.switching_register == 0.6675

    netlist_power_profile_dict = netlist_power_profile.asdict()
    assert netlist_power_profile_dict == POWER_DATA


def test_netlist_power_profile_validation():
    """
    Test validation of invalid JSON data when creating a NetlistPowerProfile object.
    """
    POWER_DATA['internal_io_pad'] = "0"
    with pytest.raises(ValidationError):
        NetlistPowerProfile(POWER_DATA)
