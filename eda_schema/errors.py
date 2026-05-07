# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Drexel University,
#                         Integrated Circuits and Electronics (ICE) Laboratory
#
# Project : EDA-Schema -- Multimodal datamodel for digital circuit design
# Module  : eda_schema/errors.py
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
