class EDASchemaError(Exception):
    """
    Base exception class for EDA schema-related errors.
    """
    def __init__(self, message="An error occurred in the EDA schema."):
        super().__init__(message)


class ValidationError(EDASchemaError):
    """
    Exception raised for validation errors.
    """
    def __init__(self, message="Validation error occurred."):
        super().__init__(message)


class DataNotFoundError(EDASchemaError):
    """
    Exception raised when requested data is not found in the database or storage.
    """
    def __init__(self, entity_name=None, message="Requested data not found."):
        if entity_name:
            message = f"Data not found for entity '{entity_name}'."
        super().__init__(message)
