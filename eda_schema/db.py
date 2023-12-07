import os
import json
import pandas as pd

from eda_schema import entity


class RawDB:
    standard_cell_columns = list(entity.StandardCellEntity().schema["items"]["properties"].keys())
    netlist_columns = list(entity.NetlistEntity().schema["items"]["properties"].keys())
    cell_metric_columns = list(entity.CellMetricsEntity().schema["items"]["properties"].keys())
    area_metric_columns = list(entity.AreaMetricsEntity().schema["items"]["properties"].keys())
    power_metric_columns = list(entity.PowerMetricsEntity().schema["items"]["properties"].keys())
    critical_path_metric_columns = list(entity.CriticalPathMetricsEntity().schema["items"]["properties"].keys())
    io_port_columns = list(entity.IOPortEntity().schema["items"]["properties"].keys())
    gate_columns = list(entity.GateEntity().schema["items"]["properties"].keys())
    net_columns = list(entity.InterconnectEntity().schema["items"]["properties"].keys())
    net_segment_columns = list(entity.InterconnectSegmentEntity().schema["items"]["properties"].keys())
    timing_path_columns = list(entity.TimingPathEntity().schema["items"]["properties"].keys())
    timing_point_columns = list(entity.TimingPointEntity().schema["items"]["properties"].keys())
    clock_tree_columns = list(entity.ClockTreeEntity().schema["items"]["properties"].keys())

    def __init__(self, data_home):
        self.data_home = data_home

    def create_table(self, entity_name, columns):
        if not os.path.exists(f"{self.data_home}/{entity_name}"):
            os.mkdir(f"{self.data_home}/{entity_name}")
        pd.DataFrame(columns=columns).to_csv(
            f"{self.data_home}/{entity_name}/table.csv", index=False
        )

    def create_dataset_tables(self):
        if not os.path.exists(f"{self.data_home}"):
            os.mkdir(f"{self.data_home}")

        self.create_table("standard_cells", entity.KEY_COLUMNS + self.standard_cell_columns)
        self.create_table("netlists", entity.KEY_COLUMNS + self.netlist_columns)
        self.create_table("cell_metrics", entity.KEY_COLUMNS + self.cell_metric_columns)
        self.create_table("area_metrics", entity.KEY_COLUMNS + self.area_metric_columns)
        self.create_table("power_metrics", entity.KEY_COLUMNS + self.power_metric_columns)
        self.create_table("critical_path_metrics", entity.KEY_COLUMNS + self.critical_path_metric_columns)
        self.create_table("ports", entity.KEY_COLUMNS + self.io_port_columns)
        self.create_table("gates", entity.KEY_COLUMNS + self.gate_columns)
        self.create_table("nets", entity.KEY_COLUMNS + self.net_columns)
        self.create_table("net_segments", entity.KEY_COLUMNS + ["net_name"] + self.net_segment_columns)
        self.create_table("timing_paths", entity.KEY_COLUMNS + self.timing_path_columns)
        self.create_table("timing_points", entity.KEY_COLUMNS + ["startpoint", "endpoint"] + self.timing_point_columns)
        self.create_table("clock_trees", entity.KEY_COLUMNS + ["clock_source"] + self.clock_tree_columns)

    def add_graph_data(self, entity_name, graph, key):
        with open(f"{self.data_home}/{entity_name}/{key}.json", "w") as out_file:
            json.dump(
                graph.graph_dict(),
                out_file,
                indent=4,
            )

    def get_graph_data(self, entity_name, key):
        with open(f"{self.data_home}/{entity_name}/{key}.json") as out_file:
            return json.load(out_file)

    def add_table_row(self, entity_name, row):
        pd.DataFrame([row]).to_csv(
            f"{self.data_home}/{entity_name}/table.csv", mode="a", index=False, header=False
        )

    def add_table_data(self, entity_name, data):
        pd.DataFrame(data).to_csv(
            f"{self.data_home}/{entity_name}/table.csv", mode="a", index=False, header=False
        )

    def get_table_data(self, entity_name, **kwargs):
        df = pd.read_csv(f"{self.data_home}/{entity_name}/table.csv")
        for k, v in kwargs.items():
            df = df[df[k]==v]
        return df

    def get_table_row(self, entity_name, **kwargs):
        df = self.get_table_data(entity_name, **kwargs)
        return df.iloc[0]
