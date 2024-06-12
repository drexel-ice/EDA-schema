import os
import json
import pandas as pd
from pymongo import MongoClient


from eda_schema import entity

class BaseDB:
    """
    Base class for managing data tables and graph data storage.
    """
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

    def create_dataset_tables(self):
        """
        Create tables for all entities in the dataset.
        """
        raise NotImplementedError

    def add_graph_data(self, entity_name, graph, key):
        """
        Add graph data to the database.

        Args:
            entity_name (str): Name of the entity.
            graph: Graph object containing the data.
            key (str): Unique identifier for the graph data.
        """
        raise NotImplementedError

    def get_graph_data(self, entity_name, key):
        """
        Retrieve graph data from the database.

        Args:
            entity_name (str): Name of the entity.
            key (str): Unique identifier for the graph data.

        Returns:
            dict: Graph data as a dictionary.
        """
        raise NotImplementedError

    def add_table_row(self, entity_name, row):
        """
        Add a row to a data table in the database.

        Args:
            entity_name (str): Name of the entity.
            row (dict): Data for the new row.
        """
        raise NotImplementedError

    def add_table_data(self, entity_name, data):
        """
        Add multiple rows to a data table in the database.

        Args:
            entity_name (str): Name of the entity.
            data (list): List of dictionaries containing data for multiple rows.
        """
        raise NotImplementedError

    def get_table_data(self, entity_name, **kwargs):
        """
        Retrieve data from a data table in the database.

        Args:
            entity_name (str): Name of the entity.
            **kwargs: Filtering criteria for retrieving data.

        Returns:
            pd.DataFrame: Data from the specified data table.
        """
        raise NotImplementedError

    def get_table_row(self, entity_name, **kwargs):
        """
        Retrieve a specific row from a data table in the database.

        Args:
            entity_name (str): Name of the entity.
            **kwargs: Filtering criteria for retrieving data.

        Returns:
            pd.Series: A specific row from the specified data table.
        """
        raise NotImplementedError


class FileDB(BaseDB):
    """
    File-based database for storing EDA-related data.

    Attributes:
        data_home (str): Directory path where data tables and graph data are stored.
    """

    def __init__(self, data_home):
        """
        Initialize the FileDB object.

        Args:
            data_home (str): Directory path where data tables and graph data are stored.
        """
        self.data_home = data_home

    def _create_table(self, entity_name, columns):
        """
        Create a data table for a specific entity.

        Args:
            entity_name (str): Name of the entity.
            columns (list): List of columns for the data table.
        """
        if not os.path.exists(f"{self.data_home}/{entity_name}"):
            os.mkdir(f"{self.data_home}/{entity_name}")
        pd.DataFrame(columns=columns).to_csv(
            f"{self.data_home}/{entity_name}/table.csv", index=False
        )

    def create_dataset_tables(self):
        """
        Create tables for all entities in the dataset.
        """
        if not os.path.exists(f"{self.data_home}"):
            os.mkdir(f"{self.data_home}")

        self._create_table("standard_cells", self.standard_cell_columns)
        self._create_table("netlists", entity.KEY_COLUMNS + self.netlist_columns)
        self._create_table("cell_metrics", entity.KEY_COLUMNS + self.cell_metric_columns)
        self._create_table("area_metrics", entity.KEY_COLUMNS + self.area_metric_columns)
        self._create_table("power_metrics", entity.KEY_COLUMNS + self.power_metric_columns)
        self._create_table("critical_path_metrics", entity.KEY_COLUMNS + self.critical_path_metric_columns)
        self._create_table("ports", entity.KEY_COLUMNS + self.io_port_columns)
        self._create_table("gates", entity.KEY_COLUMNS + self.gate_columns)
        self._create_table("nets", entity.KEY_COLUMNS + self.net_columns)
        self._create_table("net_segments", entity.KEY_COLUMNS + ["net_name"] + self.net_segment_columns)
        self._create_table("timing_paths", entity.KEY_COLUMNS + self.timing_path_columns)
        self._create_table("timing_points", entity.KEY_COLUMNS + ["startpoint", "endpoint", "path_type"] + self.timing_point_columns)
        self._create_table("clock_trees", entity.KEY_COLUMNS + ["clock_source"] + self.clock_tree_columns)

    def add_graph_data(self, entity_name, graph, key):
        """
        Add graph data to the database.

        Args:
            entity_name (str): Name of the entity.
            graph: Graph object containing the data.
            key (str): Unique identifier for the graph data.
        """
        with open(f"{self.data_home}/{entity_name}/{key}.json", "w") as out_file:
            json.dump(graph.graph_dict(), out_file)

    def get_graph_data(self, entity_name, key):
        """
        Retrieve graph data from the database.

        Args:
            entity_name (str): Name of the entity.
            key (str): Unique identifier for the graph data.

        Returns:
            dict: Graph data as a dictionary.
        """
        with open(f"{self.data_home}/{entity_name}/{key}.json") as out_file:
            return json.load(out_file)

    def add_table_row(self, entity_name, row):
        """
        Add a row to a data table in the database.

        Args:
            entity_name (str): Name of the entity.
            row (dict): Data for the new row.
        """
        pd.DataFrame([row]).to_csv(
            f"{self.data_home}/{entity_name}/table.csv", mode="a", index=False, header=False
        )

    def add_table_data(self, entity_name, data):
        """
        Add multiple rows to a data table in the database.

        Args:
            entity_name (str): Name of the entity.
            data (list): List of dictionaries containing data for multiple rows.
        """
        pd.DataFrame(data).to_csv(
            f"{self.data_home}/{entity_name}/table.csv", mode="a", index=False, header=False
        )

    def get_table_data(self, entity_name, **kwargs):
        """
        Retrieve data from a data table in the database.

        Args:
            entity_name (str): Name of the entity.
            **kwargs: Filtering criteria for retrieving data.

        Returns:
            pd.DataFrame: Data from the specified data table.
        """
        df = pd.read_csv(f"{self.data_home}/{entity_name}/table.csv")
        for k, v in kwargs.items():
            df = df[df[k]==v]
        return df

    def get_table_row(self, entity_name, **kwargs):
        """
        Retrieve a specific row from a data table in the database.

        Args:
            entity_name (str): Name of the entity.
            **kwargs: Filtering criteria for retrieving data.

        Returns:
            pd.Series: A specific row from the specified data table.
        """
        df = self.get_table_data(entity_name, **kwargs)
        return df.iloc[0]


class MongoDB(BaseDB, MongoClient):
    """
    MongoDB database for storing EDA-related data.

    Attributes:
        data_home (str): Directory path where data tables and graph data are stored.
    """

    def __init__(self, db_uri, db_name):
        """
        Initialize the FileDB object.

        Args:
            data_home (str): Directory path where data tables and graph data are stored.
        """
        self.db_uri = db_uri
        self.db_name = db_name
        super().__init__(self.db_uri)
        self.db = self[self.db_name]


    def create_dataset_tables(self):
        """
        Create tables for all entities in the dataset.
        """
        self.drop_database(self.db_name)
        self.db["metadata"].insert_many([
            {"entity": "standard_cells", "columns": self.standard_cell_columns},
            {"entity": "netlists", "columns": entity.KEY_COLUMNS + self.netlist_columns},
            {"entity": "cell_metrics", "columns": entity.KEY_COLUMNS + self.cell_metric_columns},
            {"entity": "area_metrics", "columns": entity.KEY_COLUMNS + self.area_metric_columns},
            {"entity": "power_metrics", "columns": entity.KEY_COLUMNS + self.power_metric_columns},
            {"entity": "critical_path_metrics", "columns": entity.KEY_COLUMNS + self.critical_path_metric_columns},
            {"entity": "ports", "columns": entity.KEY_COLUMNS + self.io_port_columns},
            {"entity": "gates", "columns": entity.KEY_COLUMNS + self.gate_columns},
            {"entity": "nets", "columns": entity.KEY_COLUMNS + self.net_columns},
            {"entity": "net_segments", "columns": entity.KEY_COLUMNS + ["net_name"] + self.net_segment_columns},
            {"entity": "timing_paths", "columns": entity.KEY_COLUMNS + self.timing_path_columns},
            {"entity": "timing_points", "columns": entity.KEY_COLUMNS + ["startpoint", "endpoint", "path_type"] + self.timing_point_columns},
            {"entity": "clock_trees", "columns": entity.KEY_COLUMNS + ["clock_source"] + self.clock_tree_columns},
        ])

    def add_graph_data(self, entity_name, graph, key):
        """
        Add graph data to the database.

        Args:
            entity_name (str): Name of the entity.
            graph: Graph object containing the data.
            key (str): Unique identifier for the graph data.
        """
        self.db[entity_name + "_graph"].insert_one({
            "key": key,
            **graph.graph_dict()
        })

    def get_graph_data(self, entity_name, key):
        """
        Retrieve graph data from the database.

        Args:
            entity_name (str): Name of the entity.
            key (str): Unique identifier for the graph data.

        Returns:
            dict: Graph data as a dictionary.
        """
        return self.db[entity_name + "_graph"].find_one({"key": key})

    def add_table_row(self, entity_name, row):
        """
        Add a row to a data table in the database.

        Args:
            entity_name (str): Name of the entity.
            row (dict): Data for the new row.
        """
        self.db[entity_name + "_tabular"].insert_one(row)

    def add_table_data(self, entity_name, data):
        """
        Add multiple rows to a data table in the database.

        Args:
            entity_name (str): Name of the entity.
            data (list): List of dictionaries containing data for multiple rows.
        """
        self.db[entity_name + "_tabular"].insert_many(data)

    def get_table_data(self, entity_name, **kwargs):
        """
        Retrieve data from a data table in the database.

        Args:
            entity_name (str): Name of the entity.
            **kwargs: Filtering criteria for retrieving data.

        Returns:
            pd.DataFrame: Data from the specified data table.
        """
        data = list(self.db[entity_name + "_tabular"].find(kwargs))
        for row in data:
            row.pop("_id")
        columns = self.db["metadata"].find_one({"entity": entity_name})["columns"]
        return pd.DataFrame(data, columns=columns)

    def get_table_row(self, entity_name, **kwargs):
        """
        Retrieve a specific row from a data table in the database.

        Args:
            entity_name (str): Name of the entity.
            **kwargs: Filtering criteria for retrieving data.

        Returns:
            pd.Series: A specific row from the specified data table.
        """
        row = self.db[entity_name + "_tabular"].find_one(kwargs)
        if row:
            row.pop("_id")
        return pd.Series(row)
