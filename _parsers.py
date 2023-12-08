import re
import os

def area_parsing(report_path):
    with open(report_path) as fp:
        txt = fp.read()
    
    # Define regex patterns to match Design area line
    design_pattern = r"^Design area (.*?) u.*\n"
    
    # Find matches in the input text
    design_matches = re.findall(design_pattern, txt, re.MULTILINE)
    
    return float(design_matches[0])

def count_parsing(report_path):
    with open(report_path) as fp:
        txt = fp.read()
    values = []
    # Define regex patterns to match the desired lines
    pattern_instance_count = r"leaf instance count\n-{10,}\n(\d+)"
    pattern_pin_count = r"leaf pin count\n-{10,}\n(\d+)"

    # Find matches for "leaf instance count" and "leaf pin count" lines
    instance_count_match = re.findall(pattern_instance_count, txt)
    pin_count_match = re.findall(pattern_pin_count, txt)
    values.append(instance_count_match[0])
    values.append(pin_count_match[0])
    
    return values

def power_parsing(report_path):
    """Parse Synopsys ICC power reports
    Parameters
    ----------
    report_path : str
        Power report file path
    Returns
    ----------
    dict
        Parsed power metrics
    """
    with open(report_path) as fp:
        txt = fp.read()

    split_list = txt.split("-" * 98)
    power_txt = split_list[0]

    block_names = ["Internal", "Switching", "Leakage", "Total"]
    data = {}

    # for block_name in block_names:
    regex = r"([a-zA-Z_]+)\s+([\d.e+-]+)\s+([\d.e+-]+)\s+([\d.e+-]+)\s+([\d.e+-]+)"
    for power_group, internal, switching, leakage, total in re.findall(regex, power_txt):
        power_group = power_group.lower()
        data["internal_" + power_group] =  float(internal)
        data["switching_" + power_group] =  float(switching)
        data["leakage_" + power_group] = float(leakage)
        data["total_" + power_group] = float(total)

    return data


def parse_timing_report(report_path):

    with open(report_path) as fp:
        txt = fp.read()
        
    data_dict = {}
    for match_str in re.findall(r"Startpoint.*?slack.*?\n", txt, re.DOTALL):
        path_info_dict = dict(re.findall(r"\s*(.+?): (.+?)\n", match_str))
        startpoint = path_info_dict["Startpoint"].split(" ")[0]
        endpoint = path_info_dict["Endpoint"].split(" ")[0]

        path_str_match = re.findall(r"Path\s+Group: .+?\n(.+?)(?=-{80,}|$)", match_str, re.DOTALL)[0]
        path_lines = path_str_match.strip().replace("rise edge", "rise_edge").split("\n")
        
        # Extract and process the table lines
        arrival_time_data, required_time_data = [], []
        arrival_time_in_progress = True
        for line in path_lines:
            values = line.split()
            if len(values) >= 2 and values[0] != "Path" and values[0] != "Cap":
                char_index = next((index for index, element in enumerate(values) if isinstance(element, str) and (not element.replace('.', '', 1).lstrip('-').isdigit())), None)
                if values[char_index:][0].startswith("slack"):
                    continue

                time = float(values[char_index - 1])
                delay = 0.0 if char_index == 1 else float(values[char_index - 2])
                slew = 0.0 if char_index <= 2 else float(values[char_index - 3])

                description = " ".join(values[char_index:])
                is_rise_transition = True if description[0] == "^" else False
                is_fall_transition = True if description[0] == "v" else False

                if arrival_time_in_progress:
                    arrival_time_data.append((delay, time, slew, is_rise_transition, is_fall_transition, description))
                else:
                    required_time_data.append((delay, time, slew, is_rise_transition, is_fall_transition, description))

                if description == "data arrival time":
                    arrival_time_in_progress = False
        
        slack = float(re.findall(r"(-?\d+\.\d+)\s+slack", match_str)[0])

        # if (startpoint, endpoint) not in data_dict:
        data_dict[(startpoint, endpoint)] = {
            "arrival_time_data": arrival_time_data,
            "required_time_data": required_time_data,
            "slack": slack,
        }
        # else:
        #     data_dict[(startpoint, endpoint)]["table_data"].extend(table_data)
    
    return data_dict

def parse_timing_path(path_str):
    arrival_time_path = []
    required_time_path = []
    path_lines = path_str.strip().split("\n")
    
    for line in path_lines[2:]:  # Skip the header lines
        values = line.split()
        if len(values) >= 5:
            arrival_time_path.append(float(values[3]))
            required_time_path.append(float(values[4]))
    
    return arrival_time_path, required_time_path

parse_timing_report("/mnt/networkresearchdata/savrsch_shared/datasets/i2c/id-000001/openroad/reports/route_timing_max.rpt")