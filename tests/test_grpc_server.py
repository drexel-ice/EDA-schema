import pytest
from unittest.mock import MagicMock, patch
from eda_schema.grpc_server import EDAService, ImportResponse, ExportResponse

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
        assert response.status == "Success"
        assert response.entity_id == "12345"

def test_import_from_protobuf_file_failure(grpc_service):
    request = MagicMock()
    request.file_path = "invalid_path"

    with patch('eda_schema.grpc_server.load_protobuf_file', side_effect=Exception("File not found")):
        response = grpc_service.ImportFromProtobufFile(request, MagicMock())
        assert response.status == "Failed: File not found"

def test_export_to_protobuf_file_success(grpc_service):
    request = MagicMock()
    request.entity_id = "12345"
    request.file_path = "valid_path"
    entity = MagicMock()

    with patch('eda_schema.grpc_server.fetch_from_eda_schema', return_value=entity):
        with patch('eda_schema.grpc_server.save_protobuf_file') as mock_save:
            response = grpc_service.ExportToProtobufFile(request, MagicMock())
            mock_save.assert_called_once_with(entity, "valid_path")
            assert response.status == "Success"

def test_export_to_protobuf_file_failure(grpc_service):
    request = MagicMock()
    request.entity_id = "12345"
    request.file_path = "invalid_path"

    with patch('eda_schema.grpc_server.fetch_from_eda_schema', side_effect=Exception("Entity not found")):
        response = grpc_service.ExportToProtobufFile(request, MagicMock())
        assert response.status == "Failed: Entity not found"