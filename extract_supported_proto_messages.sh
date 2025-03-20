#!/bin/bash
# This script extracts the names of all protocol buffer message types
# defined in the specified .proto file and outputs them as a Python-style list.
# THis script is mainly for imporving developer experience and may not be exported to the world when we release the updated eda schema.
# =============================================================================
# USAGE: 
#   Run this script from the root of the repository containing the .proto file.
# WHEN TO RUN: 
#   This script should be run whenever there is a change to the proto file (messages).
#   Perhaps we should also add something for when services are added.
#   DO THAT WHEN you add a test to handle such cases.
# The output of this file is 
#   This script is used to generate a list of all message types defined in the .proto file.
#   This list is used in the test cases to verify that all messages are handled correctly
#   Python-style list of all message names extracted from the .proto file.
# PROTO_MESSAGES = [
#     "Empty",
#     "EdgeEntity",
#     "StandardCellEntity",
#     "GateEntity",
#     "IOPortEntity",
#     "InterconnectSegmentEntity",
#     "InterconnectEntity",
#     "TimingPathNodeEntity",
#     "TimingPathEntity",
#     "CellMetricsEntity",
#     "AreaMetricsEntity",
#     "PowerMetricsEntity",
#     "CriticalPathMetricsEntity",
#     "ClockTreeEntity",
#     "NetlistEntity",
#     "EntityMessage",
#     "ImportRequest",
#     "ImportResponse",
#     "ExportRequest",
#     "ExportResponse",
# ]
# WHY TO RUN:
#  When ever you are updating the test_proto.py file, you need to run this script to update the PROTO_MESSAGES li
#  This will give you a list of messages that need to be updated in the test_proto.py file.
# FUTUREWORK:
#  Perhaps we need to do something similar for services as well.
# =============================================================================

PROTO_FILE="protos/eda_schema.proto"
[[ -f "$PROTO_FILE" ]] || { echo "Error: File '$PROTO_FILE' does not exist."; exit 1; }

# Extract message names
echo "PROTO_MESSAGES = ["
grep -o 'message [a-zA-Z_][a-zA-Z0-9_]*' "$PROTO_FILE" | awk '{print $2}' | while read -r message; do
    echo "  \"$message\","
done
echo "]"