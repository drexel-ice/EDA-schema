import dill
from eda_schema import entity


class StandardCellData(dict):
    """
    Dictionary class for storing standard cell data.

    Attributes:
        seq_cells (list): List of sequential cells.
    """
    seq_cells = []


class Dataset(dict):
    """
    Dictionary class representing an EDA dataset.

    Attributes:
        standard_cells (dict): Dictionary to store standard cell data.
        db (FileDB): File-based database for storing EDA-related data.
    """
    standard_cells = {}

    def __init__(self, db_obj):
        """
        Initialize the Dataset object.

        Args:
            db_obj (FileDB): File-based database for storing EDA-related data.
        """
        super().__init__()
        self.db = db_obj

    def save_to_pickle(self, filepath):
        """
        Saves the Dataset object to a pickle file.
        """
        _temp_db = self.db
        self.db = None
        with open(filepath, 'wb') as f:
            dill.dump(self, f)
        self.db = _temp_db

    def load_from_pickle(self, filepath):
        """
        Loads the Dataset object directly into the current instance.
        """
        with open(filepath, 'rb') as f:
            loaded_obj = dill.load(f)
        loaded_obj.db = self.db
        return loaded_obj

    def dump_standard_cells(self):
        """Dump standard cell data into the database."""
        for std_cell in self.standard_cells.values():
            self.db.add_table_row("standard_cells", std_cell.asdict())

    def dump_netlist(self, circuit, netlist_id, phase):
        """
        Dump netlist data into the database.

        Args:
            circuit (str): Circuit name.
            netlist_id (str): Netlist ID.
            phase (str): Circuit design phase.
        """
        netlist_key = (circuit, netlist_id, phase)
        netlist = self[netlist_key]
        netlist_key_str = "-".join(netlist_key)
        netlist_dict = dict(zip(entity.KEY_COLUMNS, netlist_key))
        self.db.add_graph_data("netlists", netlist, netlist_key_str)

        self.db.add_table_row("netlists", {**netlist_dict, **netlist.asdict()})
        self.db.add_table_row("cell_metrics", {**netlist_dict, **netlist.cell_metrics.asdict()})
        self.db.add_table_row("area_metrics", {**netlist_dict, **netlist.area_metrics.asdict()})
        self.db.add_table_row("power_metrics", {**netlist_dict, **netlist.power_metrics.asdict()})
        self.db.add_table_row(
            "critical_path_metrics",
            {**netlist_dict, **netlist.critical_path_metrics.asdict()}
        )

        port_data, gate_data, net_data, net_segment_data = [], [], [], []
        for node in netlist.nodes:
            node_dict = {**netlist_dict, **netlist.nodes[node]["entity"].asdict()}
            if netlist.nodes[node]["type"] == "PORT":
                port_data.append(node_dict)
            if netlist.nodes[node]["type"] == "GATE":
                gate_data.append(node_dict)
            if netlist.nodes[node]["type"] == "INTERCONNECT":
                net_data.append(node_dict)
                net = netlist.nodes[node]["entity"]
                net_key = f"{netlist_key_str}-{net.name}"
                if phase == "route":
                    self.db.add_graph_data("nets", net, net_key)
                for net_segment in net.nodes:
                    net_segment_data.append({
                        **netlist_dict,
                        "net_name": net.name,
                        "name": net_segment,
                        **net.nodes[net_segment]["entity"].asdict()
                    })

        self.db.add_table_data("ports", port_data)
        self.db.add_table_data("gates", gate_data)
        self.db.add_table_data("nets", net_data)
        if net_segment_data:
            self.db.add_table_data("net_segments", net_segment_data)

        timing_path_dict = []
        timing_point_data = []
        for timing_path_list in netlist.timing_paths.values():
            for timing_path in timing_path_list:
                timing_path_key = f"{netlist_key_str}-{timing_path.startpoint}-{timing_path.endpoint}-{timing_path.path_type}-{timing_path.sort_index}"
                self.db.add_graph_data("timing_paths", timing_path, timing_path_key)
                timing_path_dict.append({**netlist_dict, **timing_path.asdict()})
                for timing_point in timing_path.nodes:
                    timing_point_data.append({
                        **netlist_dict,
                        "startpoint": timing_path.startpoint,
                        "endpoint": timing_path.endpoint,
                        "path_type": timing_path.path_type,
                        "sort_index": timing_path.sort_index,
                        **timing_path.nodes[timing_point]["entity"].asdict(),
                    })

        self.db.add_table_data("timing_paths", timing_path_dict)
        self.db.add_table_data("timing_points", timing_point_data)

        clock_tree_data = []
        for clock_source, clock_tree in netlist.clock_trees.items():
            clock_tree_key = f"{netlist_key_str}-{clock_source}"
            self.db.add_graph_data("clock_trees", clock_tree, clock_tree_key)
            clock_tree_data.append({**netlist_dict, **clock_tree.asdict()})
        self.db.add_table_data("clock_trees", clock_tree_data)

    def dump_dataset(self):
        """Dump the entire dataset into the database."""
        self.db.create_dataset_tables()
        self.dump_standard_cells()

        for netlist_key in self:
            self.dump_netlist(self, *netlist_key)

    def load_standard_cells(self):
        for _, data in self.db.get_table_data("standard_cells").iterrows():
            standard_cell_entity = entity.StandardCellEntity(data.to_dict())
            self.standard_cells[standard_cell_entity.name] = standard_cell_entity


    def load_dataset(self):
        """Load the dataset from the database."""
        for _, data in self.db.get_table_data("netlists").iterrows():
            netlist_data = data.to_dict()
            key = {k: netlist_data.pop(k) for k in entity.KEY_COLUMNS}
            netlist_entity = self.load_netlist(key, netlist_data)

            self[tuple(key.values())] = netlist_entity

    def load_netlist(self, key, netlist_data=None, timing_path_sort_index=0, validate=True):
        netlist_data = netlist_data or self.db.get_table_row("netlists", **key).to_dict()
        netlist_entity = entity.NetlistEntity(netlist_data, validate=validate)

        cell_metrics_data = self.db.get_table_row("cell_metrics", **key).to_dict()
        netlist_entity.cell_metrics = entity.CellMetricsEntity(cell_metrics_data, validate=validate)

        area_metrics_data = self.db.get_table_row("area_metrics", **key).to_dict()
        netlist_entity.area_metrics = entity.AreaMetricsEntity(area_metrics_data, validate=validate)

        power_metrics_data = self.db.get_table_row("power_metrics", **key).to_dict()
        netlist_entity.power_metrics = entity.PowerMetricsEntity(power_metrics_data, validate=validate)

        port_df = self.db.get_table_data("ports", **key)
        port_dict = port_df.set_index("name").to_dict('index')

        gate_df = self.db.get_table_data("gates", **key)
        gate_dict = gate_df.set_index("name").to_dict('index')

        net_df = self.db.get_table_data("nets", **key)
        net_dict = net_df.set_index("name").to_dict('index')

        net_segment_df = None
        if key["phase"] != "floorplan":
            net_segment_df = self.db.get_table_data("net_segments", **key)

        netlist_key_str = "-".join(key.values())
        netlist_graph = self.db.get_graph_data("netlists", netlist_key_str)
        for node, node_type in zip(netlist_graph["nodes"], netlist_graph["node_types"]):
            if node_type == "PORT":
                port_entity = entity.IOPortEntity({"name": node, **port_dict[node]}, validate=validate)
                info_dict = {"type": "PORT", "entity": port_entity}

            if node_type == "GATE":
                gate_entity = entity.GateEntity({"name": node, **gate_dict[node]}, validate=validate)
                info_dict = {"type": "GATE", "entity": gate_entity}

            if node_type == "INTERCONNECT":
                net_key ={**key, "name": node}
                if key["phase"] != "floorplan":
                    net_segment_dict = net_segment_df[net_segment_df.net_name==node].set_index("name").to_dict('index')
                    interconnect_entity = self.load_interconnect(net_key, net_dict[node], net_segment_dict, validate=validate)
                else:
                    interconnect_entity = self.load_interconnect(net_key, net_dict[node], None, validate=validate)
                info_dict = {"type": "INTERCONNECT", "entity": interconnect_entity}

            netlist_entity.add_node(node, **info_dict)

        for edge in netlist_graph["edges"]:
            netlist_entity.add_edge(*edge)

        critical_path_metrics_data = self.db.get_table_row("critical_path_metrics", **key).to_dict()
        netlist_entity.critical_path_metrics = entity.CriticalPathMetricsEntity(critical_path_metrics_data, validate=validate)

        timing_path_df = self.db.get_table_data("timing_paths", **key, path_type="max", sort_index=timing_path_sort_index)
        timing_point_df = self.db.get_table_data("timing_points", **key, path_type="max", sort_index=timing_path_sort_index)
        timing_point_df["index_col"] = timing_point_df["startpoint"] + timing_point_df["endpoint"] + timing_point_df["path_type"] + timing_point_df["sort_index"].apply(str) + timing_point_df["name"]
        timing_point_dict = timing_point_df.set_index("index_col").to_dict('index')

        for _, timing_path_data in timing_path_df.iterrows():
            timing_path_key ={
                **key,
                "startpoint": timing_path_data["startpoint"],
                "endpoint": timing_path_data["endpoint"],
                "path_type": timing_path_data["path_type"],
                "sort_index": timing_path_sort_index,
            }
            timing_path_entity = self.load_timing_path(timing_path_key, timing_path_data, timing_point_df, timing_point_dict, validate=validate)
            netlist_entity.timing_paths[(timing_path_data["startpoint"], timing_path_data["endpoint"], timing_path_data["path_type"])] = timing_path_entity

        return netlist_entity

    def load_timing_path(self, timing_path_key, _timing_path_data=None, _timing_point_df=None, _timing_point_dict=None, validate=True):
        if _timing_path_data is None:
            _timing_path_data = self.db.get_table_row("timing_paths", **timing_path_key)
        if _timing_point_dict is None:
            if _timing_point_df is None:
                _timing_point_df = self.db.get_table_data("timing_points", **timing_path_key)
            _timing_point_df["index_col"] = _timing_point_df["startpoint"] + _timing_point_df["endpoint"] + _timing_point_df["path_type"] + _timing_point_df["sort_index"].apply(str) + _timing_point_df["name"]
            _timing_point_dict = _timing_point_df.set_index("index_col").to_dict('index')

        timing_path_entity = entity.TimingPathEntity(_timing_path_data.to_dict(), validate=validate)
        timing_path_key_str =  "-".join([str(x) for x in timing_path_key.values()])

        timing_path_graph = self.db.get_graph_data("timing_paths", timing_path_key_str)
        for timing_point in timing_path_graph["nodes"]:
            timing_point_entity = entity.TimingPointEntity(_timing_point_dict[_timing_path_data["startpoint"] + _timing_path_data["endpoint"] + _timing_path_data["path_type"] + str(_timing_path_data["sort_index"]) + timing_point], validate=validate)
            info_dict = {"type": "TIMINGPOINT", "entity": timing_point_entity}
            timing_path_entity.add_node(timing_point, **info_dict)

        for edge in timing_path_graph["edges"]:
            timing_path_entity.add_edge(*edge)

        return timing_path_entity

    def load_interconnect(self, net_key, _net_data=None, _net_segment_dict=None, validate=True):
        if _net_data is None:
            _net_data = self.db.get_table_row("nets", **net_key).to_dict()
        if net_key["phase"] != "floorplan" and _net_segment_dict is None:
            net_segment_key = dict(net_key)
            net_segment_key["net_name"] = net_segment_key.pop("name")
            net_segment_df = self.db.get_table_data("net_segments", **net_segment_key)
            _net_segment_dict = net_segment_df.set_index("name").to_dict('index')

        interconnect_entity = entity.InterconnectEntity(_net_data, validate=validate)
        net_key_str =  "-".join(net_key.values())

        if net_key["phase"] == "route":
            net_graph = self.db.get_graph_data("nets", net_key_str)
            for net_segment in net_graph["nodes"]:
                net_segment_entity = entity.InterconnectSegmentEntity({"name": net_segment, **_net_segment_dict[net_segment]}, validate=validate)
                info_dict = {"type": "NETSEGMENT", "entity": net_segment_entity}
                interconnect_entity.add_node(net_segment, **info_dict)

            for edge in net_graph["edges"]:
                interconnect_entity.add_edge(*edge)

        return interconnect_entity
