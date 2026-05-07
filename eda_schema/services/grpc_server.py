
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : eda_schema/services/grpc_server.py
# Authors :
#     Pratik Shrestha       <ps937@drexel.edu>
#     Amit Varde            <avv39@drexel.edu>
#
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike
# 4.0 International License (CC BY-NC-SA 4.0). You may obtain a copy of the
# license at: https://creativecommons.org/licenses/by-nc-sa/4.0/
#
# This software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. Commercial use is
# expressly prohibited; derivative works must be shared under the same
# license terms (ShareAlike).

"""
gRPC server implementation for the EDA schema service.

This module implements the gRPC server for the EDA schema service.
It provides functionalities to import and export data using Protobuf files.

Classes:
    EDAService: Implements the gRPC service methods for importing and exporting data.

Methods:
    ImportFromProtobufFile: Handles import request for a given Protobuf file.
    ExportToProtobufFile: Handles export request for an entity ID.
"""

from eda_schema.proto.eda_schema_pb2 import (  # pylint: disable=no-name-in-module
    ExportResponse,
    ImportResponse,
)
from eda_schema.proto.eda_schema_pb2_grpc import EdaSchemaServiceServicer
from eda_schema.serialization.protobuf_io import load_protobuf_file, protobuf_to_dataset


class EDAService(EdaSchemaServiceServicer):
    """gRPC service implementation for EDA Schema operations."""

    def __init__(self, dataset=None):
        """
        Initialize the EDA service.

        Args:
            dataset: Optional Dataset instance for data operations.
        """
        self.dataset = dataset

    def ImportFromProtobufFile(
        self, request, context
    ):  # pylint: disable=invalid-name,unused-argument
        """
        Handles import request for a given Protobuf file.

        Args:
            request: ImportRequest containing file_path.
            context: gRPC context (required by interface).

        Returns:
            ImportResponse: Success status and message.
        """
        try:
            # Load protobuf file
            proto_entity = load_protobuf_file(request.file_path)

            # Convert proto to EDA entity
            protobuf_to_dataset(proto_entity)

            # Save to dataset if available
            if self.dataset:
                # TODO: Implement dataset save logic  # pylint: disable=fixme
                # For now, just return success
                pass

            return ImportResponse(success=True, message="Imported successfully")
        except (FileNotFoundError, ValueError, TypeError) as e:
            return ImportResponse(success=False, message=f"Failed: {str(e)}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors
            return ImportResponse(success=False, message=f"Failed: {str(e)}")

    def ExportToProtobufFile(
        self, request, context
    ):  # pylint: disable=invalid-name,unused-argument
        """
        Handles export request for an entity ID.

        Args:
            request: ExportRequest containing entity_id and file_path.
            context: gRPC context (required by interface).

        Returns:
            ExportResponse: Success status and message.
        """
        try:
            if not self.dataset:
                return ExportResponse(success=False, message="Dataset not available")

            # TODO: Implement proper entity fetching based on request.entity_id  # pylint: disable=fixme
            # For now, this is a placeholder
            # stage_entity = self.dataset.get_stage_entity(request.entity_id)
            # proto_entity = dataset_to_protobuf(self.dataset, stage_entity)
            # save_protobuf_file(proto_entity, request.file_path)

            return ExportResponse(success=False, message="Export not yet implemented")
        except (ValueError, AttributeError) as e:
            return ExportResponse(success=False, message=f"Failed: {str(e)}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors
            return ExportResponse(success=False, message=f"Failed: {str(e)}")
