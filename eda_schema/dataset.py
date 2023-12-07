

from eda_schema import entity
from eda_schema.db import RawDB


class StandardCellData(dict):
    seq_cells = []


class Dataset(dict):
    standard_cells = None

    def __init__(self, data_dir):
        super().__init__()
        self.db = RawDB(data_dir)

    def dump_standard_cells(self):
        for std_cell in self.standard_cells.values():
            self.db.add_table_row("standard_cells", std_cell.asdict())

    def dump_netlist(self, circuit, netlist_id, phase):
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
            node_dict = {**netlist_dict, **netlist.nodes[node]["object"].asdict()}
            if netlist.nodes[node]["type"] == "PORT":
                port_data.append(node_dict)
            if netlist.nodes[node]["type"] == "GATE":
                gate_data.append(node_dict)
            if netlist.nodes[node]["type"] == "INTERCONNECT":
                net_data.append(node_dict)
                net = netlist.nodes[node]["object"]
                net_key = f"{netlist_key_str}-{net.name}"
                if phase == "route":
                    self.db.add_graph_data("nets", net, net_key)
                for net_segment in net.nodes:
                    net_segment_data.append({
                        **netlist_dict,
                        "net_name": net.name,
                        "name": net_segment,
                        **net.nodes[net_segment]["object"].asdict()
                    })

        self.db.add_table_data("ports", port_data)
        self.db.add_table_data("gates", gate_data)
        self.db.add_table_data("nets", net_data)
        self.db.add_table_data("net_segments", net_segment_data)

        timing_path_data = []
        timing_point_data = []
        for timing_path in netlist.timing_paths.values():
            timing_path_key = f"{netlist_key_str}-{timing_path.startpoint}-{timing_path.endpoint}-{timing_path.path_type}"
            self.db.add_graph_data("timing_paths", timing_path, timing_path_key)
            timing_path_data.append({**netlist_dict, **timing_path.asdict()})
            for timing_point in timing_path.nodes:
                timing_point_data.append({
                    **netlist_dict,
                    "startpoint": timing_path.startpoint,
                    "endpoint": timing_path.endpoint,
                    **timing_path.nodes[timing_point]["object"].asdict(),
                })

        self.db.add_table_data("timing_paths", timing_path_data)
        self.db.add_table_data("timing_points", timing_point_data)

        clock_tree_data = []
        for clock_source, clock_tree in netlist.clock_trees.items():
            clock_tree_key = f"{netlist_key_str}-{clock_source}"
            self.db.add_graph_data("clock_trees", clock_tree, clock_tree_key)
            clock_tree_data.append({**netlist_dict, **clock_tree.asdict()})
        self.db.add_table_data("clock_trees", clock_tree_data)

    def dump_dataset(self):
        self.db.create_dataset_tables()
        self.dump_standard_cells()

        for netlist_key in self:
            self.dump_netlist(self, *netlist_key)

    def load_dataset(self):
        for _, data in self.db.get_table_data("netlists").iterrows():
            data_dict = data.to_dict()
            key = {k: data_dict.pop(k) for k in entity.KEY_COLUMNS}

            netlist_entity = entity.NetlistEntity(data_dict)

            cell_metrics_data = self.db.get_table_row("cell_metrics", **key).to_dict()
            netlist_entity.cell_metrics = entity.CellMetricsEntity(cell_metrics_data)

            area_metrics_data = self.db.get_table_row("area_metrics", **key).to_dict()
            netlist_entity.area_metrics = entity.AreaMetricsEntity(area_metrics_data)

            power_metrics_data = self.db.get_table_row("power_metrics", **key).to_dict()
            netlist_entity.power_metrics = entity.PowerMetricsEntity(power_metrics_data)

            port_df = self.db.get_table_data("ports", **key)
            port_dict = port_df.set_index("name").to_dict('index')

            gate_df = self.db.get_table_data("gates", **key)
            gate_dict = gate_df.set_index("name").to_dict('index')

            net_df = self.db.get_table_data("nets", **key)
            net_dict = net_df.set_index("name").to_dict('index')

            netlist_key_str = "-".join(key.values())
            netlist_graph = self.db.get_graph_data("netlists", netlist_key_str)
            for node, node_type in zip(netlist_graph["nodes"], netlist_graph["node_types"]):
                if node_type == "PORT":
                    port_entity = entity.IOPortEntity(port_dict[node])
                    info_dict = {"type": "PORT", "object": port_entity}

                if node_type == "GATE":
                    gate_entity = entity.GateEntity(gate_dict[node])
                    info_dict = {"type": "GATE", "object": gate_entity}

                if node_type == "INTERCONNECT":
                    interconnect_entity = entity.InterconnectEntity(net_dict[node])
                    info_dict = {"type": "INTERCONNECT", "object": interconnect_entity}

                netlist_entity.add_node(node, **info_dict)

            for edge in netlist_graph["edges"]:
                netlist_entity.add_edge(*edge)

            critical_path_metrics_data = self.db.get_table_row("critical_path_metrics", **key).to_dict()
            netlist_entity.critical_path_metrics = entity.CriticalPathMetricsEntity(critical_path_metrics_data)

            self[tuple(key.values())] = netlist_entity
