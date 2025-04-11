import pytest
from unittest.mock import MagicMock, patch
from eda_schema.grpc_server import EDAService, ImportResponse, ExportResponse
"""
This script contains unit tests for the gRPC server implementation in the `eda_schema` module.
The gRPC server provides functionality to import and export data to and from protobuf files.

The tests are written using the `pytest` framework and utilize `unittest.mock` for mocking
dependencies. The following functionalities are tested:

1. `ImportFromProtobufFile`:
    - Tests the successful import of an entity from a valid protobuf file.
    - Tests the failure scenario when the file path is invalid or an exception occurs.

2. `ExportToProtobufFile`:
    - Tests the successful export of an entity to a valid protobuf file.
    - Tests the failure scenario when the entity cannot be fetched or an exception occurs.

Fixtures:
- `grpc_service`: Provides an instance of the `EDAService` class for testing.

Mocked Functions:
- `load_protobuf_file`: Simulates loading an entity from a protobuf file.
- `fetch_from_eda_schema`: Simulates fetching an entity from the EDA schema.
- `save_protobuf_file`: Simulates saving an entity to a protobuf file.

These tests ensure the robustness of the gRPC server by verifying its behavior under
both normal and exceptional conditions.
"""
@pytest.fixture
def grpc_service():
    return EDAService()

def test_import_from_protobuf_file_success(grpc_service):
    request = MagicMock()
    request.file_path = "valid_path"
    entity = MagicMock()
    entity.entity_id = "12345"

    with patch('eda_schema.grpc_server.load_protobuf_file', return_value=entity):
        response = grpc_service.ImportFromProtobufFile(request, MagicMock())
        assert response.success is True
        assert response.message == "12345"

def test_import_from_protobuf_file_failure(grpc_service):
    request = MagicMock()
    request.file_path = "invalid_path"

    with patch('eda_schema.grpc_server.load_protobuf_file', side_effect=Exception("File not found")):
        response = grpc_service.ImportFromProtobufFile(request, MagicMock())
        assert response.success is False
        assert "File not found" in response.message

def test_export_to_protobuf_file_success(grpc_service):
    request = MagicMock()
    request.entity_id = "12345"
    request.file_path = "valid_path"
    entity = MagicMock()

    with patch('eda_schema.grpc_server.load_protobuf_file', return_value=entity):
        with patch('eda_schema.grpc_server.save_protobuf_file'):
            response = grpc_service.ExportToProtobufFile(request, None)
            assert response.success is True
            assert response.message == "Success"

def test_export_to_protobuf_file_failure(grpc_service):
    request = MagicMock()
    request.entity_id = "12345"
    request.file_path = "invalid_path"

    with patch('eda_schema.grpc_server.load_protobuf_file', side_effect=Exception("Entity not found")):
        response = grpc_service.ExportToProtobufFile(request, None)
        assert response.success is False
        assert "Failed: Entity not found" in response.message
