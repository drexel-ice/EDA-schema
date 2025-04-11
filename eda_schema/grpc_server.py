"""
grpc_server.py

This module implements the gRPC server for the EDA schema service.
It provides functionalities to import and export data using Protobuf files.

Classes:
    EDAService: Implements the gRPC service methods for importing and exporting data.

Methods:
    ImportFromProtobufFile: Handles import request for a given Protobuf file.
    ExportToProtobufFile: Handles export request for an entity ID.

Changes:
    - Updated exception handling in ExportToProtobufFile to return ImportResponse on failure.
"""
from eda_schema.eda_schema_pb2 import ImportResponse, ExportResponse
from eda_schema.eda_schema_pb2_grpc import EDAServiceServicer
from eda_schema.protobuf_io import load_protobuf_file, save_protobuf_file

class EDAService(EDAServiceServicer):
    def ImportFromProtobufFile(self, request, context):
        """Handles import request for a given Protobuf file."""
        try:
            entity = load_protobuf_file(request.file_path)
            return ImportResponse(success=True, message=entity.entity_id)
        except Exception as e:
            return ImportResponse(success=False, message=f"Failed: {str(e)}")

    def ExportToProtobufFile(self, request, context):
        """Handles export request for an entity ID."""
        try:
            entity = load_protobuf_file(request.entity_id)
            save_protobuf_file(entity, request.file_path)
            return ExportResponse(success=True, message="Success")
        except Exception as e:
            return ImportResponse(success=False, message=f"Failed: {str(e)}")