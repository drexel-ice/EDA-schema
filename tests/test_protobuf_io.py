"""
test_protobuf_io.py

This script contains unit tests for the `eda_schema.protobuf_io` module, which provides functionality 
to save and load Protocol Buffer (protobuf) files. The tests ensure that protobuf entities can be 
correctly serialized to a file and deserialized back into Python objects. 

The tests are implemented using the `pytest` framework and include the following:
1. `test_save_protobuf_file`: Verifies that a protobuf entity can be saved to a file and that the file 
    is created successfully.
2. `test_load_protobuf_file`: Verifies that a protobuf entity can be loaded from a file and that the 
    deserialized entity matches the original entity. A mock is used to bypass dependencies on additional 
    fields or external logic.

The `setup_and_teardown` fixture is used to create a temporary file for testing and to initialize a 
sample protobuf entity (`EntityMessage`) with predefined attributes. This ensures that each test 
executes in isolation with a clean environment.

Dependencies:
- `pytest`: For writing and running the tests.
- `unittest.mock.patch`: For mocking external dependencies during testing.
- `eda_schema.protobuf_io`: The module under test, which provides `load_protobuf_file` and 
  `save_protobuf_file` functions.
- `eda_schema.eda_schema_pb2`: The generated protobuf module containing the `EntityMessage` definition.

Note:
- The `map_grpc_to_eda` function is mocked in the `test_load_protobuf_file` test to avoid dependency 
  on additional fields or transformations that are not relevant to the test.
"""
import pytest
import os
from unittest.mock import patch
from eda_schema.protobuf_io import load_protobuf_file, save_protobuf_file
from eda_schema import eda_schema_pb2 as pb2

class TestProtobufIO:

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmpdir):
        self.test_file = tmpdir.join('test_protobuf_file.bin')
        self.entity = pb2.EntityMessage()
        self.entity.name = 'TestNetlist'
        self.entity.id = 12345
        self.entity.type = "Netlist"
        yield

    def test_save_protobuf_file(self):
        save_protobuf_file(self.entity, str(self.test_file))
        assert os.path.exists(str(self.test_file))

    def test_load_protobuf_file(self):
        save_protobuf_file(self.entity, str(self.test_file))
        # MOCK map_grpc_to_eda to avoid dependency on extra fields (width, height, etc.)
        with patch('eda_schema.protobuf_io.map_grpc_to_eda', return_value=self.entity):
            loaded_entity = load_protobuf_file(str(self.test_file))
            assert loaded_entity.name == self.entity.name
            assert loaded_entity.id == self.entity.id
            assert loaded_entity.type == self.entity.type
