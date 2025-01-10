import os
import re
import yaml
from datetime import datetime
from collections import defaultdict

# Convert defaultdict to standard dict
def convert_to_dict(obj):
    if isinstance(obj, defaultdict):
        return {k: convert_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, dict):
        return {k: convert_to_dict(v) for k, v in obj.items()}
    else:
        return obj

def parse_log_file(file_path):
    """
    Parses the log file to extract timestamps, netlists, and phases.
    """
    log_entries = []
    log_pattern = (
        r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - .* - INFO - "
        r"Creating entity for netlist (?P<netlist>[\w\-]+) for phase (?P<phase>\w+)."
    )
    end_entries = []
    end_pattern = (
        r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - .* - INFO - "
        r"Netlist added to dataset\."
    )
    with open(file_path, 'r') as file:
        for line in file:
            match = re.match(log_pattern, line.strip())
            end_match = re.match(end_pattern, line.strip())
            if match:
                timestamp_str = match.group("timestamp")
                netlist = match.group("netlist")
                phase = match.group("phase")
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                log_entries.append((timestamp, netlist, phase))
            if end_match:
                timestamp_str = end_match.group("timestamp")
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                end_entries.append(timestamp)
    return log_entries, end_entries

def get_initialization_time(file_path):
    """
    Calculates the initialization time as the difference between the first log entry
    (e.g., 'Initializing OpenROADDataLoader') and the first netlist phase timestamp.
    """
    start_time = None
    first_netlist_time = None
    initialization_pattern = r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - .* - INFO - Initializing OpenROADDataLoader\."

    with open(file_path, 'r') as file:
        for line in file:
            if not start_time:
                match = re.match(initialization_pattern, line.strip())
                if match:
                    start_time = datetime.strptime(match.group("timestamp"), "%Y-%m-%d %H:%M:%S,%f")
            if not first_netlist_time and "Creating entity for netlist" in line:
                first_netlist_time = datetime.strptime(line.split(" - ")[0], "%Y-%m-%d %H:%M:%S,%f")
                break

    if start_time and first_netlist_time:
        return (first_netlist_time - start_time).total_seconds()
    else:
        raise ValueError("Initialization timestamps could not be found.")

def calculate_phase_durations(log_entries, end_entries):
    """
    Calculates the duration for each phase of each netlist.
    """
    durations = defaultdict(lambda: defaultdict(float))
    phase_start_times = {}
    entry_num = 0

    for entry in log_entries:
        timestamp, netlist, phase = entry
        key = (netlist, phase)
        phase_start_times[key] = timestamp
        duration = (end_entries[entry_num] - phase_start_times[key]).total_seconds()
        durations[netlist][phase] = duration
        entry_num += 1
    return durations

def calculate_total_time(durations):
    """
    Calculates the total time for each netlist.
    """
    total_times = {}
    for netlist, phases in durations.items():
        total_times[netlist] = sum(phases.values())
    return total_times

def calculate_total_time_by_type(total_times):
    """
    Calculates the total time spent on each netlist type.
    """
    type_totals = defaultdict(float)
    for netlist, total_time in total_times.items():
        netlist_type = netlist.split('-id-')[0]
        type_totals[netlist_type] += total_time
    return type_totals

def calculate_total_log_time(log_entries):
    """
    Calculates the total log time from the first to the last timestamp.
    """
    start_time = log_entries[0][0]
    end_time = log_entries[-1][0]
    total_log_time = (end_time - start_time).total_seconds()
    return total_log_time

def display_durations(initialization_time, durations, total_times, total_time_by_type, total_log_time):
    """
    Displays the calculated phase durations, total time for each netlist, and total log time.
    """
    print(f"\nInitialization Time: {initialization_time:.2f} seconds\n")

    for netlist_type, type_total_time in total_time_by_type.items():
        print(f"Total Time for Design '{netlist_type}': {type_total_time:.2f} seconds\n")
        for netlist, phases in durations.items():
            if netlist.startswith(netlist_type):
                print(f"  Design: {netlist}")
                for phase, duration in phases.items():
                    print(f"    {phase}: {duration:.2f} seconds")
                print(f"    Total Time: {total_times[netlist]:.2f} seconds\n")

    print(f"Total Log Time: {total_log_time:.2f} seconds")
    
def export_to_yaml(output_file, initialization_time, durations, total_times, total_time_by_type, total_log_time):
    """
    Exports the calculated results into a YAML file.
    Converts defaultdict to a standard dict for compatibility with YAML serialization.
    """
    # Prepare data for export
    data = {
        "Initialization Time (seconds)": initialization_time,
        "Netlists": {
            netlist: {
                "Phases": convert_to_dict(phases),
                "Total Time (seconds)": total_times[netlist]
            }
            for netlist, phases in durations.items()
        },
        "Total Time by Design Type (seconds)": convert_to_dict(total_time_by_type),
        "Total Log Time (seconds)": total_log_time
    }

    # Write to YAML file
    with open(output_file, 'w') as file:
        yaml.dump(data, file, default_flow_style=False)
    print(f"Results have been exported to {output_file}")
    
def calculate_file_sizes_by_netlist(directory):
    """
    Calculates the total file size for each netlist type in the given directory, 
    categorizing them into subcategories such as clock_trees, netlists, 
    netlists_without_timing_paths, and nets. Sizes are returned in MB.
    The total size per circuit is also calculated and included.
    """
    file_sizes = defaultdict(lambda: defaultdict(float))  # {netlist_type: {subcategory: total_size_in_MB}}

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.pkl'):
                # Extract the netlist type and subcategory from the file name
                parts = file.split('-')
                netlist_parts = parts[0].split('_')

                if len(parts) >= 2:
                    netlist_type = netlist_parts[-1]
                    # Handle cases where netlist type may consist of two parts
                    if len(netlist_parts) >= 2 and netlist_parts[-2] not in ["trees", "nets", "netlists", "paths"]:
                        netlist_type = "_".join([netlist_parts[-2], netlist_parts[-1]])

                    # Determine subcategory
                    if "clock_trees" in file:
                        subcategory = "clock_trees"
                    elif "netlists_without_timing_paths" in file:
                        subcategory = "netlists_without_timing_paths"
                    elif "netlists" in file:
                        subcategory = "netlists"
                    elif "nets" in file:
                        subcategory = "nets"
                    else:
                        continue  # Skip files that don't match known subcategories
                    
                    # Calculate file size in MB
                    file_path = os.path.join(root, file)
                    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    file_sizes[netlist_type][subcategory] += file_size_mb
                    file_sizes[netlist_type]["total_size"] += file_size_mb  # Update total size for the circuit

    return file_sizes


def export_file_sizes_to_yaml(file_sizes, output_yaml_path):
    """
    Exports the file size results into a YAML file.
    """
    
    cleaned_file_sizes = convert_to_dict(file_sizes)
    
    with open(output_yaml_path, 'w') as file:
        yaml.dump({"Netlist File Sizes (MB)": cleaned_file_sizes}, file, default_flow_style=False)
    print(f"File size data has been exported to {output_yaml_path}")


if __name__ == "__main__":
    # Path to the log file and yaml file
    log_file_path = "../openroad_dataloader_iwls05_sky130_openroad.log"
    directory_path = "../eda_schema_barelypass_subset_fixed/graph_dir"
    output_yaml_path = "../log_analysis_results.yaml"
    file_sizes_yaml_path = "../file_sizes_results.yaml"

    # Calculate initialization time
    initialization_time = get_initialization_time(log_file_path)

    # Parse the log file
    log_entries, end_entries = parse_log_file(log_file_path)

    # Calculate phase durations
    phase_durations = calculate_phase_durations(log_entries, end_entries)

    # Calculate total time for each netlist
    total_times = calculate_total_time(phase_durations)

    # Calculate total time by netlist type
    total_time_by_type = calculate_total_time_by_type(total_times)

    # Calculate total log time
    total_log_time = calculate_total_log_time(log_entries)

    # Display the results
    display_durations(initialization_time, phase_durations, total_times, total_time_by_type, total_log_time)
    export_to_yaml(output_yaml_path, initialization_time, phase_durations, total_times, total_time_by_type, total_log_time)
    
    # Calculate and export file sizes
    file_sizes = calculate_file_sizes_by_netlist(directory_path)
    export_file_sizes_to_yaml(file_sizes, file_sizes_yaml_path)
