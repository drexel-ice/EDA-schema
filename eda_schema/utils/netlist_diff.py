import pandas as pd


class NetlistCellMapper(dict):
    def __init__(self, netlist):
        """
        Extracts node information from a netlist and returns a dictionary of nodes mapped to their
        cell types.
        """
        for node, node_info in netlist.nodes.items():
            if node_info.get("type") == "GATE":
                self[node] = node_info["entity"].standard_cell.split("__")[-1]

    def cell_is_delay(self, cell):
        cell_type = self[cell]
        return any(keyword in cell_type for keyword in ["buf", "dly"])

    def cell_is_filler(self, cell):
        return "fill" in self[cell]

    def cell_is_tapcell(self, cell):
        return "tapvpwrvgnd" in self[cell]

    def cell_is_antenna(self, cell):
        return "diode" in self[cell]

    @staticmethod
    def cell_is_cloned(cell):
        return "clone" in cell

    def cell_is_constant_logic(self, cell):
        return "conb" in self[cell]

    def strip_sizing_info(self, cell):
        return self[cell].split("_")[0].replace("clk", "").replace("lp", "")

    def is_non_functional_cell(self, cell):
        return self.cell_is_filler(cell) or self.cell_is_tapcell(cell) or self.cell_is_antenna(cell)


def compare_netlists_by_cells(phase1_netlist, phase2_netlist):
    """
    Compares two netlists and categorizes nodes into matching, resized, buffered, filler, or
    remaining categories.

    Args:
        phase1_netlist (eda_schema.entity.NetlistEntity): The netlist of the first phase.
        phase2_netlist (eda_schema.entity.NetlistEntity): The netlist of the second phase.

    Returns:
        tuple:
            - phase1_df (DataFrame): DataFrame containing the removed cells in phase 1.
            - phase2_df (DataFrame): DataFrame containing the new or modified cells in phase 2.
            - result_summary (dict): Summary dictionary of categorized changes.
    """
    # Extract node data from both netlists
    phase1_cells = NetlistCellMapper(phase1_netlist)
    phase2_cells = NetlistCellMapper(phase2_netlist)

    result_summary = {
        "init_stage_count": len([c for c in phase1_cells if not phase1_cells.is_non_functional_cell(c)]),
        "final_stage_count": len([c for c in phase2_cells if not phase2_cells.is_non_functional_cell(c)]),
    }

    data = []
    for cell, phase2_cell_data in phase2_cells.items():
        if phase2_cells.is_non_functional_cell(cell):
            continue
        row = {
            "cell": cell,
            # Cells is both phase 1 and phase 2
            "names_match": False,
            "names_match_stdcell_match": False,
            "names_match_stdcell_not_match": False,
            "names_match_stdcell_not_match_resized": False,
            "names_match_stdcell_not_match_delay": False,
            "names_match_stdcell_not_match_remaining": False,
            # Cells is phase 2 but not in phase 1
            "names_not_match": False,
            "names_not_match_clone": False,
            "names_not_match_buffered": False,
            "names_not_match_constant_logic": False,
            "names_not_match_remaining": False,
        }

        phase1_cell_data = phase1_cells.get(cell)
        if phase1_cell_data:
            row["names_match"] = True
            if phase1_cell_data == phase2_cell_data:
                row["names_match_stdcell_match"] = True
            else:
                row["names_match_stdcell_not_match"] = True
                if phase1_cells.strip_sizing_info(cell) == phase2_cells.strip_sizing_info(cell):
                    row["names_match_stdcell_not_match_resized"] = True
                elif phase1_cells.cell_is_delay(cell) and phase2_cells.cell_is_delay(cell):
                    row["names_match_stdcell_not_match_resized"] = True
                    row["names_match_stdcell_not_match_delay"] = True
                else:
                    row["names_match_stdcell_not_match_remaining"] = True
        else:
            row["names_not_match"] = True
            if phase2_cells.cell_is_cloned(cell):
                row["names_not_match_clone"] = True
            elif phase2_cells.cell_is_delay(cell):
                row["names_not_match_buffered"] = True
            elif phase2_cells.cell_is_constant_logic(cell):
                row["names_not_match_constant_logic"] = True
            else:
                row["names_not_match_remaining"] = True
        data.append(row)

    phase2_df = pd.DataFrame(data)
    for column in phase2_df.columns:
        if column == "cell":
            continue
        result_summary[column] = len(phase2_df[phase2_df[column]])

    data = []
    for cell in phase1_cells:
        if phase1_cells.is_non_functional_cell(cell):
            continue
        row = {
            # Cells is phase 1 but not in phase 2
            "removed_cell": False,
            "removed_cell_is_constant_logic": False,
        }
        if cell not in phase2_cells:
            row["removed_cell"] = True
            if phase1_cells.cell_is_constant_logic(cell):
                row["removed_cell_is_constant_logic"] = True
        data.append(row)

    phase1_df = pd.DataFrame(data)
    for column in phase1_df.columns:
        result_summary[column] = len(phase1_df[phase1_df[column]])

    return phase1_df, phase2_df, result_summary


class NetlistNetMapper(dict):
    """
    Maps netlist nodes to their respective connections.
    """
    def __init__(self, netlist):
        super().__init__()
        self._netlist = netlist
        self._phase_cells = NetlistCellMapper(netlist)

        for node, node_info in netlist.nodes.items():
            if node_info.get("type") in ["NET", "IO_PORT"]:
                self[node] = sorted(self._get_connected_node_info(netlist.predecessors(node)) +
                                    self._get_connected_node_info(netlist.successors(node)))

    def _get_connected_node_info(self, connected_nodes):
        node_info = []
        for node in connected_nodes:
            node_type = self._netlist.nodes[node]["type"]
            if node_type == "GATE" and not self._phase_cells.is_non_functional_cell(node):
                if self._phase_cells.cell_is_cloned(node) or self._phase_cells.cell_is_constant_logic(node):
                    continue
                node_info.append((node, self._phase_cells[node]))
            else:
                node_info.append((node, "IO_PORT"))
        return node_info

    def strip_neighbor_sizing_info(self, net):
        return [(node, self._phase_cells.strip_sizing_info(node) if node in self._phase_cells else node_type)
                for node, node_type in self.get(net)]

    def strip_neighbor_delay(self, net):
        return [(node, "delay" if node in self._phase_cells and self._phase_cells.cell_is_delay(node) else node_type)
                for node, node_type in self.get(net)]

class NetlistBufferChecker:
    """
    Analyzes buffering in netlists between two phases.
    
    Args:
        netlist1 (eda_schema.entity.NetlistEntity): The netlist of the first phase.
        netlist2 (eda_schema.entity.NetlistEntity): The netlist of the second phase.
    """
    def __init__(self, netlist1, netlist2):
        self.netlist1 = netlist1
        self.netlist2 = netlist2
        self.phase1_cells = NetlistCellMapper(netlist1)
        self.phase2_cells = NetlistCellMapper(netlist2)

    def net_is_buffered(self, net):
        """
        Determines if a given net was buffered between two netlist phases.
        
        Args:
            net (str): Name of the net to check.
        
        Returns:
            tuple:
                - bool: True if buffering was added, False otherwise.
                - list: List of added buffering nodes, if any.
        """
        fanout_df = pd.DataFrame([
            self.netlist1.nodes[node]["entity"].asdict()
            for node in sorted(self.netlist1.successors(net))
        ])

        phase1_nodes = [net] + list(fanout_df.name) if not fanout_df.empty else []
        phase2_nodes, fanout_nodes, node_queue = [net], list(fanout_df.name), [net]

        while fanout_nodes and node_queue:
            node = node_queue.pop(0)
            for next_node in self.netlist2.successors(node):
                if self.phase2_cells.cell_is_cloned(next_node):
                    continue
                phase2_nodes.append(next_node)
                if next_node in fanout_nodes:
                    fanout_nodes.remove(next_node)
                else:
                    node_queue.append(next_node)

        return self._compare_for_buffer_insertion(
            self._get_node_data(phase1_nodes, self.netlist1, self.phase1_cells),
            self._get_node_data(phase2_nodes, self.netlist2, self.phase2_cells)
        )

    def net_is_buffered_at_output(self, net):
        """
        Checks if a net is buffered specifically at its output.
        
        Args:
            net (str): Name of the net to check.
        
        Returns:
            tuple:
                - bool: True if buffering was added at the output, False otherwise.
                - str: Name of the buffered net, if applicable.
        """
        net_driving_gate = list(self.netlist2.predecessors(net))[0]

        net_driving_gate_fanout_nets2 = list(self.netlist2.successors(net_driving_gate))
        net_driving_gate_fanout_gates2 = []
        for fanout_net in net_driving_gate_fanout_nets2:
            net_driving_gate_fanout_gates2 += list(self.netlist2.successors(fanout_net))
        net_driving_gate_fanout_gates2 = sorted(net_driving_gate_fanout_gates2)

        net_driving_gate_fanout_nets1 = list(self.netlist1.successors(net_driving_gate))
        net_driving_gate_fanout_gates1 = []
        for fanout_net in net_driving_gate_fanout_nets1:
            net_driving_gate_fanout_gates1 += list(self.netlist1.successors(fanout_net))
        net_driving_gate_fanout_gates1 = sorted(net_driving_gate_fanout_gates1)

        phase1_data = self._get_node_data(net_driving_gate_fanout_gates1, self.netlist1, self.phase1_cells)
        phase2_data = self._get_node_data(net_driving_gate_fanout_gates2, self.netlist2, self.phase2_cells)

        is_buffered, _ = self._compare_for_buffer_insertion(phase1_data, phase2_data)
        if is_buffered:
            buffered_cell = list(phase2_data.difference(phase1_data))[0][0]
            buffered_net = list(self.netlist2.successors(buffered_cell))[0]
            return is_buffered, buffered_net
        return False, None

    @staticmethod
    def _get_node_data(nodes, netlist, phase_cells):
        """
        Extracts relevant node data for comparison.
        
        Args:
            nodes (list): List of nodes to extract data from.
            netlist (eda_schema.entity.NetlistEntity): The netlist containing the nodes.
            phase_cells (NetlistCellMapper): Mapper to extract cell information.
        
        Returns:
            set: A set containing tuples of (node, stripped cell information).
        """
        data = set()
        for node in nodes:
            node_data = netlist.nodes[node]
            if node_data["type"] == "GATE":
                data.add((node, phase_cells.strip_sizing_info(node)))
            if node_data["type"] == "NET":
                data.add((node, "NET"))
        return data

    def _compare_for_buffer_insertion(self, phase1_data, phase2_data):
        """
        Compares two sets of node data to detect buffer insertions.
        
        Args:
            phase1_data (set): Data from the first phase.
            phase2_data (set): Data from the second phase.
        
        Returns:
            tuple:
                - bool: True if buffering was detected, False otherwise.
                - list: List of added nets related to buffering.
        """
        is_buffered = True
        if len(phase1_data.difference(phase2_data)) > 0:
            is_buffered = False
        if phase1_data == phase2_data:
            is_buffered = False
        added_nets = []
        for node, node_type in phase2_data.difference(phase1_data):
            if node_type == "GATE" and not self.phase2_cells.cell_is_delay(node):
                is_buffered = False
            if node_type == "NET":
                added_nets.append(node)
        return [is_buffered, added_nets]


def compare_netlists_by_nets(phase1_netlist, phase2_netlist):
    """
    Compares two netlists and categorizes nodes into matching, resized, buffered, filler, or remaining categories.

    Args:
        phase1_netlist (eda_schema.entity.NetlistEntity): The netlist of the first phase.
        phase2_netlist (eda_schema.entity.NetlistEntity): The netlist of the second phase.
    
    Returns:
        tuple:
            - phase1_df (DataFrame): DataFrame of removed nets from phase 1.
            - phase2_df (DataFrame): DataFrame of new or modified nets in phase 2.
            - result_summary (dict): Summary dictionary of categorized changes.
    """
    phase1_nets, phase2_nets = NetlistNetMapper(phase1_netlist), NetlistNetMapper(phase2_netlist)
    phase2_cells = NetlistCellMapper(phase2_netlist)
    buffer_checker = NetlistBufferChecker(phase1_netlist, phase2_netlist)

    result_summary = {
        "init_stage_count": len(phase1_nets),
        "final_stage_count": len(phase2_nets),
    }

    buffer_added_nets, nets_name_matched_not_resolved, nets_name_not_matched = [], [], []
    data = []
    for net, phase2_neighbors in phase2_nets.items():
        row = {
            "net": net,
            "names_match": False,
            "names_match_neighbors_match": False,
            "names_match_neighbors_not_match": False,
            "names_match_neighbors_not_match_resized": False,
            "names_match_neighbors_not_match_delay": False,
            "names_match_neighbors_not_match_buffered": False,
            "names_match_neighbors_not_match_remaining": False,
            "names_not_match": False,
            "names_not_match_buffer_added": False,
            "names_not_match_buffer_added_output": False,
            "names_not_match_conb": False,
            "names_not_match_remaining": False,
        }

        phase1_neighbors = phase1_nets.get(net)
        if phase1_neighbors:
            row["names_match"] = True
            if phase1_neighbors == phase2_neighbors:
                row["names_match_neighbors_match"] = True
            else:
                row["names_match_neighbors_not_match"] = True
                if phase1_nets.strip_neighbor_sizing_info(net) == phase2_nets.strip_neighbor_sizing_info(net):
                    row["names_match_neighbors_not_match_resized"] = True
                elif phase1_nets.strip_neighbor_delay(net) == phase2_nets.strip_neighbor_delay(net):
                    row["names_match_neighbors_not_match_delay"] = True
                elif buffer_checker.net_is_buffered(net)[0]:
                    row["names_match_neighbors_not_match_buffered"] = True
                    buffer_added_nets += buffer_checker.net_is_buffered(net)[1]
                else:
                    row["names_match_neighbors_not_match_remaining"] = True
                    nets_name_matched_not_resolved.append(net)
        else:
            nets_name_not_matched.append(net)
            row["names_not_match"] = True

        data.append(row)
    phase2_df = pd.DataFrame(data).set_index("net")

    for net in nets_name_not_matched:
        phase2_neighbors = phase2_nets.get(net)
        if net in buffer_added_nets:
            phase2_df["names_not_match_buffer_added"][net] = True
            phase2_df["names_match_neighbors_not_match_remaining"][net] = False
        elif phase2_netlist.nodes[list(phase2_netlist.predecessors(net))[0]]["type"] == "GATE" and phase2_cells.cell_is_constant_logic(list(phase2_netlist.predecessors(net))[0]):
            phase2_df["names_not_match_conb"][net] = True
        elif buffer_checker.net_is_buffered_at_output(net)[0]:
            phase2_df["names_not_match_buffer_added_output"][net] = True
            buffered_net = buffer_checker.net_is_buffered_at_output(net)[1]
            if buffered_net in nets_name_matched_not_resolved:
                nets_name_matched_not_resolved.remove(buffered_net)
            phase2_df["names_match_neighbors_not_match_buffered"][buffered_net] = True
            phase2_df["names_match_neighbors_not_match_remaining"][buffered_net] = False
        else:
            phase2_df["names_not_match_remaining"][net] = True

    for column in phase2_df.columns:
        if column == "net":
            continue
        result_summary[column] = len(phase2_df[phase2_df[column]])

    data = []
    for net, phase1_neighbors in phase1_nets.items():
        row = {"net": net, "removed_net": False}
        if net not in phase2_nets:
            row["removed_net"] = True
        data.append(row)
    phase1_df = pd.DataFrame(data).set_index("net")
    for column in phase1_df.columns:
        if column == "net":
            continue
        result_summary[column] = len(phase1_df[phase1_df[column]])

    return phase1_df, phase2_df, result_summary
