"""
Base Driver Interface for Fidoo8Driver

Defines the abstract interface that all drivers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Iterator
from enum import Enum


class PaginationStyle(Enum):
    """How the driver handles pagination"""

    NONE = "none"  # No pagination support
    OFFSET = "offset"  # LIMIT/OFFSET style (SQL)
    CURSOR = "cursor"  # Cursor-based (Fidoo, GraphQL)
    PAGE_NUMBER = "page"  # Page-based (REST APIs)


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
    def from_env(cls, **kwargs) -> "BaseDriver":
        """
        Create driver instance from environment variables.

        Raises:
            AuthenticationError: If required env vars are missing
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> DriverCapabilities:
        """
        Return driver capabilities so agent knows what it can do.

        Returns:
            DriverCapabilities with boolean flags for features
        """
        pass

    # Discovery Methods (REQUIRED)

    @abstractmethod
    def list_objects(self) -> List[str]:
        """
        Discover all available objects/tables/entities.

        Returns:
            List of object names
        """
        pass

    @abstractmethod
    def get_fields(self, object_name: str) -> Dict[str, Any]:
        """
        Get complete field schema for an object.

        Args:
            object_name: Name of object (case-sensitive!)

        Returns:
            Dictionary with field definitions

        Raises:
            ObjectNotFoundError: If object doesn't exist
        """
        pass

    # Read Operations (REQUIRED)

    @abstractmethod
    def read(
        self,
        query: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a read query and return results.

        Args:
            query: Query in driver's native language
            limit: Maximum number of records to return
            offset: Number of records to skip (for pagination)

        Returns:
            List of dictionaries (one per record)

        Raises:
            QuerySyntaxError: Invalid query syntax
            RateLimitError: API rate limit exceeded (after retries)
        """
        pass

    # Write Operations (OPTIONAL - depends on capabilities)

    def create(self, object_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record.

        Args:
            object_name: Name of object to create
            data: Field values as dictionary

        Returns:
            Created record with ID

        Raises:
            NotImplementedError: If driver doesn't support write operations
            ValidationError: If data is invalid
        """
        raise NotImplementedError("Write operations not supported by this driver")

    def update(self, object_name: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing record.

        Args:
            object_name: Name of object
            record_id: ID of record to update
            data: Field values to update

        Returns:
            Updated record

        Raises:
            NotImplementedError: If driver doesn't support updates
            ObjectNotFoundError: If record doesn't exist
        """
        raise NotImplementedError("Update operations not supported by this driver")

    def delete(self, object_name: str, record_id: str) -> bool:
        """
        Delete a record.

        Args:
            object_name: Name of object
            record_id: ID of record to delete

        Returns:
            True if successful

        Raises:
            NotImplementedError: If driver doesn't support delete

        Note:
            Agents should RARELY generate delete operations!
        """
        raise NotImplementedError("Delete operations not supported by this driver")

    # Pagination / Streaming (OPTIONAL)

    def read_batched(
        self,
        query: str,
        batch_size: int = 1000
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Execute query and yield results in batches (memory-efficient).

        Args:
            query: Query in driver's native language
            batch_size: Number of records per batch

        Yields:
            Batches of records as lists of dictionaries
        """
        raise NotImplementedError("Batched reading not supported by this driver")

    # Low-Level API (OPTIONAL - for REST APIs)

    def call_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call a REST API endpoint directly (low-level access).

        Args:
            endpoint: API endpoint path
            method: HTTP method ("GET", "POST", "PUT", "DELETE")
            params: URL query parameters
            data: Request body (for POST/PUT)
            **kwargs: Additional request options

        Returns:
            Response data as dictionary
        """
        raise NotImplementedError("Low-level endpoint calls not supported by this driver")

    # Utility Methods

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status (if supported by API).

        Returns:
            Dictionary with rate limit information
        """
        return {"remaining": None, "limit": None, "reset_at": None, "retry_after": None}

    def close(self):
        """
        Close connections and cleanup resources.
        """
        pass
