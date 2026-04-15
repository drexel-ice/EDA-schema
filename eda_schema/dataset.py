import dill
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

from eda_schema import entity
from eda_schema.db.base import BaseDB


class StandardCellData(dict[str, entity.StandardCellEntity]):
    """
    Container for standard-cell library data.

    Acts as:
        cell_name -> StandardCellEntity

    and tracks a per-instance list of sequential cell names.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize StandardCellData container.

        Args:
            *args: Positional arguments passed to dict.__init__.
            **kwargs: Keyword arguments passed to dict.__init__.
        """
        super().__init__(*args, **kwargs)
        self.seq_cells: list[str] = []

    def add_cell(self, std_cell: entity.StandardCellEntity) -> None:
        """
        Insert a standard cell and update sequential tracking.

        Args:
            std_cell: Standard cell entity to add.
        """
        self[std_cell.name] = std_cell
        if getattr(std_cell, "is_sequential", False):
            self.seq_cells.append(std_cell.name)


class Dataset(dict):
    """
    Dictionary class representing an EDA dataset.

    Attributes:
        standard_cells (dict): Dictionary to store standard cell data.
        db (FileDB): File-based database for storing EDA-related data.
    """
    standard_cells = {}

    def __init__(self, db_obj: BaseDB) -> None:
        """
        Initialize a Dataset tied to a database backend.

        Args:
            db_obj (FileDB): Database interface used for persistence.
        """
        super().__init__()
        self.db: BaseDB = db_obj
        self.standard_cells: StandardCellData = StandardCellData()

    def save_to_pickle(self, filepath: str | Path) -> None:
        """
        Serialize the Dataset object to a pickle file.

        Args:
            filepath (str | Path): Destination pickle file path.
        """
        temp = self.db
        self.db = None
        with open(filepath, "wb") as f:
            dill.dump(self, f)
        self.db = temp


    @classmethod
    def load_from_pickle(cls, filepath: str | Path, db_obj: BaseDB) -> "Dataset":
        """
        Load a Dataset instance from a pickle file and reattach the DB backend.

        Args:
            filepath (str | Path): Path to the pickle file.
            db_obj (BaseDB): Database object to reattach.

        Returns:
            Dataset: A ready-to-use dataset instance.
        """
        with open(filepath, "rb") as f:
            loaded = dill.load(f)
        loaded.db = db_obj
        return loaded

    def dump_standard_cells(self):
        """
        Dump standard cell data into the database.

        Writes all standard cells from self.standard_cells to the database.
        """
        for std_cell in self.standard_cells.values():
            self.db.add_table_row("standard_cells", std_cell.get_tabular_data())

    def dump(self) -> None:
        """
        Create all database tables and serialize the entire dataset hierarchy.
        """
        # Create empty parquet tables for all entities
        self.db.create_dataset_tables()

        # Dump standard-cell definitions first (independent of flows)
        self.dump_standard_cells()

        # Snapshot keys so iteration is safe even if dict mutates
        flow_ids = list(self.keys())

        if not flow_ids:
            raise ValueError("Dataset.dump_dataset() called but dataset contains no flows.")

        # Dump each flow entry
        for flow_id in flow_ids:
            if self[flow_id] is None:
                raise ValueError(f"Dataset contains empty design flow entry: '{flow_id}'")
            self.dump_design_flow(flow_id)

    def dump_design_flow(self, flow_id: str) -> None:
        """
        Persist a complete design flow and all its stages.

        Args:
            flow_id (str): Flow identifier stored in this dataset.
        """
        design_flow = self[flow_id]

        self.db.add_table_row("design_flows", design_flow.get_tabular_data())
        self.db.add_table_row("constraints", design_flow.constraints.get_tabular_data())

        for stage_enum in entity.DesignStages:
            stage = stage_enum.value
            self.dump_design_stage(design_flow.stages[stage], flow_id, stage)

    def dump_design_stage(self, design_stage: entity.DesignStageEntity,
                     flow_id: str, stage: str) -> None:
        """
        Persist a design-stage and associated netlist and all metrics.

        Args:
            design_stage (DesignStageEntity): Stage containing netlist + metrics.
            flow_id (str): Flow identifier.
            stage (str): Stage name.
        """
        self.db.add_table_row("design_stages", design_stage.get_tabular_data())

        netlist = design_stage.netlist
        if netlist is None:
            return
        # Persist stage-level metadata + metrics tables
        self.db.add_table_row("netlists", netlist.get_tabular_data())
        self.db.add_table_row("cell_metrics", design_stage.cell_metrics.get_tabular_data())
        self.db.add_table_row("area_metrics", design_stage.area_metrics.get_tabular_data())
        self.db.add_table_row("power_metrics", design_stage.power_metrics.get_tabular_data())
        self.db.add_table_row("routability_metrics", design_stage.routability_metrics.get_tabular_data())
        self.db.add_table_row("timing_metrics", design_stage.timing_metrics.get_tabular_data())

        self.db.add_entity_images("routability_metrics", design_stage.routability_metrics)

        # Dump netlist graph
        self.db.add_graph_data("netlists", netlist.get_graph_data(), flow_id=flow_id, stage=stage)
        self.db.add_entity_images("netlists", netlist)

        # Dump node entities (PORT / GATE / PIN / NET)
        port_data, gate_data, pin_data, net_data, metal_segment_data = [], [], [], [], []
        for node in netlist.nodes:
            node_entity = netlist.nodes[node]["entity"]
            node_type = netlist.nodes[node]["type"]
            if node_type == "PORT":
                port_data.append(node_entity.get_tabular_data())
            elif node_type == "GATE":
                gate_data.append(node_entity.get_tabular_data())
            elif node_type == "PIN":
                pin_data.append(node_entity.get_tabular_data())
            elif node_type == "NET":
                net_data.append(node_entity.get_tabular_data())
                net = netlist.nodes[node]["entity"]
                # for metal_segment in net.nodes:
                #     metal_segment_data.append(net.nodes[metal_segment]["entity"].get_tabular_data())
                # self.db.add_graph_data("nets", net.get_graph_data(), flow_id=flow_id, stage=stage, name=net.name)
                # self.db.add_entity_images("nets", node_entity)

        self.db.add_table_data("ports", port_data)
        self.db.add_table_data("gates", gate_data)
        self.db.add_table_data("pins", pin_data)
        self.db.add_table_data("nets", net_data)
        # if metal_segment_data:
        #     self.db.add_table_data("metal_segments", metal_segment_data)

        # Dump timing paths + their graphs
        timing_path_data = []
        net_arc_data = []
        cell_arc_data = []
        timing_path_graphs = []

        for timing_path in netlist.timing_paths.values():
            timing_path_data.append(timing_path.get_tabular_data())
            for node in timing_path.nodes:
                tp_node_entity = timing_path.nodes[node]["entity"]
                tp_node_type = timing_path.nodes[node]["type"]
                if tp_node_type == "NET_ARC":
                    net_arc_data.append(tp_node_entity.get_tabular_data())
                elif tp_node_type == "CELL_ARC":
                    cell_arc_data.append(tp_node_entity.get_tabular_data())
            timing_path_graphs.append({
                "data": timing_path.get_graph_data(),
                "flow_id": flow_id,
                "stage": stage,
                "startpoint": timing_path.startpoint,
                "endpoint": timing_path.endpoint,
                "path_type": timing_path.path_type,
            })


        self.db.add_table_data("net_arcs", net_arc_data)
        self.db.add_table_data("cell_arcs", cell_arc_data)
        self.db.add_table_data("timing_paths", timing_path_data)
        self.db.add_graph_data_batch("timing_paths", timing_path_graphs)

        # Dump clock trees
        clock_tree_data = []
        for clock_source, clock_tree in netlist.clock_trees.items():
            clock_tree_data.append(clock_tree.get_tabular_data())
            self.db.add_graph_data(
                "clock_trees",
                clock_tree.get_graph_data(),
                flow_id=flow_id,
                stage=stage,
                clock_source=clock_source,
            )
            self.db.add_entity_images("clock_trees", clock_tree)
        self.db.add_table_data("clock_trees", clock_tree_data)

        # Dump power delivery network
        self.db.add_entity_images("power_delivery_networks", netlist.power_delivery_network)
        self.db.add_table_row("power_delivery_networks", netlist.power_delivery_network.get_tabular_data())

    def load_standard_cells(self) -> None:
        """
        Load all standard-cell rows from the database.
        """
        df = self.db.get_table_data("standard_cells")
        for _, row in df.iterrows():
            cell = entity.StandardCellEntity(**row.to_dict())
            self.standard_cells[cell.name] = cell
            if cell.is_sequential:
                self.standard_cells.seq_cells.append(cell.name)

    def load(self, flow_id: str | None = None, stage: str | None = None) -> None:
        """
        Load the complete dataset—or a filtered subset—from the database.

        Args:
            flow_id (str | None): If provided, load only this flow.
            stage (str | None): If provided, restrict loading to this stage.
                When provided, `flow_id` must also be supplied.

        Returns:
            None. The Dataset instance is populated in-place.
        """
        # Load standard-cell library
        self.load_standard_cells()

        # Determine which flows to load
        if flow_id is not None:
            flow_ids = [flow_id]
        else:
            df_flows = self.db.get_table_data("design_flows")
            flow_ids = list(df_flows["flow_id"])

        # Fully load each design flow
        for _flow_id in flow_ids:
            design_flow = self.load_design_flow(_flow_id, stage)
            self[_flow_id] = design_flow

    def load_design_flow(self, flow_id: str, stage: str | None = None) -> entity.DesignFlowEntity:
        """
        Load a full design flow (or a specific stage of it).

        Args:
            flow_id (str): Flow identifier.
            stage (str | None): Limit reconstruction to this stage only.

        Returns:
            DesignFlowEntity: Fully reconstructed design-flow object.
        """
        design_flow_entity = self.db.get_entity("design_flows", flow_id=flow_id)
        for stage_enum in entity.DesignStages:
            _stage = stage_enum.value
            if stage and stage!=_stage:
                continue
            design_flow_entity.stages[_stage] = self.load_design_stage(flow_id=flow_id, stage=_stage)
        return design_flow_entity

    def load_design_stage(self, flow_id: str, stage: str) -> entity.DesignStageEntity:
        """
        Load a design stage including netlist + all metric entities.

        Args:
            flow_id (str): Flow identifier.
            stage (str): Stage name.

        Returns:
            DesignStageEntity: The reconstructed stage entity.
        """
        design_stage_entity = self.db.get_entity("design_stages", flow_id=flow_id, stage=stage)
        design_stage_entity.netlist = self.load_netlist(flow_id=flow_id, stage=stage)
        design_stage_entity.cell_metrics = self.db.get_entity("cell_metrics", flow_id=flow_id, stage=stage)
        design_stage_entity.area_metrics = self.db.get_entity("area_metrics", flow_id=flow_id, stage=stage)

        # Load power metrics and apply migration (Watts -> μW) if needed
        power_metrics = self.db.get_entity("power_metrics", flow_id=flow_id, stage=stage)
        if power_metrics:
            # Migration: Convert from Watts to μW if values are in old format (< 1.0)
            # New parser outputs values in μW (typically > 100), old database has Watts (< 1.0)
            if power_metrics.total_power is not None and power_metrics.total_power < 1.0:
                # Convert all power values from Watts to μW (multiply by 1e6) and round
                power_metrics.total_power = round(power_metrics.total_power * 1e6, 6)
                if power_metrics.combinational_power is not None:
                    power_metrics.combinational_power = round(power_metrics.combinational_power * 1e6, 6)
                if power_metrics.sequential_power is not None:
                    power_metrics.sequential_power = round(power_metrics.sequential_power * 1e6, 6)
                if power_metrics.macro_power is not None:
                    power_metrics.macro_power = round(power_metrics.macro_power * 1e6, 6)
                if power_metrics.internal_power is not None:
                    power_metrics.internal_power = round(power_metrics.internal_power * 1e6, 6)
                if power_metrics.switching_power is not None:
                    power_metrics.switching_power = round(power_metrics.switching_power * 1e6, 6)
                if power_metrics.leakage_power is not None:
                    power_metrics.leakage_power = round(power_metrics.leakage_power * 1e6, 6)
        design_stage_entity.power_metrics = power_metrics

        design_stage_entity.routability_metrics = self.db.get_entity("routability_metrics", flow_id=flow_id, stage=stage)
        design_stage_entity.timing_metrics = self.db.get_entity("timing_metrics", flow_id=flow_id, stage=stage)
        return design_stage_entity

    def load_netlist(self, flow_id: str, stage: str) -> entity.NetlistEntity:
        """
        Load a NetlistEntity and rebuild all node entities,
        timing paths, arcs, and clock trees.

        Args:
            flow_id (str): Flow identifier.
            stage (str): Stage name.

        Returns:
            NetlistEntity: Fully reconstructed netlist entity.
        """
        netlist_entity = self.db.get_entity("netlists", load_sub_entities=False, flow_id=flow_id, stage=stage)

        port_df = self.db.get_table_data("ports", flow_id=flow_id, stage=stage)
        port_dict = port_df.set_index("name").to_dict('index')
        pin_df = self.db.get_table_data("pins", flow_id=flow_id, stage=stage)
        pin_dict = pin_df.set_index("name").to_dict('index')
        gate_df = self.db.get_table_data("gates", flow_id=flow_id, stage=stage)
        gate_dict = gate_df.set_index("name").to_dict('index')
        net_df = self.db.get_table_data("nets", flow_id=flow_id, stage=stage)
        net_dict = net_df.set_index("name").to_dict('index')

        for node in netlist_entity.nodes:
            node_type = netlist_entity.nodes[node]["type"]
            if node_type == "PORT":
                netlist_entity.nodes[node]["entity"] = entity.PortEntity(name=node, **port_dict[node])
            elif node_type == "PIN":
                netlist_entity.nodes[node]["entity"] = entity.PinEntity(name=node, **pin_dict[node])
            elif node_type == "GATE":
                netlist_entity.nodes[node]["entity"] = entity.GateEntity(name=node, **gate_dict[node])
            elif node_type == "NET":
                netlist_entity.nodes[node]["entity"] = entity.NetEntity(name=node, **net_dict[node])

        netlist_entity.timing_paths = self.load_timing_paths(flow_id, stage, netlist_entity)
        netlist_entity.clock_trees = self.load_clock_trees(flow_id, stage, netlist_entity)
        netlist_entity.power_delivery_network = self.db.get_entity("power_delivery_networks", flow_id=flow_id, stage=stage)

        return netlist_entity

    def load_timing_paths(self, flow_id: str, stage: str, netlist_entity: entity.NetlistEntity,) -> Dict[Tuple[str, str, str], entity.TimingPathEntity]:
        """
        Load and reconstruct all timing paths for a given flow and stage.

        Args:
            flow_id (str): Flow identifier.
            stage (str): Stage name.
            netlist_entity (NetlistEntity): The already-loaded netlist whose
                PORT, PIN, GATE, and NET entities will be referenced when
                binding timing-path node entities.

        Returns:
            dict[tuple[str, str, str], TimingPathEntity]:
                Mapping (startpoint, endpoint, path_type) → TimingPathEntity.
        """
        net_arc_df = self.db.get_table_data("net_arcs", flow_id=flow_id, stage=stage)
        net_arc_dict = {}
        for _, row in net_arc_df.iterrows():
            row_dict = row.to_dict()
            key = (row.startpoint, row.endpoint, row.path_type, row.net_name)
            net_arc_dict[key] = row_dict

        cell_arc_df = self.db.get_table_data("cell_arcs", flow_id=flow_id, stage=stage)
        cell_arc_dict = {}
        for _, row in cell_arc_df.iterrows():
            row_dict = row.to_dict()
            key = (row.startpoint, row.endpoint, row.path_type, row.gate_name)
            cell_arc_dict[key] = row_dict

        timing_paths = {}
        df = self.db.get_table_data("timing_paths", flow_id=flow_id, stage=stage)
        for row in df.itertuples(index=False):
            timing_path_entity = self.db.get_entity(
                "timing_paths",
                flow_id=flow_id,
                stage=stage,
                startpoint=row.startpoint,
                endpoint=row.endpoint,
                path_type=row.path_type,
                load_sub_entities=True,
            )

            for node in timing_path_entity.nodes:
                node_type = timing_path_entity.nodes[node]["type"]
                if node_type == "PORT":
                    timing_path_entity.nodes[node]["entity"] = netlist_entity.nodes[node]["entity"]
                elif node_type == "PIN":
                    timing_path_entity.nodes[node]["entity"] = netlist_entity.nodes[node]["entity"]
                elif node_type == "NET_ARC":
                    arc_key = (row.startpoint, row.endpoint, row.path_type, node)
                    if arc_key in net_arc_dict:
                        timing_path_entity.nodes[node]["entity"] = entity.NetArcEntity(**net_arc_dict[arc_key])
                elif node_type == "CELL_ARC":
                    arc_key = (row.startpoint, row.endpoint, row.path_type, node)
                    if arc_key in cell_arc_dict:
                        timing_path_entity.nodes[node]["entity"] = entity.CellArcEntity(**cell_arc_dict[arc_key])

            timing_paths[(row.startpoint, row.endpoint, row.path_type)] = timing_path_entity

        return timing_paths

    def load_clock_trees(self, flow_id: str, stage: str, netlist_entity: entity.NetlistEntity) -> dict[str, entity.ClockTreeEntity]:
        """
        Load and reconstruct all clock trees for the given design stage.

        Args:
            flow_id (str): Flow identifier.
            stage (str): Stage name.
            netlist_entity (NetlistEntity): The pre-loaded netlist whose
                PORT, PIN, GATE, and NET entities should be referenced
                when rebuilding the clock-tree graphs.

        Returns:
            dict[str, ClockTreeEntity]: Mapping of clock_source → reconstructed ClockTreeEntity.
        """
        clock_tree_entities = {}
        df = self.db.get_table_data("clock_trees", flow_id=flow_id, stage=stage)
        for row in df.itertuples(index=False):
            clock_tree_entity = self.db.get_entity("clock_trees", load_sub_entities=True, flow_id=flow_id, stage=stage, clock_source=row.clock_source)
            for node in clock_tree_entity.nodes:
                node_type = clock_tree_entity.nodes[node]["type"]
                clock_tree_entity.nodes[node]["entity"] = netlist_entity.nodes[node]["entity"]

            clock_tree_entities[row.clock_source] = clock_tree_entity

        return clock_tree_entities
