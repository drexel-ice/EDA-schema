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
