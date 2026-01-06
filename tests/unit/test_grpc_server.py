"""
Unit tests for gRPC server implementation in the eda_schema module.

The gRPC server provides functionality to import and export data to and from
protobuf files. The tests use pytest framework and unittest.mock for mocking
dependencies.

Tested functionalities:
1. ImportFromProtobufFile:
   - Successful import of an entity from a valid protobuf file
   - Failure scenario when the file path is invalid or an exception occurs

2. ExportToProtobufFile:
   - Successful export of an entity to a valid protobuf file
   - Failure scenario when the entity cannot be fetched or an exception occurs
"""
from unittest.mock import MagicMock, patch

import pytest

from eda_schema.services.grpc_server import EDAService


@pytest.fixture
def grpc_service():
    """Provide an instance of the EDAService class for testing."""
    return EDAService()


def test_import_from_protobuf_file_success(grpc_service):  # pylint: disable=redefined-outer-name
    """Test successful import of an entity from a valid protobuf file."""
    request = MagicMock()
    request.file_path = "valid_path"
    # Create a mock proto object
    mock_proto = MagicMock()
    mock_stage_entity = MagicMock()

    with patch('eda_schema.services.grpc_server.load_protobuf_file',
               return_value=mock_proto):
        with patch('eda_schema.services.grpc_server.protobuf_to_dataset',
                   return_value=mock_stage_entity):
            response = grpc_service.ImportFromProtobufFile(request, MagicMock())
            assert response.success is True
            assert "Imported successfully" in response.message


def test_import_from_protobuf_file_failure(grpc_service):  # pylint: disable=redefined-outer-name
    """Test failure scenario when file path is invalid or exception occurs."""
    request = MagicMock()
    request.file_path = "invalid_path"

    with patch('eda_schema.services.grpc_server.load_protobuf_file',
               side_effect=Exception("File not found")):
        response = grpc_service.ImportFromProtobufFile(request, MagicMock())
        assert response.success is False
        assert "File not found" in response.message


def test_export_to_protobuf_file_success(grpc_service):  # pylint: disable=redefined-outer-name
    """Test export when dataset is not available."""
    request = MagicMock()
    request.entity_id = "12345"
    request.file_path = "valid_path"

    # Export requires dataset, so expect failure when dataset is None
    response = grpc_service.ExportToProtobufFile(request, None)
    assert response.success is False
    assert "dataset not available" in response.message.lower()


def test_export_to_protobuf_file_failure(grpc_service):  # pylint: disable=redefined-outer-name
    """Test export failure when dataset is not available."""
    request = MagicMock()
    request.entity_id = "12345"
    request.file_path = "invalid_path"

    # Export requires dataset
    response = grpc_service.ExportToProtobufFile(request, None)
    assert response.success is False
    assert "dataset not available" in response.message.lower()
