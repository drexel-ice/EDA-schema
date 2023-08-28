import pytest
from eda_schema import entity
from eda_schema.errors import ValidationError


POWER_DATA = {
    'internal_power': 0.0,
    'switching_power': 0.6675,
    'leakage_power': 0.0,
    'combinational_power': 0.1,
    'sequential_power': 0.1,
    'macro_power': 0,
    'total_power': 0.8675,
}

def test_netlist_power_profile():
    """
    Test creating a NetlistPowerMetrics object and accessing its attributes.
    """
    netlist_power_profile = entity.PowerMetricsEntity(POWER_DATA)

    assert netlist_power_profile.internal_power == 0
    assert netlist_power_profile.switching_power == 0.6675

    netlist_power_profile_dict = netlist_power_profile.asdict()
    assert netlist_power_profile_dict == POWER_DATA


def test_netlist_power_profile_validation():
    """
    Test validation of invalid JSON data when creating a NetlistPowerMetrics object.
    """
    POWER_DATA['internal_power'] = "0"
    with pytest.raises(ValidationError):
        entity.PowerMetricsEntity(POWER_DATA)
