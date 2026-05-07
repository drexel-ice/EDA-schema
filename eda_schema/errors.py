class EDASchemaError(Exception):
    """
    Base exception class for EDA schema-related errors.
    """

    def __init__(self, message="An error occurred in the EDA schema."):
        """
        Initialize the EDA schema error.

        Args:
            message: Error message describing what went wrong.
        """
        super().__init__(message)


class ValidationError(EDASchemaError):
    """
    Exception raised for validation errors.
    """

    def __init__(self, message="Validation error occurred."):
        """
        Initialize the validation error.

        Args:
            message: Error message describing the validation failure.
        """
        super().__init__(message)


class DataNotFoundError(EDASchemaError):
    """
    Exception raised when requested data is not found in the database or storage.
    """

    def __init__(self, entity_name=None, message=None):
        """
        Initialize the data not found error.

        Args:
            entity_name: Optional name of the entity that was not found.
            message: Optional custom error message. If not provided, a default
                    message is generated based on entity_name.
        """
        if message is None:
            if entity_name:
                message = f"Data not found for entity '{entity_name}'."
            else:
                message = "Requested data not found."
        super().__init__(message)
