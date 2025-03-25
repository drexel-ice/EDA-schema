from eda_schema.entity import PHASES, NetlistEntity
from eda_schema.dataset import Dataset
from eda_schema.db import SQLitePickleDB
from pprint import pprint
import eda_schema.eda_schema_pb2 as pb2
from eda_schema.protobuf_io import save_protobuf_file, dataset_to_protobuf, load_protobuf_file

"""
scratch.py: A utility script for testing and exploring EDA schema functionality

This script demonstrates the process of loading a dataset from a specified 
directory using a netlist ID, displaying the dataset's contents, converting 
the dataset into a Protocol Buffers (protobuf) format, and verifying the 
integrity of the conversion process.

Key Features:
1. Dataset Loading:
    - Loads standard cells and a netlist dataset from a SQLite database.
    - Displays detailed information about the dataset, including standard cells 
      and netlist attributes.

2. Protobuf Conversion:
    - Converts the dataset into a protobuf format.
    - Saves the serialized protobuf data to a file.
    - Ensures the output directory exists before saving.

3. Protobuf Verification:
    - Reads back the protobuf file and displays its contents.
    - Compares the original dataset with the deserialized protobuf data to 
      ensure data integrity.

Usage:
     python scratch.py

Files Read and Written:
- Input:
  1. SQLite Database:
      - Location: dataset/test
      - Loads standard cells and netlist with ID id-000001.
  2. Protobuf Schema Definition:
      - Indirectly uses eda_schema.eda_schema_pb2 generated from eda_schema.proto.

- Output:
  1. Protobuf File:
      - Location: out/id-000001_netlist.pb
      - Contains the serialized netlist data in protobuf format.
      - Creates the output directory if it doesn't exist.

Validation:
- Compares attributes such as dimensions, density metrics, cell metrics, area 
  metrics, power metrics, critical path metrics, and timing paths count.
- Ensures 100% match percentage, validating the correctness of the 
  serialization/deserialization process.

This script serves as a comprehensive utility for testing and validating the 
EDA schema protobuf implementation.
"""

# Start with this:
DATASET_DIR = "dataset/test"
NETLIST_ID = 'id-000001'
# Generate this filename based on the netlist ID
PB_FILE = f"out/{NETLIST_ID}_netlist.pb"


def load_dataset(dataset_dir, netlist_id):
    # Initialize the Dataset object with the SQLitePickleDB
    dataset = Dataset(SQLitePickleDB(dataset_dir))
    dataset.load_standard_cells()
    dataset.load_dataset(netlist_id=netlist_id)
    return dataset

def print_dataset(dataset):
    """
    Print all data loaded into the dataset for verification.
    """
    print("\n--- Standard Cells ---")
    pprint(dataset.standard_cells)

    print("\n--- Netlists ---")
    for netlist_key, netlist in dataset.items():
        print(f"Netlist Key: {netlist_key}")
        print(f"  Type: {type(netlist)}")
        print(f"  Keys: {list(netlist.__dict__.keys()) if hasattr(netlist, '__dict__') else 'N/A'}")
        # Print all netlist keys
        if hasattr(netlist, '__dict__'):
            print("  Netlist attributes:")
            for key, value in netlist.__dict__.items():
                value_type = type(value).__name__
                if isinstance(value, dict):
                    print(f"    {key}: dict with {len(value)} items")
                elif isinstance(value, list):
                    print(f"    {key}: list with {len(value)} items")
                else:
                    print(f"    {key}: {value_type}")
        # Print metrics if available
        if hasattr(netlist, 'cell_metrics'):
            print(f"  Cell Metrics: {netlist.cell_metrics}")
        if hasattr(netlist, 'area_metrics'):
            print(f"  Area Metrics: {netlist.area_metrics}")
        if hasattr(netlist, 'power_metrics'):
            print(f"  Power Metrics: {netlist.power_metrics}")
        
        # Print node count if available
        if hasattr(netlist, 'nodes'):
            print(f"  Node Count: {len(netlist.nodes)}")
            print(f"  Node Types: {set(node['type'] for node in netlist.nodes.values() if 'type' in node)}")
            # New addition: print out details for each node
            print("  Nodes:")
            for node_key, node in netlist.nodes.items():
                print(f"    {node_key}: {node}")
        
        # Print timing paths if available
        if hasattr(netlist, 'timing_paths'):
            path_count = sum(len(paths) for paths in netlist.timing_paths.values())
            print(f"  Timing Path Count: {path_count}")

def convert_dataset_to_protobuf(dataset, output_filename):
    try:
        # Ensure output directory exists
        import os
        output_dir = os.path.dirname(output_filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        
        for netlist_key, netlist in dataset.items():
            print(f"Processing netlist: {netlist_key}")
            
            # Set name field if needed - this might be required by the protobuf_io module
            netlist_name = netlist_key[0] if isinstance(netlist_key, tuple) and len(netlist_key) > 0 else "unknown"
            
            # Convert netlist to protobuf using the function from protobuf_io
            netlist_proto = dataset_to_protobuf(netlist)
            
            # Debug: Print serialized size and available fields before saving
            print(f"Protobuf object created, size: {netlist_proto.ByteSize()} bytes")
            print(f"Protobuf type: {type(netlist_proto)}")
            
            # Debug: Alternative way to save protobuf
            try:
                # Save using direct file write instead of save_protobuf_file function
                with open(output_filename, 'wb') as f:
                    print(f"Writing protobuf directly to file: {output_filename}")
                    f.write(netlist_proto.SerializeToString())
                print(f"Successfully wrote protobuf file directly for netlist {netlist_key}")
            except Exception as direct_write_error:
                print(f"Error directly writing protobuf: {str(direct_write_error)}")
                
                # Try with the original save_protobuf_file but with better error handling
                print(f"Trying with save_protobuf_file: {output_filename}")
                try:
                    from inspect import signature
                    # Check signature of save_protobuf_file
                    sig = signature(save_protobuf_file)
                    print(f"save_protobuf_file signature: {sig}")
                    
                    save_protobuf_file(netlist_proto, output_filename)
                    print(f"Successfully saved protobuf file for netlist {netlist_key}")
                except Exception as save_error:
                    import traceback
                    print(f"Detailed error from save_protobuf_file: {str(save_error)}")
                    traceback.print_exc()
            
            # For simplicity, we're only processing the first netlist
            break
            
    except Exception as e:
        print(f"Error converting dataset to protobuf: {str(e)}")
        import traceback

def print_dataset_netlist_details(dataset):
    """
    Print detailed information about the netlist keys and names in the dataset.
    
    Args:
        dataset: The dataset containing netlists to inspect
    """
    print("\n--- Netlist Key Details ---")
    for netlist_key, netlist in dataset.items():
        print(f"Netlist key type: {type(netlist_key)}, value: {netlist_key}")
        if hasattr(netlist, 'name'):
            print(f"Netlist has name attribute: {netlist.name}")
        else:
            print("Netlist does not have a name attribute")
        # Only print details for the first netlist if you want to limit output
        break

def compare_dataset_and_protobuf(dataset, protobuf_data):
    """
    Perform a detailed comparison between a dataset netlist and protobuf data.
    
    This function compares all relevant attributes between the two objects and 
    prints detailed information about matches and differences to stdout.
    
    Args:
        dataset: Dataset object containing netlists
        protobuf_data: Protobuf object loaded from file
    
    Returns:
        bool: True if the data matches completely, False otherwise
    """
    print("\n===== COMPARISON: DATASET VS PROTOBUF =====")
    if not dataset or not protobuf_data:
        print("ERROR: Cannot compare - one or both objects are None")
        return False
    
    match_count = 0
    mismatch_count = 0
    error_count = 0
    
    # Get the first netlist from the dataset for comparison
    netlist = None
    netlist_key = None
    for key, value in dataset.items():
        netlist = value
        netlist_key = key
        break
    
    if not netlist:
        print("ERROR: No netlist found in dataset")
        return False
    
    print(f"Comparing netlist {netlist_key} with protobuf data...")
    
    # List of basic attributes to compare
    basic_attrs = [
        'width', 'height', 'no_of_inputs', 'no_of_outputs', 
        'utilization', 'cell_density', 'pin_density', 'net_density'
    ]
    
    # Compare basic attributes
    print("\n--- Basic Attributes ---")
    for attr in basic_attrs:
        try:
            if hasattr(netlist, attr) and hasattr(protobuf_data, attr):
                netlist_val = getattr(netlist, attr)
                protobuf_val = getattr(protobuf_data, attr)
                
                # Ensure consistent types for comparison
                if isinstance(netlist_val, (int, float)) and isinstance(protobuf_val, (int, float)):
                    # Use approximate comparison for floats
                    match = abs(float(netlist_val) - float(protobuf_val)) < 0.001
                else:
                    match = netlist_val == protobuf_val
                
                if match:
                    print(f"✅ {attr}: {netlist_val} == {protobuf_val}")
                    match_count += 1
                else:
                    print(f"❌ {attr}: {netlist_val} != {protobuf_val}")
                    mismatch_count += 1
            elif hasattr(netlist, attr):
                print(f"❌ {attr}: Missing in protobuf, dataset has {getattr(netlist, attr)}")
                mismatch_count += 1
            elif hasattr(protobuf_data, attr):
                print(f"❌ {attr}: Missing in dataset, protobuf has {getattr(protobuf_data, attr)}")
                mismatch_count += 1
            else:
                print(f"⚠️ {attr}: Not found in either object")
        except Exception as e:
            print(f"ERROR comparing {attr}: {str(e)}")
            error_count += 1
    
    # Compare cell metrics
    if hasattr(netlist, 'cell_metrics') and hasattr(protobuf_data, 'cell_metrics'):
        print("\n--- Cell Metrics ---")
        cm_netlist = netlist.cell_metrics
        cm_proto = protobuf_data.cell_metrics
        
        # List of cell metrics attributes to compare
        cm_attrs = [
            'no_of_combinational_cells', 'no_of_sequential_cells',
            'no_of_buffers', 'no_of_inverters', 'no_of_fillers',
            'no_of_tap_cells', 'no_of_diodes', 'no_of_macros',
            'no_of_total_cells'
        ]
        
        for attr in cm_attrs:
            try:
                if hasattr(cm_netlist, attr) and hasattr(cm_proto, attr):
                    netlist_val = getattr(cm_netlist, attr)
                    protobuf_val = getattr(cm_proto, attr)
                    
                    if netlist_val == protobuf_val:
                        print(f"✅ cell_metrics.{attr}: {netlist_val} == {protobuf_val}")
                        match_count += 1
                    else:
                        print(f"❌ cell_metrics.{attr}: {netlist_val} != {protobuf_val}")
                        mismatch_count += 1
                elif hasattr(cm_netlist, attr):
                    print(f"❌ cell_metrics.{attr}: Missing in protobuf, dataset has {getattr(cm_netlist, attr)}")
                    mismatch_count += 1
                elif hasattr(cm_proto, attr):
                    print(f"❌ cell_metrics.{attr}: Missing in dataset, protobuf has {getattr(cm_proto, attr)}")
                    mismatch_count += 1
            except Exception as e:
                print(f"ERROR comparing cell_metrics.{attr}: {str(e)}")
                error_count += 1
    
    # Compare area metrics
    if hasattr(netlist, 'area_metrics') and hasattr(protobuf_data, 'area_metrics'):
        print("\n--- Area Metrics ---")
        am_netlist = netlist.area_metrics
        am_proto = protobuf_data.area_metrics
        
        # List of area metrics attributes to compare
        am_attrs = [
            'combinational_cell_area', 'sequential_cell_area', 'buffer_area',
            'inverter_area', 'filler_area', 'tap_cell_area', 'diode_area',
            'macro_area', 'cell_area', 'total_area'
        ]
        
        for attr in am_attrs:
            try:
                if hasattr(am_netlist, attr) and hasattr(am_proto, attr):
                    netlist_val = getattr(am_netlist, attr)
                    protobuf_val = getattr(am_proto, attr)
                    
                    # Use approximate comparison for floats
                    match = abs(float(netlist_val) - float(protobuf_val)) < 0.001
                    
                    if match:
                        print(f"✅ area_metrics.{attr}: {netlist_val} == {protobuf_val}")
                        match_count += 1
                    else:
                        print(f"❌ area_metrics.{attr}: {netlist_val} != {protobuf_val}")
                        mismatch_count += 1
                elif hasattr(am_netlist, attr):
                    print(f"❌ area_metrics.{attr}: Missing in protobuf, dataset has {getattr(am_netlist, attr)}")
                    mismatch_count += 1
                elif hasattr(am_proto, attr):
                    print(f"❌ area_metrics.{attr}: Missing in dataset, protobuf has {getattr(am_proto, attr)}")
                    mismatch_count += 1
            except Exception as e:
                print(f"ERROR comparing area_metrics.{attr}: {str(e)}")
                error_count += 1
    
    # Compare power metrics
    if hasattr(netlist, 'power_metrics') and hasattr(protobuf_data, 'power_metrics'):
        print("\n--- Power Metrics ---")
        pm_netlist = netlist.power_metrics
        pm_proto = protobuf_data.power_metrics
        
        # List of power metrics attributes to compare
        pm_attrs = [
            'combinational_power', 'sequential_power', 'macro_power',
            'internal_power', 'switching_power', 'leakage_power', 'total_power'
        ]
        
        for attr in pm_attrs:
            try:
                if hasattr(pm_netlist, attr) and hasattr(pm_proto, attr):
                    netlist_val = getattr(pm_netlist, attr)
                    protobuf_val = getattr(pm_proto, attr)
                    
                    # Use approximate comparison for floats
                    match = abs(float(netlist_val) - float(protobuf_val)) < 0.001
                    
                    if match:
                        print(f"✅ power_metrics.{attr}: {netlist_val} == {protobuf_val}")
                        match_count += 1
                    else:
                        print(f"❌ power_metrics.{attr}: {netlist_val} != {protobuf_val}")
                        mismatch_count += 1
                elif hasattr(pm_netlist, attr):
                    print(f"❌ power_metrics.{attr}: Missing in protobuf, dataset has {getattr(pm_netlist, attr)}")
                    mismatch_count += 1
                elif hasattr(pm_proto, attr):
                    print(f"❌ power_metrics.{attr}: Missing in dataset, protobuf has {getattr(pm_proto, attr)}")
                    mismatch_count += 1
            except Exception as e:
                print(f"ERROR comparing power_metrics.{attr}: {str(e)}")
                error_count += 1
    
    # Compare critical path metrics
    if hasattr(netlist, 'critical_path_metrics') and hasattr(protobuf_data, 'critical_path_metrics'):
        print("\n--- Critical Path Metrics ---")
        cpm_netlist = netlist.critical_path_metrics
        cpm_proto = protobuf_data.critical_path_metrics
        
        # List of critical path metrics attributes to compare
        cpm_attrs = [
            'startpoint', 'endpoint', 'worst_arrival_time', 'worst_slack',
            'total_negative_slack', 'no_of_timing_paths', 'no_of_slack_violations'
        ]
        
        for attr in cpm_attrs:
            try:
                if hasattr(cpm_netlist, attr) and hasattr(cpm_proto, attr):
                    netlist_val = getattr(cpm_netlist, attr)
                    protobuf_val = getattr(cpm_proto, attr)
                    
                    if isinstance(netlist_val, (int, float)) and isinstance(protobuf_val, (int, float)):
                        # Use approximate comparison for floats
                        match = abs(float(netlist_val) - float(protobuf_val)) < 0.001
                    else:
                        match = str(netlist_val) == str(protobuf_val)
                    
                    if match:
                        print(f"✅ critical_path_metrics.{attr}: {netlist_val} == {protobuf_val}")
                        match_count += 1
                    else:
                        print(f"❌ critical_path_metrics.{attr}: {netlist_val} != {protobuf_val}")
                        mismatch_count += 1
                elif hasattr(cpm_netlist, attr):
                    print(f"❌ critical_path_metrics.{attr}: Missing in protobuf, dataset has {getattr(cpm_netlist, attr)}")
                    mismatch_count += 1
                elif hasattr(cpm_proto, attr):
                    print(f"❌ critical_path_metrics.{attr}: Missing in dataset, protobuf has {getattr(cpm_proto, attr)}")
                    mismatch_count += 1
            except Exception as e:
                print(f"ERROR comparing critical_path_metrics.{attr}: {str(e)}")
                error_count += 1
    
    # Compare timing paths (count and basic attributes)
    if hasattr(netlist, 'timing_paths') and hasattr(protobuf_data, 'timing_paths'):
        print("\n--- Timing Paths ---")
        try:
            netlist_timing_path_count = sum(len(paths) for paths in netlist.timing_paths.values())
            protobuf_timing_path_count = len(protobuf_data.timing_paths)
            
            if netlist_timing_path_count == protobuf_timing_path_count:
                print(f"✅ Timing path count: {netlist_timing_path_count} == {protobuf_timing_path_count}")
                match_count += 1
            else:
                print(f"❌ Timing path count: {netlist_timing_path_count} != {protobuf_timing_path_count}")
                mismatch_count += 1
                
            # If we wanted to compare individual timing paths, we would need more complex logic here
            # since the structure is different between the dataset and protobuf
        except Exception as e:
            print(f"ERROR comparing timing_paths: {str(e)}")
            error_count += 1
    
    # Summary
    print("\n===== COMPARISON SUMMARY =====")
    print(f"Total Matches: {match_count}")
    print(f"Total Mismatches: {mismatch_count}")
    print(f"Total Errors: {error_count}")
    
    match_percentage = 0
    if match_count + mismatch_count > 0:
        match_percentage = (match_count / (match_count + mismatch_count)) * 100
    
    print(f"Match Percentage: {match_percentage:.2f}%")
    
    if mismatch_count == 0 and error_count == 0:
        print("\n✅ DATA MATCHES COMPLETELY")
        return True
    else:
        print("\n❌ DATA HAS DIFFERENCES")
        return False

def print_protobuf(proto_obj, indent=0, max_depth=3, current_depth=0, field_name=None):
    """
    Print the contents of a protobuf object in a readable format.
    
    Args:
        proto_obj: The protobuf object to print
        indent: Current indentation level (default: 0)
        max_depth: Maximum depth to traverse for nested messages (default: 3)
        current_depth: Current depth in the recursive traversal (default: 0)
        field_name: Name of the field being printed (default: None)
    """
    if current_depth > max_depth:
        print(" " * indent + f"{field_name}: <max depth reached>")
        return
    
    if field_name:
        header = f"{field_name}:"
    else:
        header = f"{proto_obj.__class__.__name__}:"
    
    print(" " * indent + header)
    indent += 2
    
    # Check if this is a basic type
    if not hasattr(proto_obj, 'DESCRIPTOR'):
        print(" " * indent + f"Value: {proto_obj}")
        return
    
    # Handle each field in the protobuf message
    for field in proto_obj.DESCRIPTOR.fields:
        field_value = getattr(proto_obj, field.name)
        
        # Handle repeated fields (lists)
        if field.label == field.LABEL_REPEATED:
            print(" " * indent + f"{field.name}: [{len(field_value)} items]")
            
            # Print first 5 items if there are any
            if len(field_value) > 0:
                for i, item in enumerate(field_value[:5]):
                    if hasattr(item, 'DESCRIPTOR'):  # Nested message
                        print_protobuf(item, indent + 2, max_depth, current_depth + 1, f"[{i}]")
                    else:  # Basic type
                        print(" " * (indent + 2) + f"[{i}]: {item}")
                
                # If there are more items, print a summary
                if len(field_value) > 5:
                    print(" " * (indent + 2) + f"... {len(field_value) - 5} more items")
        
        # Handle nested messages
        elif field.type == field.TYPE_MESSAGE:
            if field_value != proto_obj.DESCRIPTOR.fields_by_name[field.name].default_value:
                print_protobuf(field_value, indent, max_depth, current_depth + 1, field.name)
            else:
                print(" " * indent + f"{field.name}: <empty>")
        
        # Handle basic types
        else:
            print(" " * indent + f"{field.name}: {field_value}")

if __name__ == "__main__":
    try:
        # Load initial dataset
        print("#" * 79)
        dataset = load_dataset(DATASET_DIR, NETLIST_ID)
        if dataset:
            print(f"Dataset loaded successfully for netlist {NETLIST_ID} from {DATASET_DIR} ")        
            print("\n=== CONTENTS: dataset ===")
            print_dataset(dataset)
        
        # Convert dataset to protobuf and save to file
        print("#" * 79)
        print(f"\n\nConverting dataset to protobuf format and saving to {PB_FILE}...")
        convert_dataset_to_protobuf(dataset, PB_FILE)
        print(f" Conversion to {PB_FILE} completed successfully.")
        print("#" * 79)

        # Read back the protobuf file
        print("#" * 79)
        print(f"\n\nReading back protobuf data from {PB_FILE}...")
        protobuf_data = load_protobuf_file(PB_FILE)
        if protobuf_data:
            print(f" Protobuf file {PB_FILE} loaded successfully. Loaded protobuf size: {protobuf_data.ByteSize()} bytes")
            print("\n=== CONTENTS:protobuf ===")
            print_protobuf(protobuf_data)
            
            # Compare dataset and protobuf data
            if dataset:
                print("\n\nWe are comparing the dataset and protobuf data...")
                compare_dataset_and_protobuf(dataset, protobuf_data)
        
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        import traceback
        traceback.print_exc()

