import pytest
import os
from eda_schema.protobuf_io import load_protobuf_file, save_protobuf_file
from eda_schema import eda_schema_pb2 as pb2

class TestProtobufIO:

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmpdir):
        # Create a temporary file for testing
        self.test_file = tmpdir.join('test_protobuf_file.bin')
        self.entity = pb2.EntityMessage()
        self.entity.type = 'TestEntity'
        self.entity.some_field = 'some_value'
        yield
        # Teardown code (if any) goes here

    def test_save_protobuf_file(self):
        # Save the entity to a file
        save_protobuf_file(self.entity, str(self.test_file))

        # Check if the file was created
        assert os.path.exists(str(self.test_file))

    def test_load_protobuf_file(self):
        # Save the entity to a file first
        save_protobuf_file(self.entity, str(self.test_file))

        # Load the entity from the file
        loaded_entity = load_protobuf_file(str(self.test_file))

        # Check if the loaded entity matches the original entity
        assert loaded_entity.type == self.entity.type
        assert loaded_entity.some_field == self.entity.some_field
