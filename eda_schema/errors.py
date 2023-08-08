class EDASchemaError(Exception):
    """
    Base exception class for EDA schema-related errors.
    """

class ValidationError(EDASchemaError):
    """
    Exception raised for validation errors.
    """
