"""
Tests for all entity classes.
"""
import pytest
from eda_schema import entity
from eda_schema.entity import DesignStages


class TestDesignStages:
    """Test DesignStages enum."""

    def test_design_stages_values(self):
        """Test DesignStages enum values."""
        assert DesignStages.FLOORPLAN.value == "floorplan"
        assert DesignStages.FINAL.value == "final"

    def test_design_stages_tolist(self):
        """Test converting DesignStages to list."""
        stages = DesignStages.tolist()
        assert isinstance(stages, list)
        assert "floorplan" in stages
        assert "final" in stages


class TestNetlistEntity:
    """Test NetlistEntity."""

    def test_netlist_entity_creation(self, sample_netlist_data):
        """Test creating NetlistEntity."""
        netlist = entity.NetlistEntity(**sample_netlist_data)
        assert netlist.flow_id == 'test_flow_001'
        assert netlist.stage == 'floorplan'
        assert netlist.width == 100.0
        assert netlist.height == 100.0
        assert netlist.no_of_cells == 100

    def test_netlist_entity_optional_fields(self, sample_netlist_data):
        """Test NetlistEntity with optional fields set to None."""
        data = sample_netlist_data.copy()
        data['width'] = None
        data['height'] = None

        netlist = entity.NetlistEntity(**data)
        assert netlist.width is None
        assert netlist.height is None

    def test_netlist_entity_node_types(self):
        """Test NetlistEntity NODE_TYPES."""
        assert 'GATE' in entity.NetlistEntity.NODE_TYPES
        assert 'PORT' in entity.NetlistEntity.NODE_TYPES
        assert 'NET' in entity.NetlistEntity.NODE_TYPES
        assert 'PIN' in entity.NetlistEntity.NODE_TYPES


class TestGateEntity:
    """Test GateEntity."""

    def test_gate_entity_creation(self, sample_gate_data):
        """Test creating GateEntity."""
        gate = entity.GateEntity(**sample_gate_data)
        assert gate.name == 'gate_001'
        assert gate.standard_cell == 'NAND2_X1'
        assert gate.x_min == 10.0
        assert gate.y_min == 20.0
        assert gate.x_max == 15.0
        assert gate.y_max == 25.0

    def test_gate_entity_optional_fields(self, sample_gate_data):
        """Test GateEntity with optional fields."""
        data = sample_gate_data.copy()
        data['x_min'] = None
        data['y_min'] = None
        data['x_max'] = None
        data['y_max'] = None

        gate = entity.GateEntity(**data)
        assert gate.x_min is None
        assert gate.y_min is None


class TestPortEntity:
    """Test PortEntity."""

    def test_port_entity_creation(self, sample_port_data):
        """Test creating PortEntity."""
        port = entity.PortEntity(**sample_port_data)
        assert port.name == 'port_001'
        assert port.direction == 'INPUT'
        assert port.x == 0.0
        assert port.y == 0.0

    def test_port_entity_directions(self):
        """Test PortEntity with different directions."""
        input_port = entity.PortEntity(
            flow_id='test', stage='test', name='in', direction='INPUT', x=0, y=0
        )
        output_port = entity.PortEntity(
            flow_id='test', stage='test', name='out', direction='OUTPUT', x=0, y=0
        )

        assert input_port.direction == 'INPUT'
        assert output_port.direction == 'OUTPUT'


class TestNetEntity:
    """Test NetEntity."""

    def test_net_entity_creation(self, sample_net_data):
        """Test creating NetEntity."""
        net = entity.NetEntity(**sample_net_data)
        assert net.name == 'net_001'
        assert net.is_special_net is False
        assert net.no_of_fanouts == 3

    def test_net_entity_optional_fields(self, sample_net_data):
        """Test NetEntity with optional fields."""
        data = sample_net_data.copy()
        data['x_min'] = 0.0
        data['y_min'] = 0.0
        data['x_max'] = 10.0
        data['y_max'] = 10.0

        net = entity.NetEntity(**data)
        assert net.x_min == 0.0
        assert net.y_max == 10.0


class TestPowerMetricsEntity:
    """Test PowerMetricsEntity."""

    def test_power_metrics_creation(self, sample_power_metrics_data):
        """Test creating PowerMetricsEntity."""
        power = entity.PowerMetricsEntity(**sample_power_metrics_data)
        assert power.total_power == 0.51
        assert power.combinational_power == 0.1
        assert power.sequential_power == 0.2

    def test_power_metrics_all_fields(self, sample_power_metrics_data):
        """Test all power metrics fields are accessible."""
        power = entity.PowerMetricsEntity(**sample_power_metrics_data)
        assert hasattr(power, 'internal_power')
        assert hasattr(power, 'switching_power')
        assert hasattr(power, 'leakage_power')

    def test_power_metrics_validation_invalid_type(self, sample_power_metrics_data):
        """Test validation catches invalid types in PowerMetricsEntity."""
        # Test that invalid type raises TypeError when validate() is called
        invalid_power_data = sample_power_metrics_data.copy()
        invalid_power_data['internal_power'] = "0"  # String instead of float
        # Dataclass will accept it, but validation should catch it
        power_profile = entity.PowerMetricsEntity(**invalid_power_data)
        with pytest.raises(TypeError):
            power_profile.validate()


class TestAreaMetricsEntity:  # pylint: disable=too-few-public-methods
    """Test AreaMetricsEntity."""

    def test_area_metrics_creation(self, sample_area_metrics_data):
        """Test creating AreaMetricsEntity."""
        area = entity.AreaMetricsEntity(**sample_area_metrics_data)
        assert area.total_area == 200.0
        assert area.cell_area == 165.0
        assert area.combinational_cell_area == 100.0


class TestCellMetricsEntity:  # pylint: disable=too-few-public-methods
    """Test CellMetricsEntity."""

    def test_cell_metrics_creation(self, sample_cell_metrics_data):
        """Test creating CellMetricsEntity."""
        cell_metrics = entity.CellMetricsEntity(**sample_cell_metrics_data)
        assert cell_metrics.no_of_total_cells == 100
        assert cell_metrics.no_of_combinational_cells == 80
        assert cell_metrics.no_of_sequential_cells == 20


class TestStandardCellEntity:
    """Test StandardCellEntity."""

    def test_standard_cell_creation(self, sample_standard_cell_data):
        """Test creating StandardCellEntity."""
        std_cell = entity.StandardCellEntity(**sample_standard_cell_data)
        assert std_cell.name == 'NAND2_X1'
        assert std_cell.width == 0.5
        assert std_cell.height == 2.0
        assert std_cell.no_of_input_pins == 2
        assert std_cell.no_of_output_pins == 1

    def test_standard_cell_flags(self, sample_standard_cell_data):
        """Test standard cell type flags."""
        # Regular cell
        data = sample_standard_cell_data.copy()
        std_cell = entity.StandardCellEntity(**data)
        assert std_cell.is_sequential is False
        assert std_cell.is_buffer is False
        assert std_cell.is_inverter is False

        # Sequential cell
        data['is_sequential'] = True
        seq_cell = entity.StandardCellEntity(**data)
        assert seq_cell.is_sequential is True


class TestDesignFlowEntity:  # pylint: disable=too-few-public-methods
    """Test DesignFlowEntity."""

    def test_design_flow_creation(self):
        """Test creating DesignFlowEntity."""
        flow = entity.DesignFlowEntity(
            flow_id='flow_001',
            design='test_design'
        )
        assert flow.flow_id == 'flow_001'
        assert flow.design == 'test_design'
        assert flow.stages == {}


class TestConstraintEntity:  # pylint: disable=too-few-public-methods
    """Test ConstraintEntity."""

    def test_constraint_entity_creation(self):
        """Test creating ConstraintEntity."""
        constraint = entity.ConstraintEntity(
            flow_id='flow_001',
            clock_period=10.0,
            core_utilization=0.8
        )
        assert constraint.flow_id == 'flow_001'
        assert constraint.clock_period == 10.0
        assert constraint.core_utilization == 0.8


class TestDesignStageEntity:  # pylint: disable=too-few-public-methods
    """Test DesignStageEntity."""

    def test_design_stage_creation(self):
        """Test creating DesignStageEntity."""
        stage = entity.DesignStageEntity(
            flow_id='flow_001',
            stage='floorplan'
        )
        assert stage.flow_id == 'flow_001'
        assert stage.stage == 'floorplan'
        assert stage.netlist is None


class TestPinEntity:
    """Test PinEntity."""

    def test_pin_entity_creation(self, sample_pin_data):
        """Test creating PinEntity."""
        pin = entity.PinEntity(**sample_pin_data)
        assert pin.name == 'pin_001'
        assert pin.direction == 'INPUT'
        assert pin.is_startpoint is True
        assert pin.is_endpoint is False
        assert pin.x_min == 5.0
        assert pin.y_min == 10.0

    def test_pin_entity_optional_fields(self, sample_pin_data):
        """Test PinEntity with optional timing fields."""
        data = sample_pin_data.copy()
        data['setup_rise_slew'] = 0.5
        data['setup_fall_slew'] = 0.6
        data['hold_rise_slack'] = 0.1
        data['load_capacitance'] = 0.01

        pin = entity.PinEntity(**data)
        assert pin.setup_rise_slew == 0.5
        assert pin.setup_fall_slew == 0.6
        assert pin.hold_rise_slack == 0.1
        assert pin.load_capacitance == 0.01


class TestTimingMetricsEntity:  # pylint: disable=too-few-public-methods
    """Test TimingMetricsEntity."""

    def test_timing_metrics_creation(self, sample_timing_metrics_data):
        """Test creating TimingMetricsEntity."""
        timing = entity.TimingMetricsEntity(**sample_timing_metrics_data)
        assert timing.flow_id == 'test_flow_001'
        assert timing.total_negative_slack == -10.5
        assert timing.worst_slack == -5.2
        assert timing.critical_path_startpoint == 'start_001'
        assert timing.critical_path_endpoint == 'end_001'
        assert timing.no_of_endpoints == 50
        assert timing.no_of_violating_endpoints == 5


class TestRoutabilityMetricsEntity:  # pylint: disable=too-few-public-methods
    """Test RoutabilityMetricsEntity."""

    def test_routability_metrics_creation(self, sample_routability_metrics_data):
        """Test creating RoutabilityMetricsEntity."""
        routability = entity.RoutabilityMetricsEntity(**sample_routability_metrics_data)
        assert routability.flow_id == 'test_flow_001'
        assert routability.rudy_net is None
        assert routability.rudy_pin is None


class TestNetArcEntity:
    """Test NetArcEntity."""

    def test_net_arc_creation(self, sample_net_arc_data):
        """Test creating NetArcEntity."""
        net_arc = entity.NetArcEntity(**sample_net_arc_data)
        assert net_arc.startpoint == 'start_001'
        assert net_arc.endpoint == 'end_001'
        assert net_arc.path_type == 'setup'
        assert net_arc.net_name == 'net_001'
        assert net_arc.delay == 1.5
        assert net_arc.arrival_time == 10.0
        assert net_arc.slew == 0.5

    def test_net_arc_optional_fields(self, sample_net_arc_data):
        """Test NetArcEntity with optional capacitance."""
        data = sample_net_arc_data.copy()
        data['capacitance'] = 0.02
        net_arc = entity.NetArcEntity(**data)
        assert net_arc.capacitance == 0.02


class TestCellArcEntity:  # pylint: disable=too-few-public-methods
    """Test CellArcEntity."""

    def test_cell_arc_creation(self, sample_cell_arc_data):
        """Test creating CellArcEntity."""
        cell_arc = entity.CellArcEntity(**sample_cell_arc_data)
        assert cell_arc.startpoint == 'start_001'
        assert cell_arc.endpoint == 'end_001'
        assert cell_arc.path_type == 'setup'
        assert cell_arc.gate_name == 'gate_001'
        assert cell_arc.delay == 2.0
        assert cell_arc.arrival_time == 12.0
        assert cell_arc.slew == 0.6


class TestPDNEntity:  # pylint: disable=too-few-public-methods
    """Test PDNEntity."""

    def test_pdn_creation(self, sample_pdn_data):
        """Test creating PDNEntity."""
        pdn = entity.PDNEntity(**sample_pdn_data)
        assert pdn.flow_id == 'test_flow_001'
        assert pdn.routing_vdd is None
        assert pdn.routing_vss is None
        assert pdn.ir_drop_vdd is None


class TestClockTreeEntity:
    """Test ClockTreeEntity."""

    def test_clock_tree_creation(self, sample_clock_tree_data):
        """Test creating ClockTreeEntity."""
        clock_tree = entity.ClockTreeEntity(**sample_clock_tree_data)
        assert clock_tree.flow_id == 'test_flow_001'
        assert clock_tree.clock_source == 'clk'
        assert clock_tree.no_of_clock_sinks == 100
        assert clock_tree.no_of_buffers == 10
        # ClockTreeEntity is a GraphEntity
        assert hasattr(clock_tree, '_graph')

    def test_clock_tree_graph_operations(self, sample_clock_tree_data):
        """Test ClockTreeEntity graph operations."""
        clock_tree = entity.ClockTreeEntity(**sample_clock_tree_data)

        # Add nodes (using valid NODE_TYPES)
        clock_tree.add_node('sink1', type='PIN', entity=None)
        clock_tree.add_node('sink2', type='PIN', entity=None)
        clock_tree.add_node('gate1', type='GATE', entity=None)

        # Add edges
        clock_tree.add_edge('gate1', 'sink1')
        clock_tree.add_edge('gate1', 'sink2')

        assert len(list(clock_tree.nodes)) == 3
        assert len(list(clock_tree.edges)) == 2
        assert 'sink1' in clock_tree.nodes
        assert ('gate1', 'sink1') in clock_tree.edges


class TestTimingPathEntity:
    """Test TimingPathEntity."""

    def test_timing_path_creation(self):
        """Test creating TimingPathEntity."""
        timing_path = entity.TimingPathEntity(
            flow_id='test_flow_001',
            stage='floorplan',
            startpoint='start_001',
            endpoint='end_001',
            path_type='setup',
            arrival_time=100.0,
            required_time=95.0,
            slack=-5.0,
            no_of_pins=10,
            is_critical_path=True
        )
        assert timing_path.flow_id == 'test_flow_001'
        assert timing_path.startpoint == 'start_001'
        assert timing_path.endpoint == 'end_001'
        assert timing_path.path_type == 'setup'
        assert timing_path.arrival_time == 100.0
        assert timing_path.required_time == 95.0
        assert timing_path.slack == -5.0
        assert timing_path.no_of_pins == 10
        assert timing_path.is_critical_path is True
        # TimingPathEntity is a GraphEntity
        assert hasattr(timing_path, '_graph')

    def test_timing_path_graph_operations(self):
        """Test TimingPathEntity graph operations."""
        timing_path = entity.TimingPathEntity(
            flow_id='test_flow_001',
            stage='floorplan',
            startpoint='start_001',
            endpoint='end_001',
            path_type='setup',
            arrival_time=100.0,
            required_time=95.0,
            slack=-5.0,
            no_of_pins=10,
            is_critical_path=True
        )

        # Add nodes representing path elements (using valid NODE_TYPES)
        timing_path.add_node('start_001', type='PIN', entity=None)
        timing_path.add_node('net_arc1', type='NET_ARC', entity=None)
        timing_path.add_node('end_001', type='PIN', entity=None)

        # Add edges
        timing_path.add_edge('start_001', 'net_arc1')
        timing_path.add_edge('net_arc1', 'end_001')

        assert len(list(timing_path.nodes)) == 3
        assert len(list(timing_path.edges)) == 2
