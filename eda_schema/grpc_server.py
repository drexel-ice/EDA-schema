"""
grpc_server.py

This module implements the gRPC server for the EDA schema service.
It provides functionalities to import and export data using Protobuf files.

Classes:
    EDAService: Implements the gRPC service methods for importing and exporting data.

Methods:
    ImportFromProtobufFile: Handles import request for a given Protobuf file.
    ExportToProtobufFile: Handles export request for an entity ID.
"""
from eda_schema.eda_schema_pb2 import ImportResponse, ExportResponse
from eda_schema.eda_schema_pb2_grpc import EDAServiceServicer
class EDAService(EDAServiceServicer):
    def ImportFromProtobufFile(self, request, context):
        """Handles import request for a given Protobuf file."""
        try:
            entity = load_protobuf_file(request.file_path)
            return ImportResponse(status="Success", entity_id=entity.entity_id)
        except Exception as e:
            return ImportResponse(status=f"Failed: {str(e)}")

    def ExportToProtobufFile(self, request, context):
        """Handles export request for an entity ID."""
        try:
            entity = fetch_from_eda_schema(request.entity_id)
            save_protobuf_file(entity, request.file_path)
            return ExportResponse(status="Success")
        except Exception as e:
            return ExportResponse(status=f"Failed: {str(e)}")