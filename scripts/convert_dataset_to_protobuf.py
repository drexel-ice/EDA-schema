import os
from eda_schema.dataset import Dataset
from eda_schema.db import SQLitePickleDB
from eda_schema.protobuf_io import save_protobuf_file, dataset_to_protobuf

# Constants
DATASET_DIR = "dataset/test"
GRPC_DATASET_DIR = "dataset/test_dataset_grpc"
NETLIST_ID = 'id-000001'


def convert_dataset_to_protobuf(dataset_dir, grpc_dataset_dir, netlist_id):
    """
    Converts an EDA dataset from database format into Protobuf (.pb) files.

    Args:
        dataset_dir (str): Path to the existing dataset directory containing the database.
        grpc_dataset_dir (str): Output directory where Protobuf files will be saved.
        netlist_id (str): Netlist ID used to filter which netlist(s) to export.
    """
    dataset = Dataset(SQLitePickleDB(dataset_dir))
    dataset.load_standard_cells()
    dataset.load_dataset(netlist_id=netlist_id)

    for key, netlist in dataset.items():
        netlist_protobuf = dataset_to_protobuf(dataset, netlist)

        circuit, netlist_id, phase = key
        output_path = os.path.join(grpc_dataset_dir, circuit, netlist_id)
        os.makedirs(output_path, exist_ok=True)

        output_file = os.path.join(output_path, f"{phase}_netlist.pb")
        save_protobuf_file(netlist_protobuf, output_file)


if __name__ == "__main__":
    convert_dataset_to_protobuf(DATASET_DIR, GRPC_DATASET_DIR, NETLIST_ID)
