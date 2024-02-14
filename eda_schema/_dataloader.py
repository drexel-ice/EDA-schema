import re

from pynet.parser.lef_parser import LEFParser
from pynet.parser.parser import Parser, ParseModes

import eda_schema.entity as entity
from eda_schema.dataset import StandardCellData

from _parsers import parse_area, parse_power, parse_timing_report
from _liberty.parser import parse_liberty

PHASE_DICT = {
    "floorplan": "2_floorplan",
    "place": "3_place",
    "cts": "4_cts",
    "route": "5_route",
}


def calculate_rudy(net_bbox):
    """
    Calculate RUDY for a net based on each pin and the net's bounding box.

    Parameters:
    - net_bbox: Tuple (x_min, x_max, y_min, y_max) representing the bounding box of the net.

    Returns:
    - RUDY pin value.
    """
    w_k = net_bbox[1] - net_bbox[0]
    h_k = net_bbox[3] - net_bbox[2]

    return w_k * h_k / (w_k + h_k)


class PynetDataLoader:
    def __init__(self, lef_file, lib_file, dataset):
        self._dataset = dataset
        self._lef_file = lef_file
        self._lib_obj = self.get_lib_object(lib_file)
        self._dataset.standard_cells = self.get_standard_cell_data()

    @staticmethod
    def get_lef_object(lef_file):
        lef_obj = LEFParser(lef_file)
        lef_obj.parse()
        lef_obj_macro_dict = {}
        for k, v in lef_obj.macro_dict.items():
            lef_obj_macro_dict[k.replace(" ", "__")] = v
        lef_obj.macro_dict = lef_obj_macro_dict
        return lef_obj

    @staticmethod
    def get_lib_object(lib_file):
        lib_obj = {}
        library = parse_liberty(open(lib_file).read())
        for cell in library.get_groups('cell'):
            lib_obj[cell.args[0].value] = {}
            input_capacitance_list, output_capacitance_list, leakage_power_list = [], [], []

            for x in cell.__dict__["groups"]:
                if x.group_name == "leakage_power":
                    leakage_power_list.append(x.attributes[0].value)
                if x.group_name == "pin":
                    is_input, is_output = False, False
                    for attr in x.attributes:
                        if attr.name == "direction" and attr.value=="input":
                            is_input = True
                        if attr.name == "direction" and attr.value=="output":
                            is_output = True
                        if attr.name == "capacitance":
                            cap = attr.value
                    if is_input:
                        input_capacitance_list.append(cap)
                    if is_output:
                        output_capacitance_list.append(cap)

            if input_capacitance_list:
                lib_obj[cell.args[0].value]["input_capacitance_min"] = min(input_capacitance_list)
                lib_obj[cell.args[0].value]["input_capacitance_max"] = max(input_capacitance_list)
                lib_obj[cell.args[0].value]["input_capacitance_mean"] = sum(input_capacitance_list)/len(input_capacitance_list)
            else:
                lib_obj[cell.args[0].value]["input_capacitance_min"] = None
                lib_obj[cell.args[0].value]["input_capacitance_max"] = None
                lib_obj[cell.args[0].value]["input_capacitance_mean"] = None

            if output_capacitance_list:
                lib_obj[cell.args[0].value]["output_capacitance_min"] = min(output_capacitance_list)
                lib_obj[cell.args[0].value]["output_capacitance_max"] = max(output_capacitance_list)
                lib_obj[cell.args[0].value]["output_capacitance_mean"] = sum(output_capacitance_list)/len(output_capacitance_list)
            else:
                lib_obj[cell.args[0].value]["output_capacitance_min"] = None
                lib_obj[cell.args[0].value]["output_capacitance_max"] = None
                lib_obj[cell.args[0].value]["output_capacitance_mean"] = None

            if leakage_power_list:
                lib_obj[cell.args[0].value]["leakage_power_min"] = min(leakage_power_list)
                lib_obj[cell.args[0].value]["leakage_power_max"] = max(leakage_power_list)
            else:
                lib_obj[cell.args[0].value]["leakage_power_min"] = None
                lib_obj[cell.args[0].value]["leakage_power_max"] = None
            for cell_attr in cell.attributes:
                if cell_attr.name == "cell_leakage_power":
                    lib_obj[cell.args[0].value]["leakage_power_provided"] = cell_attr.value

        return lib_obj

    @staticmethod
    def get_standard_cell_entity(std_cell, standard_cell_info, lib_obj):
        no_ip, no_op = 0, 0
        for pin in standard_cell_info.pin_dict.values():
            if pin.info["DIRECTION"] == "INPUT":
                no_ip += 1
            if pin.info["DIRECTION"] == "OUTPUT":
                no_op += 1
        is_seq = "CLK" in standard_cell_info.pin_dict.keys() or "CLK_IN" in standard_cell_info.pin_dict.keys()

        std_cell_lib_obj = lib_obj.get(std_cell)

        return entity.StandardCellEntity({
            "name": std_cell,
            "width": standard_cell_info.info["SIZE"][0],
            "height": standard_cell_info.info["SIZE"][1],
            "no_of_input_pins": no_ip,
            "no_of_output_pins": no_op,
            "is_sequential": is_seq,
            "is_inverter": "inv" in std_cell,
            "is_buffer": "buf" in std_cell,
            "drive_strength": int(std_cell.split("_")[-1]) if std_cell[-1].isdigit() else None,
            "input_capacitance_min": lib_obj[std_cell]["input_capacitance_min"] if std_cell_lib_obj else 0,
            "input_capacitance_max": lib_obj[std_cell]["input_capacitance_max"] if std_cell_lib_obj else 0,
            "input_capacitance_mean": lib_obj[std_cell]["input_capacitance_mean"] if std_cell_lib_obj else 0,
            "output_capacitance_min": lib_obj[std_cell]["output_capacitance_min"] if std_cell_lib_obj else 0,
            "output_capacitance_max": lib_obj[std_cell]["output_capacitance_max"] if std_cell_lib_obj else 0,
            "output_capacitance_mean": lib_obj[std_cell]["output_capacitance_mean"] if std_cell_lib_obj else 0,
            "leakage_power_min": lib_obj[std_cell]["leakage_power_min"] if std_cell_lib_obj else 0,
            "leakage_power_max": lib_obj[std_cell]["leakage_power_max"] if std_cell_lib_obj else 0,
            "leakage_power_provided": lib_obj[std_cell]["leakage_power_provided"] if std_cell_lib_obj else 0,
        })

    def get_standard_cell_data(self):
        standard_cell_data = StandardCellData()
        lef_obj = self.get_lef_object(self._lef_file)
        for std_cell, standard_cell_info in lef_obj.macro_dict.items():
            if "fill" in std_cell:
                continue
            standard_cell_data[std_cell] = self.get_standard_cell_entity(std_cell, standard_cell_info, self._lib_obj)
            if standard_cell_data[std_cell].is_sequential:
                standard_cell_data.seq_cells.append(std_cell)
        return standard_cell_data

    @staticmethod
    def get_io_port_entity(netlist, node):
        return entity.IOPortEntity({
            "name": node,
            "direction": netlist.get_node_attribute(node, "node_type"),
            "x": netlist.get_node_attribute(node, "x"),
            "y": netlist.get_node_attribute(node, "y"),
            "y": netlist.get_node_attribute(node, "y"),
            "capacitance": netlist.get_node_attribute(node, "total_capacitance"),
        })

    @staticmethod
    def get_gate_entity(netlist, node):
        return entity.GateEntity({
            "name": str(node),
            "standard_cell": netlist.get_node_op(node),
            "logic_level": 0,
            "no_of_fanins": len(netlist.get_node_inputs(node)),
            "no_of_fanouts": len(netlist.get_node_outputs(node)),
            "x": netlist.get_node_attributes(node)["x"],
            "y": netlist.get_node_attributes(node)["y"],
        })

    @staticmethod
    def get_interconnect_segment_entity(route):
        points = route.points
        if len(points) != 2:
            return

        return entity.InterconnectSegmentEntity({
            "length": abs(points[0][0] - points[1][0]) + abs(points[0][1] - points[1][1]),
            "metal_layer": route.layer,
            "x1": points[0][0],
            "y1": points[0][1],
            "x2": points[1][0],
            "y2": points[1][1],
            "x": (points[0][0] + points[1][0])/2,
            "y": (points[0][1] + points[1][1])/2,
            "rudy": calculate_rudy([points[0][0], points[1][0], points[0][1], points[1][1]]),
            "resistance": None,
            "capacitance": None,
        })


    def get_interconnect_entity(self, netlist, node):
        interconnect_entity = entity.InterconnectEntity()

        hwpl = 0
        x_min, x_max, y_min, y_max = float("inf"), -float("inf"), float("inf"), -float("inf")
        edges = []
        routes = netlist.get_node_attribute(node, "routed")
        for i, route in enumerate(routes):
            interconnect_segment_entity = self.get_interconnect_segment_entity(route)
            if not interconnect_segment_entity:
                continue
            interconnect_segment_entity.name = f"{node}_{i}"

            interconnect_entity.add_node(
                interconnect_segment_entity.name,
                type="NETSEGMENT",
                object=interconnect_segment_entity
            )

            hwpl += interconnect_segment_entity.length
            for point in route.points:
                if point[0] < x_min:
                    x_min = point[0]
                if point[1] < y_min:
                    y_min = point[1]
                if point[0] > x_max:
                    x_max = point[0]
                if point[1] > y_max:
                    y_max = point[1]

        for net_segment_i in interconnect_entity.nodes:
            i_net_segment = interconnect_entity.nodes[net_segment_i]["object"]
            i_points = ((i_net_segment.x1, i_net_segment.y1), (i_net_segment.x2, i_net_segment.y2))
            for net_segment_j in interconnect_entity.nodes:
                j_net_segment = interconnect_entity.nodes[net_segment_j]["object"]
                j_points = ((j_net_segment.x1, j_net_segment.y1), (j_net_segment.x2, j_net_segment.y2))
                if net_segment_i == net_segment_j:
                    continue
                if i_points[0] in j_points or i_points[1] in j_points:
                    edges.append((net_segment_i, net_segment_j))

        for edge in edges:
            interconnect_entity.add_edge(*edge)

        interconnect_entity.load({
            "name": node,
            "no_of_inputs": len(netlist.get_node_inputs(node)),
            "no_of_outputs": len(netlist.get_node_outputs(node)),
            "hwpl": hwpl,
            "x_min": x_min,
            "y_min": y_min,
            "x_max": x_max,
            "y_max": y_max,
            "rudy": calculate_rudy([x_min, x_max, y_min, y_max]),
            "resistance": 0,
            "capacitance": netlist.get_node_attribute(node, "total_capacitance"),
        })

        return interconnect_entity

    @staticmethod
    def get_cell_area_entities(standard_cells, data_home, phase, netlist):
        cell_metric_dict = {
            "no_of_combinational_cells": 0,
            "no_of_sequential_cells": 0,
            "no_of_buffers": 0,
            "no_of_inverters": 0,
            "no_of_macros": 0,
            "no_of_total_cells": 0,
        }
        area_metric_dict = {
            "combinational_cell_area": 0,
            "sequential_cell_area": 0,
            "buffer_area": 0,
            "inverter_area": 0,
            "macro_area": 0,
            "cell_area": 0,
            "net_area": 0,
            "total_area": parse_area(f"{data_home}/openroad/reports/{phase}_area.rpt"),
        }

        for node in netlist.nodes:
            if netlist.get_node_attribute(node, "node_type") != "GATE":
                continue
            node_op = netlist.get_node_attribute(node, "op")
            x, y = standard_cells[node_op].width, standard_cells[node_op].height
            area = x * y

            cell_metric_dict["no_of_total_cells"] += 1
            area_metric_dict["cell_area"] += area
            if node_op in standard_cells.seq_cells:
                cell_metric_dict["no_of_sequential_cells"] += 1
                area_metric_dict["sequential_cell_area"] += area
            else:
                cell_metric_dict["no_of_combinational_cells"] += 1
                area_metric_dict["combinational_cell_area"] += area
            if "buf" in node_op:
                cell_metric_dict["no_of_buffers"] += 1
                area_metric_dict["buffer_area"] += area
            if "inv" in node_op:
                cell_metric_dict["no_of_inverters"] += 1
                area_metric_dict["inverter_area"] += area
        return (
            entity.CellMetricsEntity(cell_metric_dict),
            entity.AreaMetricsEntity(area_metric_dict)
        )

    @staticmethod
    def get_power_entity(data_home, phase):
        power_dict = parse_power(f"{data_home}/openroad/reports/{phase}_power.rpt")
        return entity.PowerMetricsEntity({
            "sequential_power": power_dict["total_sequential"],
            "combinational_power": power_dict["total_combinational"],
            "macro_power": power_dict["total_macro"],
            "internal_power": power_dict["internal_total"],
            "switching_power": power_dict["switching_total"],
            "leakage_power": power_dict["leakage_total"],
            "total_power": power_dict["total_total"],
        })

    @staticmethod
    def get_timing_path_entity(startpoint, endpoint, path_type, timing_path_info):
        timing_path_entity = entity.TimingPathEntity({
            "startpoint": startpoint,
            "endpoint": endpoint,
            "path_type": path_type,
            "arrival_time": timing_path_info["arrival_time_data"][-1][1],
            "required_time": timing_path_info["required_time_data"][-1][1],
            "slack": timing_path_info["slack"],
            "no_of_gates": (len(timing_path_info["arrival_time_data"]) - 4) / 2,
            "is_critical_path": False,
        })

        prev_node = None
        for i, x in enumerate(timing_path_info["arrival_time_data"]):
            match_obj = re.findall(r". (.*?)/.+? \((.*?)\)", x[5])
            if not match_obj:
                continue
            node = match_obj[0][0]

            timing_point_entity = entity.TimingPointEntity({
                "node_depth": i,
                "cell_delay": x[0],
                "arrival_time": x[1],
                "slew": x[2],
                "is_rise_transition": x[3],
                "is_fall_transition": x[4],
            })
            timing_path_entity.add_node(node, type="TIMINGPOINT", object=timing_point_entity)

            if prev_node:
                timing_path_entity.add_edge(prev_node, node)
            prev_node = node

        return timing_path_entity

    def add_timing_paths(self, netlist_entity, data_home, phase):
        timing_dict = parse_timing_report(f"{data_home}/openroad/reports/{phase}_timing_min.rpt")
        for (startpoint, endpoint), timing_path_info in timing_dict.items():
            timing_path_entity = self.get_timing_path_entity(startpoint, endpoint, "min", timing_path_info)
            netlist_entity.timing_paths[(startpoint, endpoint, "min")] = timing_path_entity

        critical_path_dict = {
            "startpoint": None,
            "endpoint": None,
            "no_of_timing_paths": 0,
            "worst_slack": None,
            "total_negative_slack": 0,
            "no_of_slack_violations": 0,
        }
        timing_dict = parse_timing_report(f"{data_home}/openroad/reports/{phase}_timing_max.rpt")
        for (startpoint, endpoint), timing_path_info in timing_dict.items():
            timing_path_entity = self.get_timing_path_entity(startpoint, endpoint, "max", timing_path_info)
            netlist_entity.timing_paths[(startpoint, endpoint, "max")] = timing_path_entity

            critical_path_dict["no_of_timing_paths"] += 1
            if timing_path_entity.slack <= critical_path_dict["worst_slack"]:
                critical_path_dict["worst_slack"] = timing_path_entity.slack
                critical_path_dict["startpoint"] = startpoint
                critical_path_dict["endpoint"] = endpoint
            if timing_path_entity.slack < 0:
                critical_path_dict["no_of_slack_violations"] += 1
                critical_path_dict["total_negative_slack"] += timing_path_entity.slack

        netlist_entity.timing_paths[(
            critical_path_dict["startpoint"],
            critical_path_dict["endpoint"],
            "max",
        )].is_critical_path = True
        netlist_entity.critical_path_metrics = entity.CriticalPathMetricsEntity(
            critical_path_dict
        )

    def get_clock_tree_entity(self, netlist_entity, clock_source):
        clock_tree_entity = entity.ClockTreeEntity()
        clock_tree_entity.load_from_netlist(netlist_entity, clock_source, self._dataset.standard_cells.seq_cells)
        return clock_tree_entity

    def add_netlist(self, circuit, netlist_id, phase, data_home, clock_source):
        parser = Parser(
            f"{data_home}/openroad/outputs/{PHASE_DICT[phase]}.def",
            ParseModes.DEF,
            self._lef_file,
            spef_file=f"{data_home}/openroad/outputs/6_final.spef",
        )
        netlist = parser.parse()

        netlist_entity = entity.NetlistEntity()

        no_of_pins = 0
        no_of_nets = 0
        for node in netlist.nodes:
            if netlist.get_node_attribute(node, "node_type") in ["INPUT", "OUTPUT"]:
                io_port = self.get_io_port_entity(netlist, node)
                info_dict = {"type": "PORT", "object": io_port}

            if netlist.get_node_attribute(node, "node_type") == "GATE":
                if phase is not "floorplan" and netlist.get_node_attributes(node)["x"] is None:
                    continue
                gate = self.get_gate_entity(netlist, node)
                info_dict = {"type": "GATE", "object": gate}
                no_of_pins += self._dataset.standard_cells[gate.standard_cell].no_of_input_pins
                no_of_pins += self._dataset.standard_cells[gate.standard_cell].no_of_output_pins

            if netlist.get_node_attribute(node, "node_type") == "WIRE":
                interconnect = self.get_interconnect_entity(netlist, node)
                info_dict = {"type": "INTERCONNECT", "object": interconnect}
                no_of_nets += 1

            netlist_entity.add_node(node, **info_dict)

        for edge in netlist.edges:
            netlist_entity.add_edge(*edge)

        netlist_cell_metrics, netlist_area_metrics = self.get_cell_area_entities(
            self._dataset.standard_cells, data_home, phase, netlist
        )
        netlist_entity.cell_metrics = netlist_cell_metrics
        netlist_entity.area_metrics = netlist_area_metrics
        netlist_entity.power_metrics = self.get_power_entity(data_home, phase)

        self.add_timing_paths(netlist_entity, data_home, phase)
        netlist_entity.clock_trees[clock_source] = self.get_clock_tree_entity(netlist_entity, clock_source)

        netlist_entity.load({
            "width": netlist.attributes["width"],
            "height": netlist.attributes["length"],
            "no_of_inputs": len(netlist.inputs),
            "no_of_outputs": len(netlist.outputs),
            "cell_density": netlist_cell_metrics.no_of_total_cells / netlist_area_metrics.total_area,
            "pin_density": no_of_pins / netlist_area_metrics.total_area,
            "net_density": no_of_nets / netlist_area_metrics.total_area,
        })

        self._dataset[(circuit, netlist_id, phase)] = netlist_entity


    def get_dataset(self):
        return self._dataset
