import pytest
from eda_schema import entity
from eda_schema.errors import ValidationError

NETLIST_DATA = {
    'width': 10,
    'height': 10,
    "no_of_inputs": 10,
    "no_of_outputs": 10,
    "cell_density": 0.5,
    "pin_density": 0.5,
    "net_density": 0.5,
}

def test_netlist():
    """
    Test creating a Netlist object and accessing its attributes.
    """
    netlist = entity.NetlistEntity(NETLIST_DATA)

    assert netlist.width == 10
    assert netlist.cell_density == 0.5

    print(netlist.asdict())
    netlist_dict = netlist.asdict()
    assert netlist_dict == NETLIST_DATA


def test_netlist_validation():
    """
    Test validation of invalid JSON data when creating a Netlist object.
    """
    invalid_data = dict(NETLIST_DATA)
    invalid_data['no_of_inputs'] = "10"
    with pytest.raises(ValidationError):
        entity.NetlistEntity(invalid_data)
    
    valid_data = dict(NETLIST_DATA)
    valid_data['cell_density'] = None
    assert entity.NetlistEntity(NETLIST_DATA) is not None


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
