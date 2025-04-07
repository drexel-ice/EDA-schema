import pytest
import os
from unittest.mock import patch
"""
Unit tests for Protobuf IO functionality in the eda_schema package.

This module tests the ability to save and load Protobuf entitys to and from files.
It uses pytest for testing and unittest.mock for mocking dependencies.
"""

from eda_schema import eda_schema_pb2 as pb2
from eda_schema.protobuf_io import load_protobuf_file, save_protobuf_file

# Static list of entity names
PROTO_ENTITIES = [
    "StandardCellEntity",
    "GateEntity",
    "IOPortEntity",
    "InterconnectSegmentEntity",
    "InterconnectEntity",
    "TimingPathNodeEntity",
    "TimingPathEntity",
    "CellMetricsEntity",
    "AreaMetricsEntity",
    "PowerMetricsEntity",
    "CriticalPathMetricsEntity",
    "ClockTreeEntity",
    "NetlistEntity",
]

def get_test_protobuf(entity_name):
    """
    Return a populated protobuf object for the given entity name.

    Args:
        entity_name (str): Name of the Protobuf message class.

    Returns:
        protobuf.Message: An instance of the corresponding Protobuf message, populated with test data.
    """
    raise NotImplementedError("Return a populated protobuf object for the given entity name.")

def compare_protobufs(expected, actual):
    """
    Compare two protobuf messages for equality.

    Args:
        expected (protobuf.Message): The expected Protobuf message.
        actual (protobuf.Message): The actual Protobuf message to compare.

    Returns:
        bool: True if the messages are equal, False otherwise.
    """
    raise NotImplementedError("Compare two protobuf objects for equality.")


class TestProtobufIO:  # SINGLE class

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmpdir):
        self.test_file = tmpdir.join('test_protobuf_file.bin')
        yield

    @pytest.mark.parametrize("entity_name", PROTO_ENTITIES)  # FIXED: applied to function
    def test_save_and_load_protobuf_file(self, entity_name):
        expected_protobuf = get_test_protobuf(entity_name)
        # Dynamically create entity of correct type
        protobuf_cls = getattr(pb2, entity_name)
        protobuf = protobuf_cls()

        # Save protobuf - pass the correct entity_name as entity_class
        save_protobuf_file(protobuf, str(self.test_file), entity_class=entity_name)
        
        # Load entity (load always returns an EntityMessage)
        loaded_protobuf = load_protobuf_file(str(self.test_file))
        assert compare_protobufs(expected_protobuf, loaded_protobuf)
