"""
Base Driver Class - Stub

This is a reference stub showing the interface that FidooDriver implements.
For the full specification, see the driver design specification (v2.0).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Iterator
from enum import Enum


class PaginationStyle(Enum):
    """How the driver handles pagination"""
    NONE = "none"              # No pagination support
    OFFSET = "offset"          # LIMIT/OFFSET style (SQL)
    CURSOR = "cursor"          # Cursor-based (Salesforce, GraphQL)
    PAGE_NUMBER = "page"       # Page-based (REST APIs)
    OFFSET_TOKEN = "offset_token"  # Token-based offset (Fidoo)


@dataclass
class DriverCapabilities:
    """What the driver can do"""
    read: bool = True
    write: bool = False
    update: bool = False
    delete: bool = False
    batch_operations: bool = False
    streaming: bool = False
    pagination: PaginationStyle = PaginationStyle.NONE
    query_language: Optional[str] = None
    max_page_size: Optional[int] = None
    supports_transactions: bool = False
    supports_relationships: bool = False


class BaseDriver(ABC):
    """
    Base class for all drivers.
    Every driver should inherit from this and implement required methods.
    """

    def __init__(
        self,
        api_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        debug: bool = False,
        **kwargs
    ):
        """
        Initialize the driver.

        Args:
            api_url: Base URL for API/database connection
            api_key: Authentication key/token (optional, can be loaded from env)
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts for rate limiting
            debug: Enable debug logging (logs all API calls)
            **kwargs: Driver-specific options
        """
        self.api_url = api_url
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.debug = debug

    @classmethod
    def from_env(cls, **kwargs) -> 'BaseDriver':
        """
        Create driver instance from environment variables.
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> DriverCapabilities:
        """Return driver capabilities so agent knows what it can do."""
        pass

    @abstractmethod
    def list_objects(self) -> List[str]:
        """Discover all available objects/tables/entities."""
        pass

    @abstractmethod
    def get_fields(self, object_name: str) -> Dict[str, Any]:
        """Get complete field schema for an object."""
        pass

    @abstractmethod
    def read(
        self,
        query: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Execute a read query and return results."""
        pass

    def close(self):
        """Close connections and cleanup resources."""
        pass
