"""
Fidoo Expense Management API Driver

Python driver for integrating with the Fidoo expense management and corporate card platform.

Installation:
    pip install fidoo-driver

Quick Start:
    from fidoo import FidooDriver

    client = FidooDriver.from_env()
    users = client.read("user/get-users")
    client.close()

API Documentation: https://www.fidoo.com/expense-management/integrace/api
"""

__version__ = "1.0.0"
__author__ = "Claude Code"
__license__ = "MIT"

from .client import FidooDriver
from .base import DriverCapabilities, PaginationStyle
from .exceptions import (
    DriverError,
    AuthenticationError,
    ConnectionError,
    ObjectNotFoundError,
    FieldNotFoundError,
    QuerySyntaxError,
    RateLimitError,
    ValidationError,
    TimeoutError
)

__all__ = [
    "FidooDriver",
    "DriverCapabilities",
    "PaginationStyle",
    "DriverError",
    "AuthenticationError",
    "ConnectionError",
    "ObjectNotFoundError",
    "FieldNotFoundError",
    "QuerySyntaxError",
    "RateLimitError",
    "ValidationError",
    "TimeoutError",
    "__version__",
    "__author__",
    "__license__",
]
