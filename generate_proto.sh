# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Script  : generate_proto.sh
# Authors : Pratik Shrestha <ps937@drexel.edu>, Amit Varde <avv39@drexel.edu>
#
# Licensed under CC BY-NC-SA 4.0. See LICENCE for full terms.
# Non-commercial use only; ShareAlike required for derivative works.

#!/bin/bash

# =============================================================================
# Script: generate_proto.sh
# Purpose:
#   Compile Protocol Buffers (.proto) definitions and generate Python classes
#   and gRPC service stubs for the EDA Schema project.
#
# WHEN to run:
#   - Whenever eda_schema.proto is modified (e.g., adding/removing message fields, services).
#   - If you delete or modify generated Python files like eda_schema_pb2.py or eda_schema_pb2_grpc.py.
#
# WHY to run:
#   - To reflect the latest .proto schema changes into Python code used by gRPC server/client.
#   - Ensures gRPC services and message structures are up-to-date and synchronized with proto definitions.
#
# Usage:
#   ./generate_proto.sh
#
# Main Command :
#   python -m grpc_tools.protoc \
#       --proto_path=. \
#       --python_out=./eda_schema \
#       --grpc_python_out=./eda_schema \
#       protos/eda_schema.proto
#
# What it does:
#   - Reads: 
#       ./protos/eda_schema.proto          # Proto file defining messages & services
#   - Writes:
#       ./eda_schema/proto/eda_schema_pb2.py     # Generated Python message classes
#       ./eda_schema/proto/eda_schema_pb2_grpc.py# Generated gRPC service classes
#
# Expected Project Structure:
#   /eda-schema-internal/
#   ├── eda_schema/
#   │   ├── proto/
#   │   │   ├── eda_schema_pb2.py  [output file]
#   │   │   └── eda_schema_pb2_grpc.py [output file]
#   │   └── (other source files)
#   ├── protos/
#   │   └── eda_schema.proto
#   └── generate_proto.sh
# =============================================================================


# Clean all .pyc files and __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -exec rm -f {} +
echo "Cleaned all .pyc files and __pycache__ directories."

PROTO_PATH="./protos"
PROTO_DIR="eda_schema/proto"
PROTO_FILE="eda_schema.proto"

  # List the existing files before regeneration
echo "The following files will be regenerated:"
if [[ -f ./${PROTO_DIR}/eda_schema_pb2.py && -f ./${PROTO_DIR}/eda_schema_pb2_grpc.py ]]; then
  echo "SHA sums of existing files:"
  SHA_SUM_PB2=$(sha256sum ./${PROTO_DIR}/eda_schema_pb2.py | awk '{print $1}')
  SHA_SUM_PB2_GRPC=$(sha256sum ./${PROTO_DIR}/eda_schema_pb2_grpc.py | awk '{print $1}')
  echo " eda_schema_pb2.py: $SHA_SUM_PB2"
  echo " eda_schema_pb2_grpc.py: $SHA_SUM_PB2_GRPC"
  # Delete the existing files before regeneration
  echo "Deleting existing files:"
  rm -f ./${PROTO_DIR}/eda_schema_pb2.py ./${PROTO_DIR}/eda_schema_pb2_grpc.py
  echo "Deleted eda_schema_pb2.py and eda_schema_pb2_grpc.py."
else
  echo "Error!: Files do not exist yet."
fi

echo "Regenerating gRPC Python files with proto3 optional support..."
echo "python -m grpc_tools.protoc --proto_path=${PROTO_PATH} --experimental_allow_proto3_optional --python_out=./${PROTO_DIR} --grpc_python_out=./${PROTO_DIR} ${PROTO_FILE}"
python -m grpc_tools.protoc \
  --proto_path=${PROTO_PATH} \
  --experimental_allow_proto3_optional \
  --python_out=./${PROTO_DIR} \
  --grpc_python_out=./${PROTO_DIR} \
  ${PROTO_FILE}

# Check if the command was successful
[[ $? -ne 0 ]] && { echo "Error: Failed to generate gRPC Python files."}


# List the newly generated files after regeneration
echo "Files regenerated:"
if [[ -f ./${PROTO_DIR}/eda_schema_pb2.py && -f ./${PROTO_DIR}/eda_schema_pb2_grpc.py ]]; then
  echo "Auto-Patching the Generated File because Python thinks eda_schema_pb2 is a top-level module, not part of the eda_schema package."
  sed -i 's/^import eda_schema_pb2/from . import eda_schema_pb2/' eda_schema/proto/eda_schema_pb2_grpc.py
  echo "SHA sums of newly generated files:"
  NEW_SHA_SUM_PB2=$(sha256sum ./${PROTO_DIR}/eda_schema_pb2.py | awk '{print $1}')
  NEW_SHA_SUM_PB2_GRPC=$(sha256sum ./${PROTO_DIR}/eda_schema_pb2_grpc.py | awk '{print $1}')
  echo " eda_schema_pb2.py: $NEW_SHA_SUM_PB2"
  echo " eda_schema_pb2_grpc.py: $NEW_SHA_SUM_PB2_GRPC"
else
  echo "Error: Generated files are missing."
fi
echo "gRPC Python files generated successfully!"
# Display detailed information about the newly generated files
echo "Detailed information of the newly generated files:"
ls -l ./${PROTO_DIR}/eda_schema_pb2.py
ls -l ./${PROTO_DIR}/eda_schema_pb2_grpc.py
[[ "$SHA_SUM_PB2" == "$NEW_SHA_SUM_PB2" ]] && echo " eda_schema_pb2.py: No change detected." || echo " eda_schema_pb2.py: File Updated."
[[ "$SHA_SUM_PB2_GRPC" == "$NEW_SHA_SUM_PB2_GRPC" ]] && echo " eda_schema_pb2_grpc.py: No change detected." || echo " eda_schema_pb2_grpc.py: File Updated."