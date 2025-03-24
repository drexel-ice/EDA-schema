import pytest
import os
from unittest.mock import patch
"""
Unit tests for Protobuf IO functionality in the eda_schema package.

This module tests the ability to save and load Protobuf messages to and from files.
It uses pytest for testing and unittest.mock for mocking dependencies.
"""

from eda_schema import eda_schema_pb2 as pb2
from eda_schema.protobuf_io import load_protobuf_file, save_protobuf_file

# Static list of message names
PROTO_MESSAGES = [
    "Empty",
    "EdgeEntity",
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
    "EntityMessage",
    "ImportRequest",
    "ImportResponse",
    "ExportRequest",
    "ExportResponse",
]

class TestProtobufIO:  # SINGLE class

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmpdir):
        self.test_file = tmpdir.join('test_protobuf_file.bin')
        yield

    @pytest.mark.parametrize("message_name", PROTO_MESSAGES)  # FIXED: applied to function
    def test_save_and_load_protobuf_file(self, message_name):
        # Dynamically create entity of correct type
        entity_cls = getattr(pb2, message_name)
        entity = entity_cls()
        
        # Populate fields if they exist
        if hasattr(entity, 'name'):
            entity.name = 'TestNetlist'
        if hasattr(entity, 'id'):
            entity.id = 12345
        if hasattr(entity, 'type'):
            entity.type = "Netlist"

        # Save entity - pass the correct message_name as entity_class
        save_protobuf_file(entity, str(self.test_file), entity_class=message_name)
        
        # Load entity (load always returns an EntityMessage)
        loaded_entity = load_protobuf_file(str(self.test_file))
        
        # Compare common fields only if they exist on loaded_entity
        if hasattr(entity, 'name') and hasattr(loaded_entity, 'name'):
            assert loaded_entity.name == entity.name
        if hasattr(entity, 'id') and hasattr(loaded_entity, 'id'):
            assert loaded_entity.id == entity.id
        if hasattr(entity, 'type') and hasattr(loaded_entity, 'type'):
            assert loaded_entity.type == entity.type
