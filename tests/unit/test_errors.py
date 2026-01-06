"""
Tests for custom exceptions.
"""

from eda_schema.errors import EDASchemaError, ValidationError, DataNotFoundError


class TestEDASchemaError:  # pylint: disable=too-few-public-methods
    """Test EDASchemaError."""

    def test_edaschema_error_creation(self):
        """Test creating EDASchemaError."""
        error = EDASchemaError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


class TestValidationError:  # pylint: disable=too-few-public-methods
    """Test ValidationError."""

    def test_validation_error_creation(self):
        """Test creating ValidationError."""
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, EDASchemaError)


class TestDataNotFoundError:
    """Test DataNotFoundError."""

    def test_data_not_found_error_creation(self):
        """Test creating DataNotFoundError."""
        error = DataNotFoundError(message="Data not found")
        assert "Data not found" in str(error)
        assert isinstance(error, EDASchemaError)

    def test_data_not_found_error_with_entity(self):
        """Test DataNotFoundError with entity name."""
        error = DataNotFoundError(entity_name="netlists")
        assert "netlists" in str(error)
