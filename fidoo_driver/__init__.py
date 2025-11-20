"""
Fidoo8Driver - Python API Driver for Fidoo Expense Management API

Complete driver for interacting with Fidoo's comprehensive expense management platform.

Installation:
    pip install fidoo8-driver

Quick Start:
    >>> from fidoo8 import Fidoo8Driver
    >>> driver = Fidoo8Driver.from_env()
    >>> users = driver.read("User", limit=50)

Features:
    - User management and profiles
    - Card management (personal and shared)
    - Transaction tracking
    - Expense management
    - Travel reports and allowances
    - Personal billing and settlements
    - Automatic retry on rate limits
    - Comprehensive error handling
    - Debug mode for troubleshooting

API Documentation:
    https://www.fidoo.com/support/expense-management-en/it-specialist/specifications-api/

Demo API:
    https://api-demo.fidoo.com/v2/

Production API:
    https://api.fidoo.com/v2/
"""

__version__ = "1.0.0"
__author__ = "Fidoo API Driver Generator"

from .client import Fidoo8Driver
from .base import BaseDriver, DriverCapabilities, PaginationStyle
from .exceptions import (
    DriverError,
    AuthenticationError,
    ConnectionError,
    ObjectNotFoundError,
    FieldNotFoundError,
    QuerySyntaxError,
    RateLimitError,
    ValidationError,
    TimeoutError,
)

__all__ = [
    "Fidoo8Driver",
    "BaseDriver",
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
]
