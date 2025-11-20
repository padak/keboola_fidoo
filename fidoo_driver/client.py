"""
Fidoo7 Driver - Main Client Implementation

Expense management API driver with support for users, cards, transactions, expenses, and travel management.

Features:
- API key authentication (X-Api-Key header)
- Cursor-based pagination with offsetToken
- Rate limiting with automatic exponential backoff
- Structured error handling
- Debug mode for troubleshooting
"""

import logging
import os
import time
from typing import Any, Dict, Iterator, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Bug Prevention #5: Try package imports first, fallback to standalone
try:
    from .base import BaseDriver, DriverCapabilities, PaginationStyle
    from .exceptions import (
        AuthenticationError,
        ConnectionError,
        DriverError,
        FieldNotFoundError,
        ObjectNotFoundError,
        QuerySyntaxError,
        RateLimitError,
        TimeoutError,
        ValidationError,
    )
except ImportError:
    # Running as standalone script (e.g., in tests)
    from base import BaseDriver, DriverCapabilities, PaginationStyle
    from exceptions import (
        AuthenticationError,
        ConnectionError,
        DriverError,
        FieldNotFoundError,
        ObjectNotFoundError,
        QuerySyntaxError,
        RateLimitError,
        TimeoutError,
        ValidationError,
    )


class Fidoo7Driver(BaseDriver):
    """
    Fidoo7 Expense Management API Driver

    REST API driver for Fidoo expense management system.
    Supports user management, card operations, transactions, expenses, and travel management.

    Capabilities:
    - Read operations (GET endpoints for all objects)
    - Write operations (POST endpoints for create/update)
    - Delete operations (remove users, cards, settings)
    - Batch operations (load/unload multiple cards)
    - Cursor-based pagination (offsetToken)
    - Rate limiting (6,000 requests/day with automatic retry)

    Example:
        >>> client = Fidoo7Driver.from_env()
        >>> users = client.read("user/get-users", limit=50)
        >>> print(f"Found {len(users)} users")
        >>> client.close()
    """

    # Core constants
    DEFAULT_BASE_URL = "https://api.fidoo.com/v2/"
    DEMO_BASE_URL = "https://api-demo.fidoo.com/v2/"
    MAX_PAGE_SIZE = 100
    SAFE_DEFAULT_PAGE_SIZE = 50
    RATE_LIMIT_PER_DAY = 6000
    DRIVER_NAME = "Fidoo7"

    # Available objects/endpoints
    AVAILABLE_OBJECTS = [
        "user",
        "card",
        "transaction",
        "cash_transaction",
        "mvc_transaction",
        "expense",
        "travel_report",
        "travel_request",
        "personal_billing",
        "account",
        "cost_center",
        "project",
        "account_assignment",
        "accounting_category",
        "vat_breakdown",
        "vehicle",
        "receipt",
    ]

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        debug: bool = False,
        **kwargs
    ):
        """
        Initialize Fidoo7Driver.

        IMPORTANT: Follows strict 4-phase initialization order to prevent bugs.
        See: docs/BUG_PREVENTION_INITIALIZATION.md

        Args:
            base_url: API base URL (default: production https://api.fidoo.com/v2/)
            api_key: API key for authentication (from X-Api-Key header)
            access_token: OAuth access token (if supported, currently unused)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retry attempts for rate limiting (default: 3)
            debug: Enable debug logging (default: False)
            **kwargs: Additional driver-specific options

        Raises:
            AuthenticationError: If credentials invalid or missing
            ConnectionError: If cannot reach API

        Example:
            >>> driver = Fidoo7Driver.from_env()  # Recommended
            >>> driver = Fidoo7Driver(
            ...     base_url="https://api-demo.fidoo.com/v2/",
            ...     api_key="your_api_key_here"
            ... )
        """

        # ===== PHASE 1: Set custom attributes =====
        # Initialize any driver-specific fields before parent attributes
        self.driver_name = self.DRIVER_NAME
        self.demo_url = self.DEMO_BASE_URL

        # Setup logging
        if debug:
            logging.basicConfig(level=logging.DEBUG)
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.DEBUG)
        else:
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.WARNING)
        self.logger = logger

        # ===== PHASE 2: Set parent class attributes =====
        # DO NOT call super().__init__()! Set these manually instead.
        # This must happen BEFORE _create_session() so session can use them.
        resolved_base_url = base_url or self.DEFAULT_BASE_URL
        self.base_url = resolved_base_url
        self.api_key = api_key
        self.access_token = access_token
        self.timeout = timeout or 30
        self.max_retries = max_retries or 3
        self.debug = debug

        # ===== PHASE 3: Create session =====
        # Session creation can now use all attributes set above
        self.session = self._create_session()

        # ===== PHASE 4: Validate connection =====
        # Validation can now use self.session and other attributes
        self._validate_connection()

    @classmethod
    def from_env(cls, **kwargs) -> "Fidoo7Driver":
        """
        Create driver instance from environment variables.

        Environment variables:
            FIDOO_API_KEY: API key (required)
            FIDOO_API_URL: API base URL (optional, defaults to production)
            FIDOO_TIMEOUT: Request timeout in seconds (optional)
            FIDOO_MAX_RETRIES: Max retry attempts (optional)
            FIDOO_DEBUG: Enable debug mode "true"/"false" (optional)

        Args:
            **kwargs: Additional arguments passed to __init__

        Returns:
            Configured driver instance

        Raises:
            AuthenticationError: If required env vars are missing

        Example:
            >>> driver = Fidoo7Driver.from_env()
            >>> users = driver.read("user/get-users")
        """
        # Bug Prevention #6: NEVER hardcode credentials
        api_key = os.getenv("FIDOO_API_KEY")
        if not api_key:
            raise AuthenticationError(
                "Missing API key. Set FIDOO_API_KEY environment variable.",
                details={
                    "required_env_vars": ["FIDOO_API_KEY"],
                    "optional_env_vars": [
                        "FIDOO_API_URL",
                        "FIDOO_TIMEOUT",
                        "FIDOO_MAX_RETRIES",
                        "FIDOO_DEBUG",
                    ],
                },
            )

        base_url = os.getenv("FIDOO_API_URL", cls.DEFAULT_BASE_URL)
        timeout = int(os.getenv("FIDOO_TIMEOUT", "30"))
        max_retries = int(os.getenv("FIDOO_MAX_RETRIES", "3"))
        debug = os.getenv("FIDOO_DEBUG", "false").lower() == "true"

        return cls(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
            debug=debug,
            **kwargs,
        )

    def get_capabilities(self) -> DriverCapabilities:
        """
        Return driver capabilities.

        Returns:
            DriverCapabilities object with supported features

        Example:
            >>> capabilities = client.get_capabilities()
            >>> if capabilities.write:
            ...     print("Write operations supported")
        """
        return DriverCapabilities(
            read=True,
            write=True,
            update=True,
            delete=True,
            batch_operations=True,
            streaming=False,
            pagination=PaginationStyle.CURSOR,
            query_language=None,  # REST API, no query language
            max_page_size=self.MAX_PAGE_SIZE,
            supports_transactions=False,
            supports_relationships=True,
        )

    def list_objects(self) -> List[str]:
        """
        Discover all available objects/endpoints.

        Returns:
            List of available object names

        Example:
            >>> objects = client.list_objects()
            >>> print(objects)
            ['user', 'card', 'transaction', 'expense', ...]
        """
        return self.AVAILABLE_OBJECTS

    def get_fields(self, object_name: str) -> Dict[str, Any]:
        """
        Get complete field schema for an object.

        Args:
            object_name: Name of object (case-sensitive)

        Returns:
            Dictionary with field definitions

        Raises:
            ObjectNotFoundError: If object doesn't exist

        Example:
            >>> fields = client.get_fields("user")
            >>> print(fields.keys())
            dict_keys(['firstName', 'lastName', 'email', ...])
        """
        # Map object names to their field schemas
        schemas = {
            "user": {
                "firstName": {"type": "string", "required": False, "label": "First Name"},
                "lastName": {"type": "string", "required": False, "label": "Last Name"},
                "email": {"type": "string", "required": False, "label": "Email"},
                "phone": {"type": "string", "required": False, "label": "Phone"},
                "employeeNumber": {
                    "type": "string",
                    "required": False,
                    "label": "Employee Number",
                },
                "userState": {
                    "type": "string",
                    "required": False,
                    "label": "User State",
                    "enum": ["active", "deleted", "new"],
                },
            },
            "card": {
                "cardId": {"type": "string", "required": True, "label": "Card ID"},
                "status": {"type": "string", "required": False, "label": "Status"},
                "type": {
                    "type": "string",
                    "required": False,
                    "label": "Card Type",
                    "enum": ["personal", "shared"],
                },
                "masked_pan": {"type": "string", "required": False, "label": "Masked PAN"},
                "expiration": {"type": "string", "required": False, "label": "Expiration"},
                "available_balance": {
                    "type": "number",
                    "required": False,
                    "label": "Available Balance",
                },
            },
            "transaction": {
                "id": {"type": "string", "required": True, "label": "Transaction ID"},
                "cardId": {"type": "string", "required": False, "label": "Card ID"},
                "amount": {"type": "number", "required": False, "label": "Amount"},
                "date": {
                    "type": "datetime",
                    "required": False,
                    "label": "Transaction Date",
                },
            },
            "expense": {
                "id": {"type": "string", "required": True, "label": "Expense ID"},
                "amount": {"type": "number", "required": False, "label": "Amount"},
                "date": {"type": "datetime", "required": False, "label": "Expense Date"},
                "description": {
                    "type": "string",
                    "required": False,
                    "label": "Description",
                },
            },
            "account": {
                "accountId": {"type": "string", "required": True, "label": "Account ID"},
                "currency": {"type": "string", "required": False, "label": "Currency"},
                "balance": {"type": "number", "required": False, "label": "Balance"},
            },
        }

        if object_name not in schemas:
            available = self.list_objects()
            raise ObjectNotFoundError(
                f"Object '{object_name}' not found. Available objects: {', '.join(available[:5])}...",
                details={"requested": object_name, "available": available},
            )

        return schemas[object_name]

    def read(
        self,
        query: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a read query and return results.

        For Fidoo API, 'query' is the endpoint path (e.g., "user/get-users").

        Args:
            query: Endpoint path (e.g., "user/get-users" or "card/get-cards")
            limit: Maximum number of records to return (default: 50, max: 100)
            offset: Pagination token (offsetToken from previous response)

        Returns:
            List of records

        Raises:
            ObjectNotFoundError: If endpoint doesn't exist
            RateLimitError: If API rate limit exceeded
            QuerySyntaxError: If query/endpoint invalid
            TimeoutError: If request times out

        Example:
            >>> results = client.read("user/get-users", limit=50)
            >>> print(f"Found {len(results)} users")

            >>> # Pagination example
            >>> first_batch = client.read("user/get-users", limit=50)
            >>> if first_batch:
            ...     next_batch = client.read("user/get-users", limit=50, offset=first_batch[-1].get("offsetToken"))
        """
        # Bug Prevention #4: Validate page size
        if limit is None:
            limit = self.SAFE_DEFAULT_PAGE_SIZE
        if limit > self.MAX_PAGE_SIZE:
            raise ValidationError(
                f"limit cannot exceed {self.MAX_PAGE_SIZE} (got: {limit})",
                details={
                    "provided": limit,
                    "maximum": self.MAX_PAGE_SIZE,
                    "parameter": "limit",
                    "suggestion": f"Use limit <= {self.MAX_PAGE_SIZE}",
                },
            )

        # Build endpoint path
        endpoint = f"/v2/{query.lstrip('/')}"

        # Build request parameters
        params = {"limit": limit}
        if offset:
            params["offsetToken"] = offset

        try:
            response = self.session.post(
                f"{self.base_url.rstrip('/')}{endpoint}",
                json=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise TimeoutError(
                f"Request to {endpoint} timed out after {self.timeout} seconds",
                details={"endpoint": endpoint, "timeout": self.timeout},
            )
        except requests.exceptions.HTTPError as e:
            self._handle_api_error(e.response, f"reading from {endpoint}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Failed to connect to {endpoint}",
                details={"endpoint": endpoint, "error": str(e)},
            )

        # Parse response
        return self._parse_response(response)

    def read_batched(
        self, query: str, batch_size: int = 50
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Execute query and yield results in batches (memory-efficient).

        Args:
            query: Endpoint path (e.g., "user/get-users")
            batch_size: Number of records per batch (default: 50, max: 100)

        Yields:
            Batches of records as lists of dictionaries

        Example:
            >>> total = 0
            >>> for batch in client.read_batched("user/get-users", batch_size=50):
            ...     for user in batch:
            ...         print(f"{user['firstName']} {user['lastName']}")
            ...     total += len(batch)
            >>> print(f"Total users: {total}")
        """
        offset_token = None

        while True:
            # Fetch batch
            batch = self.read(query, limit=batch_size, offset=offset_token)

            if not batch:
                break

            yield batch

            # Check for next page
            # In Fidoo API, check if response has nextOffsetToken
            if isinstance(batch, dict) and batch.get("complete"):
                break

            # Get next offset token from batch (if it's a response object)
            if isinstance(batch, dict) and "nextOffsetToken" in batch:
                offset_token = batch["nextOffsetToken"]
            else:
                # No more pages
                break

    def create(self, object_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record.

        Args:
            object_name: Name of object (e.g., "user", "cost_center")
            data: Field values as dictionary

        Returns:
            Created record with ID

        Raises:
            ValidationError: If data is invalid
            ObjectNotFoundError: If object type not found

        Example:
            >>> user = client.create("user", {
            ...     "firstName": "John",
            ...     "lastName": "Doe",
            ...     "email": "john@example.com"
            ... })
            >>> print(f"Created user: {user['id']}")
        """
        # Map object names to create endpoints
        endpoint_map = {
            "user": "user/add-user",
            "cost_center": "settings/add-cost-center",
            "project": "settings/add-project",
            "accounting_category": "settings/add-accounting-category",
            "vat_breakdown": "settings/add-vat-breakdown",
            "account_assignment": "settings/add-account-assignment",
            "vehicle": "settings/add-vehicle",
        }

        if object_name not in endpoint_map:
            raise ObjectNotFoundError(
                f"Cannot create object type '{object_name}'",
                details={"requested": object_name, "creatable_types": list(endpoint_map.keys())},
            )

        endpoint = endpoint_map[object_name]
        full_endpoint = f"/v2/{endpoint}"

        try:
            response = self.session.post(
                f"{self.base_url.rstrip('/')}{full_endpoint}",
                json=data,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                error_data = e.response.json()
                raise ValidationError(
                    f"Validation failed: {error_data.get('message', 'Unknown error')}",
                    details={"object": object_name, "errors": error_data},
                )
            self._handle_api_error(e.response, f"creating {object_name}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Failed to create {object_name}",
                details={"object": object_name, "error": str(e)},
            )

        return self._parse_response(response)

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
            ObjectNotFoundError: If record doesn't exist
            ValidationError: If data is invalid

        Example:
            >>> user = client.update("user", "user123", {"phone": "+1234567890"})
            >>> print(f"Updated user: {user['email']}")
        """
        # Map object names to update endpoints
        endpoint_map = {
            "user": "user/update-user",
            "cost_center": "settings/update-cost-center",
            "project": "settings/update-project",
            "accounting_category": "settings/update-accounting-category",
            "vat_breakdown": "settings/update-vat-breakdown",
            "account_assignment": "settings/update-account-assignment",
            "vehicle": "settings/update-vehicle",
        }

        if object_name not in endpoint_map:
            raise ObjectNotFoundError(
                f"Cannot update object type '{object_name}'",
                details={"requested": object_name, "updatable_types": list(endpoint_map.keys())},
            )

        endpoint = endpoint_map[object_name]
        full_endpoint = f"/v2/{endpoint}"

        # Add record ID to data
        update_data = {"id": record_id, **data}

        try:
            response = self.session.post(
                f"{self.base_url.rstrip('/')}{full_endpoint}",
                json=update_data,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ObjectNotFoundError(
                    f"Record not found: {record_id}",
                    details={"object": object_name, "record_id": record_id},
                )
            elif e.response.status_code == 400:
                error_data = e.response.json()
                raise ValidationError(
                    f"Validation failed: {error_data.get('message', 'Unknown error')}",
                    details={"object": object_name, "record_id": record_id, "errors": error_data},
                )
            self._handle_api_error(e.response, f"updating {object_name} {record_id}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Failed to update {object_name}",
                details={"object": object_name, "record_id": record_id, "error": str(e)},
            )

        return self._parse_response(response)

    def delete(self, object_name: str, record_id: str) -> bool:
        """
        Delete a record.

        Args:
            object_name: Name of object
            record_id: ID of record to delete

        Returns:
            True if successful

        Raises:
            ObjectNotFoundError: If record doesn't exist
            ValidationError: If record cannot be deleted (e.g., user has roles)

        Note:
            Use with caution! Some deletions have prerequisites.
            For example, users cannot be deleted if they have roles or card holdings.

        Example:
            >>> success = client.delete("cost_center", "cc123")
            >>> print("Deleted" if success else "Failed")
        """
        # Map object names to delete endpoints
        endpoint_map = {
            "user": "user/delete-user",
            "cost_center": "settings/delete-cost-center",
            "project": "settings/delete-project",
            "accounting_category": "settings/delete-accounting-category",
            "vat_breakdown": "settings/delete-vat-breakdown",
            "account_assignment": "settings/delete-account-assignment",
            "vehicle": "settings/delete-vehicle",
        }

        if object_name not in endpoint_map:
            raise ObjectNotFoundError(
                f"Cannot delete object type '{object_name}'",
                details={"requested": object_name, "deletable_types": list(endpoint_map.keys())},
            )

        endpoint = endpoint_map[object_name]
        full_endpoint = f"/v2/{endpoint}"

        delete_data = {"id": record_id}

        try:
            response = self.session.post(
                f"{self.base_url.rstrip('/')}{full_endpoint}",
                json=delete_data,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ObjectNotFoundError(
                    f"Record not found: {record_id}",
                    details={"object": object_name, "record_id": record_id},
                )
            elif e.response.status_code == 400:
                error_data = e.response.json()
                raise ValidationError(
                    f"Cannot delete: {error_data.get('message', 'Unknown error')}",
                    details={"object": object_name, "record_id": record_id, "errors": error_data},
                )
            self._handle_api_error(e.response, f"deleting {object_name} {record_id}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Failed to delete {object_name}",
                details={"object": object_name, "record_id": record_id, "error": str(e)},
            )

        return True

    def call_endpoint(
        self,
        endpoint: str,
        method: str = "POST",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Call a REST API endpoint directly (low-level access).

        Args:
            endpoint: API endpoint path (e.g., "/v2/user/get-users")
            method: HTTP method ("GET", "POST", "PUT", "DELETE")
            params: URL query parameters (for GET)
            data: Request body (for POST/PUT)
            **kwargs: Additional request options

        Returns:
            Response data as dictionary

        Example:
            >>> result = client.call_endpoint(
            ...     endpoint="/v2/user/get-users",
            ...     method="POST",
            ...     data={"limit": 50}
            ... )
            >>> print(result)
        """
        url = f"{self.base_url.rstrip('/')}{endpoint}"

        if self.debug:
            self.logger.debug(f"[DEBUG] {method} {url}")

        try:
            if method.upper() == "GET":
                response = self.session.get(
                    url, params=params or data, timeout=self.timeout, **kwargs
                )
            elif method.upper() == "POST":
                response = self.session.post(url, json=data or params, timeout=self.timeout, **kwargs)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data or params, timeout=self.timeout, **kwargs)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, json=data or params, timeout=self.timeout, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"API call failed: {str(e)}",
                details={"endpoint": endpoint, "method": method, "error": str(e)},
            )

        return response.json()

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.

        Fidoo API has 6,000 requests per customer per day.
        This method returns the documented limit (actual remaining requests not available).

        Returns:
            {
                "limit": int,           # Total requests per day
                "retry_after": int      # Seconds to wait if rate limited
            }

        Example:
            >>> status = client.get_rate_limit_status()
            >>> print(f"Rate limit: {status['limit']} requests/day")
        """
        return {
            "limit": self.RATE_LIMIT_PER_DAY,
            "remaining": None,  # Not provided by Fidoo API
            "reset_at": None,   # Not provided by Fidoo API
            "retry_after": None,  # Set by 429 response
        }

    def close(self):
        """Close connections and cleanup resources."""
        if self.session:
            self.session.close()

    # Internal helper methods

    def _create_session(self) -> requests.Session:
        """
        Create HTTP session with authentication.

        Bug Prevention #1 & #2: Correct header setup
        - EXACT header name: X-Api-Key (case-sensitive!)
        - Do NOT set Content-Type in session headers
        - Content-Type is added automatically by requests library

        Returns:
            Configured requests.Session with auth headers
        """
        session = requests.Session()

        # Set headers that apply to ALL requests
        session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": f"{self.driver_name}-Python-Driver/1.0.0",
            }
        )
        # NOTE: Do NOT set Content-Type here! (affects GET requests)

        # Add authentication (use IF, not ELIF - multiple can coexist)
        if self.access_token:
            session.headers["Authorization"] = f"Bearer {self.access_token}"

        if self.api_key:
            # Bug Prevention #1: EXACT header name from docs (case-sensitive!)
            session.headers["X-Api-Key"] = self.api_key

        # Configure retries with exponential backoff
        if self.max_retries > 0:
            retry_strategy = Retry(
                total=self.max_retries,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET", "POST", "PUT", "DELETE"],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)

        return session

    def _parse_response(self, response: requests.Response) -> List[Dict[str, Any]]:
        """
        Parse API response and extract data records.

        Bug Prevention #3: Handle case-sensitive field names
        Try all known variations: root, items, data, results

        Args:
            response: HTTP response from API

        Returns:
            List of records

        Raises:
            ConnectionError: If response is not valid JSON
        """
        try:
            data = response.json()
        except ValueError as e:
            raise ConnectionError(
                "Invalid JSON response from API",
                details={
                    "status_code": response.status_code,
                    "content": response.text[:500],
                    "error": str(e),
                },
            )

        # Handle direct array responses
        if isinstance(data, list):
            return data

        # Handle object-wrapped responses
        if isinstance(data, dict):
            # Bug Prevention #3: Try all known field names (case-sensitive!)
            # Order: Try documented field first, then common variations
            records = (
                data.get("root")
                or data.get("items")
                or data.get("Items")
                or data.get("data")
                or data.get("Data")
                or data.get("results")
                or data.get("Results")
                or data.get("Records")
                or data.get("records")
                or []
            )

            # Ensure we return a list
            if isinstance(records, list):
                return records
            elif records is not None:
                return [records]  # Wrap single object in list
            else:
                return []

        # Unknown format
        return []

    def _handle_api_error(self, response: requests.Response, context: str = ""):
        """
        Convert HTTP errors to structured driver exceptions.

        Args:
            response: Failed HTTP response
            context: Context string (e.g., "reading user records")

        Raises:
            Appropriate DriverError subclass
        """
        status_code = response.status_code

        try:
            error_data = response.json()
            error_msg = error_data.get("error", error_data.get("message", "Unknown error"))
        except ValueError:
            error_msg = response.text[:500]

        # Map status codes to exceptions
        if status_code == 401:
            raise AuthenticationError(
                f"Authentication failed: {error_msg}",
                details={
                    "status_code": 401,
                    "context": context,
                    "suggestion": "Check your API key or access token",
                    "api_response": error_msg,
                },
            )
        elif status_code == 403:
            raise AuthenticationError(
                f"Permission denied: {error_msg}",
                details={
                    "status_code": 403,
                    "context": context,
                    "suggestion": "Verify your API key has required permissions",
                    "api_response": error_msg,
                },
            )
        elif status_code == 404:
            raise ObjectNotFoundError(
                f"Resource not found: {error_msg}",
                details={
                    "status_code": 404,
                    "context": context,
                    "suggestion": "Check endpoint path and object existence",
                    "api_response": error_msg,
                },
            )
        elif status_code == 429:
            # Should not happen after retries, but handle it
            retry_after = response.headers.get("Retry-After", "60")
            raise RateLimitError(
                f"Rate limit exceeded (after retries): {error_msg}",
                details={
                    "status_code": 429,
                    "retry_after": retry_after,
                    "context": context,
                    "suggestion": f"Wait {retry_after} seconds before retrying",
                    "limit_per_day": self.RATE_LIMIT_PER_DAY,
                    "api_response": error_msg,
                },
            )
        elif status_code >= 500:
            raise ConnectionError(
                f"API server error: {error_msg}",
                details={
                    "status_code": status_code,
                    "context": context,
                    "suggestion": "API server issue - try again later",
                    "api_response": error_msg,
                },
            )
        else:
            raise DriverError(
                f"API request failed: {error_msg}",
                details={
                    "status_code": status_code,
                    "context": context,
                    "api_response": error_msg,
                },
            )

    def _validate_connection(self):
        """
        Validate connection at __init__ time (fail fast!).

        Calls the public status endpoint to verify API key validity.

        Raises:
            AuthenticationError: Invalid credentials
            ConnectionError: Cannot reach API
        """
        try:
            response = self.session.get(
                f"{self.base_url.rstrip('/')}/v2/status/user-info",
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Invalid Fidoo API key. Check your credentials.",
                    details={"api_url": self.base_url, "status_code": 401},
                )
            elif e.response.status_code >= 500:
                raise ConnectionError(
                    "Fidoo API server is not responding",
                    details={"api_url": self.base_url, "status_code": e.response.status_code},
                )
            else:
                raise ConnectionError(
                    f"Connection validation failed: {e}",
                    details={"api_url": self.base_url, "status_code": e.response.status_code},
                )
        except requests.exceptions.Timeout:
            raise ConnectionError(
                f"Connection to Fidoo API timed out after {self.timeout} seconds",
                details={"api_url": self.base_url, "timeout": self.timeout},
            )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Cannot reach Fidoo API: {e}",
                details={"api_url": self.base_url, "error": str(e)},
            )
