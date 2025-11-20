"""
Base Driver Class - Abstract Interface

Defines the contract that all drivers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional


class PaginationStyle(Enum):
    """How the driver handles pagination"""
    NONE = "none"              # No pagination support
    OFFSET = "offset"          # LIMIT/OFFSET style (SQL)
    CURSOR = "cursor"          # Cursor-based (Salesforce, GraphQL)
    PAGE_NUMBER = "page"       # Page-based (REST APIs)


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
    query_language: Optional[str] = None  # "SOQL", "SQL", "MongoDB Query", None
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

        # Validate credentials at init time (fail fast!)
        self._validate_connection()

    @classmethod
    def from_env(cls, **kwargs) -> 'BaseDriver':
        """
        Create driver instance from environment variables.

        Example:
            # Reads FIDOO_API_URL and FIDOO_API_KEY from os.environ
            client = Fidoo7Driver.from_env()

        Raises:
            AuthenticationError: If required env vars are missing
        """
        pass  # Implementation in subclass

    @abstractmethod
    def get_capabilities(self) -> DriverCapabilities:
        """
        Return driver capabilities so agent knows what it can do.

        Returns:
            DriverCapabilities with boolean flags for features

        Example:
            capabilities = client.get_capabilities()
            if capabilities.write:
                # Agent can generate create() calls
        """
        pass

    # Discovery Methods (REQUIRED)

    @abstractmethod
    def list_objects(self) -> List[str]:
        """
        Discover all available objects/endpoints/resources.

        Returns:
            List of object names (e.g., ["user", "card", "expense"])

        Example:
            objects = client.list_objects()
            # ["user", "card", "transaction", "expense", ...]
        """
        pass

    @abstractmethod
    def get_fields(self, object_name: str) -> Dict[str, Any]:
        """
        Get complete field schema for an object.

        Args:
            object_name: Name of object (case-sensitive!)

        Returns:
            Dictionary with field definitions:
            {
                "field_name": {
                    "type": "string|integer|float|boolean|datetime|...",
                    "label": "Human-readable name",
                    "required": bool,
                    "nullable": bool,
                    "max_length": int (for strings),
                    "references": str (for foreign keys)
                }
            }

        Raises:
            ObjectNotFoundError: If object doesn't exist

        Example:
            fields = client.get_fields("user")
            # Returns: {
            #   "firstName": {"type": "string", "required": False, "label": "First Name"},
            #   ...
            # }
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
            query: Query in driver's native language or endpoint path
            limit: Maximum number of records to return
            offset: Number of records to skip (for pagination)

        Returns:
            List of dictionaries (one per record)

        Raises:
            QuerySyntaxError: Invalid query syntax
            RateLimitError: API rate limit exceeded (after retries)

        Example:
            results = client.read("user/get-users", limit=100)
            # Returns: [{"id": "...", "firstName": "John", ...}, ...]
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

        Example:
            record = client.create("user", {
                "firstName": "John",
                "lastName": "Doe",
                "email": "john@example.com"
            })
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
            Always require explicit user approval for deletes.
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

        Example:
            for batch in client.read_batched("user/get-users", batch_size=100):
                process_batch(batch)  # Process 100 records at a time

        Note:
            Agent generates code with this pattern.
            Python runtime handles iteration (not the agent!).
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
            endpoint: API endpoint path (e.g., "/v2/user/get-users")
            method: HTTP method ("GET", "POST", "PUT", "DELETE")
            params: URL query parameters
            data: Request body (for POST/PUT)
            **kwargs: Additional request options

        Returns:
            Response data as dictionary

        Example:
            result = client.call_endpoint(
                endpoint="/v2/user/get-users",
                method="POST",
                data={"limit": 50}
            )
        """
        raise NotImplementedError("Low-level endpoint calls not supported by this driver")

    # Utility Methods

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status (if supported by API).

        Returns:
            {
                "remaining": int,     # Requests remaining
                "limit": int,         # Total limit
                "reset_at": str,      # ISO timestamp when limit resets
                "retry_after": int    # Seconds to wait (if rate limited)
            }

        Example:
            status = client.get_rate_limit_status()
            if status["remaining"] < 10:
                print("Warning: Only 10 API calls left!")
        """
        return {"remaining": None, "limit": None, "reset_at": None, "retry_after": None}

    def close(self):
        """
        Close connections and cleanup resources.

        Example:
            client = Driver.from_env()
            try:
                results = client.read("user/get-users")
            finally:
                client.close()
        """
        pass

    # Internal Methods

    def _validate_connection(self):
        """
        Validate connection at __init__ time (fail fast!).

        Raises:
            AuthenticationError: Invalid credentials
            ConnectionError: Cannot reach API
        """
        pass
