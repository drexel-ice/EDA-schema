# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : tests/unit/test_schema_metadata.py
# Authors :
#     Pratik Shrestha       <ps937@drexel.edu>
#
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike
# 4.0 International License (CC BY-NC-SA 4.0). You may obtain a copy of the
# license at: https://creativecommons.org/licenses/by-nc-sa/4.0/
#
# This software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. Commercial use is
# expressly prohibited; derivative works must be shared under the same
# license terms (ShareAlike).

"""
Tests for SchemaMetadata registry.
"""

from eda_schema.entity import SchemaMetadata
from eda_schema import entity


class TestSchemaMetadata:
    """Test SchemaMetadata functionality."""

    def test_schema_metadata_get_model(self):
        """Test getting entity model."""
        model = SchemaMetadata.get_model('netlists')
        assert model is not None
        assert model == entity.NetlistEntity

    def test_schema_metadata_get_pk_columns(self):
        """Test getting primary key columns."""
        pk_cols = SchemaMetadata.get_pk_columns('netlists')
        assert 'flow_id' in pk_cols
        assert 'stage' in pk_cols

    def test_schema_metadata_is_graph_entity(self):
        """Test checking if entity is a graph entity."""
        assert SchemaMetadata.is_graph_entity('netlists') is True
        assert SchemaMetadata.is_graph_entity('power_metrics') is False

    def test_schema_metadata_items(self):
        """Test getting all registered entities."""
        items = SchemaMetadata.items()
        assert isinstance(items, list)
        entity_names = [name for name, _ in items]
        assert 'netlists' in entity_names
        assert 'gates' in entity_names
