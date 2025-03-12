import unittest
from unittest.mock import patch, MagicMock
from eda_schema.grpc_server import EDAService
from eda_schema.protobuf_io import load_protobuf_file, save_protobuf_file
from eda_schema.entity import NetlistEntity
from eda_schema.errors import ValidationError

class TestEDAService(unittest.TestCase):
    @patch('eda_schema.grpc_server.load_protobuf_file')
    @patch('eda_schema.grpc_server.ImportResponse')
    def test_import_from_protobuf_file_success(self, mock_import_response, mock_load_protobuf_file):
        mock_load_protobuf_file.return_value = NetlistEntity({"entity_id": "123"})
        mock_import_response.return_value = MagicMock()

        service = EDAService()
        request = MagicMock(file_path="test_path")
        context = MagicMock()

        response = service.ImportFromProtobufFile(request, context)

        mock_load_protobuf_file.assert_called_once_with("test_path")
        mock_import_response.assert_called_once_with(status="Success", entity_id="123")
        self.assertEqual(response, mock_import_response.return_value)

    @patch('eda_schema.grpc_server.load_protobuf_file')
    @patch('eda_schema.grpc_server.ImportResponse')
    def test_import_from_protobuf_file_failure(self, mock_import_response, mock_load_protobuf_file):
        mock_load_protobuf_file.side_effect = ValidationError("Invalid file")
        mock_import_response.return_value = MagicMock()

        service = EDAService()
        request = MagicMock(file_path="test_path")
        context = MagicMock()

        response = service.ImportFromProtobufFile(request, context)

        mock_load_protobuf_file.assert_called_once_with("test_path")
        mock_import_response.assert_called_once_with(status="Failed: Invalid file")
        self.assertEqual(response, mock_import_response.return_value)

    @patch('eda_schema.grpc_server.save_protobuf_file')
    @patch('eda_schema.grpc_server.fetch_from_eda_schema')
    @patch('eda_schema.grpc_server.ExportResponse')
    def test_export_to_protobuf_file_success(self, mock_export_response, mock_fetch_from_eda_schema, mock_save_protobuf_file):
        mock_fetch_from_eda_schema.return_value = NetlistEntity({"entity_id": "123"})
        mock_export_response.return_value = MagicMock()

        service = EDAService()
        request = MagicMock(entity_id="123", file_path="test_path")
        context = MagicMock()

        response = service.ExportToProtobufFile(request, context)

        mock_fetch_from_eda_schema.assert_called_once_with("123")
        mock_save_protobuf_file.assert_called_once_with(mock_fetch_from_eda_schema.return_value, "test_path")
        mock_export_response.assert_called_once_with(status="Success")
        self.assertEqual(response, mock_export_response.return_value)

    @patch('eda_schema.grpc_server.save_protobuf_file')
    @patch('eda_schema.grpc_server.fetch_from_eda_schema')
    @patch('eda_schema.grpc_server.ExportResponse')
    def test_export_to_protobuf_file_failure(self, mock_export_response, mock_fetch_from_eda_schema, mock_save_protobuf_file):
        mock_fetch_from_eda_schema.side_effect = ValidationError("Entity not found")
        mock_export_response.return_value = MagicMock()

        service = EDAService()
        request = MagicMock(entity_id="123", file_path="test_path")
        context = MagicMock()

        response = service.ExportToProtobufFile(request, context)

        mock_fetch_from_eda_schema.assert_called_once_with("123")
        mock_save_protobuf_file.assert_not_called()
        mock_export_response.assert_called_once_with(status="Failed: Entity not found")
        self.assertEqual(response, mock_export_response.return_value)

if __name__ == '__main__':
    unittest.main()