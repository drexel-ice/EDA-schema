import os
import json

import dill
import sqlite3

import pandas as pd
from pymongo import MongoClient

from eda_schema import entity
from eda_schema.errors import DataNotFoundError


class SchemaMetadata:
    standard_cells = entity.StandardCellEntity().schema["items"]["properties"]
    stages = entity.StageEntity().schema["items"]["properties"]
    netlists = entity.NetlistEntity().schema["items"]["properties"]
    cell_metrics = entity.CellMetricsEntity().schema["items"]["properties"]
    area_metrics = entity.AreaMetricsEntity().schema["items"]["properties"]
    power_metrics = entity.PowerMetricsEntity().schema["items"]["properties"]
    timing_metrics = entity.TimingMetricsEntity().schema["items"]["properties"]
    ports = entity.PortEntity().schema["items"]["properties"]
    gates = entity.GateEntity().schema["items"]["properties"]
    pins = entity.PinEntity().schema["items"]["properties"]
    nets = entity.InterconnectEntity().schema["items"]["properties"]
    wires = {
        "net_name": {"type": "string"},
        **entity.WireEntity().schema["items"]["properties"]
    }
    timing_graphs = entity.TimingGraphEntity().schema["items"]["properties"]
    timing_paths = entity.TimingPathEntity().schema["items"]["properties"]
    timing_path_pins = {
        "startpoint": {"type": "string"},
        "endpoint": {"type": "string"},
        "path_type": {"type": "string"},
        **entity.TimingPathPinEntity().schema["items"]["properties"],
    }
    clock_trees = entity.ClockTreeEntity().schema["items"]["properties"]

    @classmethod
    def items(cls):
        """Returns an iterable of (name, schema) tuples for all defined schemas."""
        return [(attr, getattr(cls, attr)) for attr in dir(cls)
                if not attr.startswith("__") and not callable(getattr(cls, attr))]

    @classmethod
    def get_schema(cls, name):
        """Get the schema for a specific entity by name."""
        return getattr(cls, name, None)

    @classmethod
    def is_graph_entity(cls, entity_name):
        return entity_name in ["netlists", "clock_trees", "timing_paths", "timing_graphs", "nets"]


class BaseDB:
    """
    Base class for managing data tables and graph data storage.
    """
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

    def _create_table(self, entity_name, columns, is_graph_entity):
        """
        Create a data table for a specific entity.

        Args:
            entity_name (str): Name of the entity.
            columns (list): List of columns for the data table.
        """
        if not os.path.exists(f"{self.data_home}/{entity_name}"):
            os.mkdir(f"{self.data_home}/{entity_name}")
        if is_graph_entity and not os.path.exists(f"{self.data_home}/{entity_name}/graphs"):
            os.mkdir(f"{self.data_home}/{entity_name}/graphs")
        pd.DataFrame(columns=columns).to_csv(
            f"{self.data_home}/{entity_name}/table.csv", index=False
        )

    def create_dataset_tables(self):
        """
        Create tables for all entities in the dataset.
        """
        if not os.path.exists(f"{self.data_home}"):
            os.mkdir(f"{self.data_home}")

        for entity_name, schema in SchemaMetadata.items():
            if entity_name == "standard_cells":
                self._create_table(entity_name, list(schema.keys()), is_graph_entity=SchemaMetadata.is_graph_entity(entity_name))
            else:
                self._create_table(entity_name, entity.KEY_COLUMNS + list(schema.keys()), is_graph_entity=SchemaMetadata.is_graph_entity(entity_name))

    def add_graph_data(self, entity_name, graph, key):
        """
        Add graph data to the database.

        Args:
            entity_name (str): Name of the entity.
            graph: Graph object containing the data.
            key (str): Unique identifier for the graph data.
        """
        with open(f"{self.data_home}/{entity_name}/graphs/{key}.json", "w") as out_file:
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
        with open(f"{self.data_home}/{entity_name}/graphs/{key}.json") as out_file:
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
        metadata = []
        for entity_name, schema in SchemaMetadata.items():
            if entity_name == "standard_cells":
                self._create_table(entity_name, list(schema.keys()))
                metadata.append({"entity": entity_name, "columns": list(schema.keys())})
            else:
                metadata.append({"entity": entity_name, "columns": entity.KEY_COLUMNS + list(schema.keys())})
        self.db["metadata"].insert_many(metadata)

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
        if entity_name=="timing_paths":
            df = pd.DataFrame(data, columns=columns)
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


class SQLitePickleDB(BaseDB):
    """
    Storage class that uses SQLite for tables and pickle files for graph data.
    """

    def __init__(self, data_dir):
        """
        Initialize the SQLite connection and graph storage directory.

        Args:
            db_path (str): Path to the SQLite database file.
            graph_dir (str): Directory to store graph pickle files.
        """
        self.conn = sqlite3.connect(f"{data_dir}/tabular.db")
        self.cursor = self.conn.cursor()
        self.graph_dir = f"{data_dir}/graph_dir"

        # Create the graph directory if it doesn't exist
        if not os.path.exists(self.graph_dir):
            os.makedirs(self.graph_dir)

    def create_dataset_tables(self):
        """
        Create tables for all entities in the dataset.
        """
        def map_json_type_to_sqlite(schema_type):
            schema_type_str = str(schema_type)

            if "number" in schema_type_str:
                datatype = "REAL"
            if "string" in schema_type_str:
                datatype = "TEXT"
            if "boolean" in schema_type_str:
                datatype = "INTEGER"
            is_nullable = "null" in schema_type_str

            return datatype, is_nullable

        for entity_name, schema in SchemaMetadata.items():
            if entity_name == "standard_cells":
                columns = []
            else:
                columns = [f"{col} TEXT NOT NULL" for col in entity.KEY_COLUMNS]

            for column_name, column_schema in schema.items():
                sqlite_type, is_nullable = map_json_type_to_sqlite(column_schema["type"])
                null_constraint = "NULL" if is_nullable else "NOT NULL"
                columns.append(f"{column_name} {sqlite_type} {null_constraint}")

            columns_def = ", ".join(columns)
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {entity_name} ({columns_def});")

        self.conn.commit()

    def add_graph_data(self, entity_name, graph, key):
        """
        Add graph data to the database.

        Args:
            entity_name (str): Name of the entity.
            graph: Graph object containing the data.
            key (str): Unique identifier for the graph data.
        """
        filepath = os.path.join(self.graph_dir, f"{entity_name}_{key}.pkl")
        with open(filepath, "wb") as f:
            dill.dump(graph, f)

    def get_graph_data(self, entity_name, key):
        """
        Retrieve graph data from the database.

        Args:
            entity_name (str): Name of the entity.
            key (str): Unique identifier for the graph data.

        Returns:
            The loaded graph object.
        """
        filepath = os.path.join(self.graph_dir, f"{entity_name}_{key}.pkl")
        with open(filepath, 'rb') as f:
            return dill.load(f)

    def add_table_row(self, entity_name, row):
        """
        Add a row to a data table in the database.

        Args:
            entity_name (str): Name of the entity.
            row (dict): Data for the new row.
        """
        columns = ", ".join(row.keys())
        placeholders = ", ".join(["?" for _ in row])
        values = tuple(row.values())

        self.cursor.execute(f"INSERT INTO {entity_name} ({columns}) VALUES ({placeholders});", values)
        self.conn.commit()

    def add_table_data(self, entity_name, data):
        """
        Add multiple rows to a data table in the database.

        Args:
            entity_name (str): Name of the entity.
            data (list of dict): List of rows to insert into the table.
        """
        if not data:
            return

        columns = ", ".join(data[0].keys())
        placeholders = ", ".join(["?" for _ in data[0]])
        values = [tuple(row.values()) for row in data]

        self.cursor.executemany(f"INSERT INTO {entity_name} ({columns}) VALUES ({placeholders});", values)
        self.conn.commit()

    def get_table_data(self, entity_name, **kwargs):
        """
        Retrieve data from a data table in the database.

        Args:
            entity_name (str): Name of the entity.
            **kwargs: Filtering criteria for retrieving data.

        Returns:
            pd.DataFrame: Data from the specified data table.
        """
        query = f"SELECT * FROM {entity_name}"
        if kwargs:
            conditions = " AND ".join([f"{k} = ?" for k in kwargs])
            query += f" WHERE {conditions}"
            df = pd.read_sql_query(query, self.conn, params=tuple(kwargs.values()))
        else:
            df = pd.read_sql_query(query, self.conn)

        schema = SchemaMetadata.get_schema(entity_name)
        for column in df.columns:
            if column in entity.KEY_COLUMNS:
                continue
            if schema[column]["type"] == "boolean" or "boolean" in schema[column]["type"]:
                df[column] = df[column].astype(bool)

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
        return df.iloc[0] if not df.empty else None

    def save_netlist(self, netlist, circuit, netlist_id, phase):
        key_str = f"{circuit}-{netlist_id}-{phase}"
        timing_paths = netlist.timing_paths
        netlist.timing_paths = []
        self.add_graph_data("netlists", netlist, key_str)

        filepath = os.path.join(self.graph_dir, f"timing_paths_{key_str}.pkl")
        with open(filepath, "wb") as f:
            dill.dump(timing_paths, f)
        netlist.timing_paths = timing_paths

    def load_netlist(self, circuit, netlist_id, phase, load_timing_paths=True):
        key_str = f"{circuit}-{netlist_id}-{phase}"
        try:
            netlist_entity = self.get_graph_data("netlists", key_str)
            if load_timing_paths:
                filepath = os.path.join(self.graph_dir, f"timing_paths_{key_str}.pkl")
                with open(filepath, 'rb') as f:
                    netlist_entity.timing_paths = dill.load(f)
        except FileNotFoundError:
            raise DataNotFoundError(entity_name=key_str)
        return netlist_entity
