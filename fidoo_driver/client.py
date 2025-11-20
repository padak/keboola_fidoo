"""
Fidoo8Driver - Python API Driver for Fidoo Expense Management API

Fidoo is a comprehensive expense management platform for corporate finances.
This driver provides access to:
- User management and profiles
- Card management (personal and shared)
- Transaction tracking
- Expense management
- Travel reports and allowances
- Personal billing and settlements
- System settings and configurations

API Documentation: https://www.fidoo.com/support/expense-management-en/it-specialist/specifications-api/
Demo API: https://api-demo.fidoo.com/v2/
Production API: https://api.fidoo.com/v2/
"""

import os
import time
import logging
import requests
from typing import List, Dict, Any, Optional, Iterator
from urllib.parse import urljoin

# Try package imports first, fallback to standalone
try:
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
except ImportError:
    # Running as standalone script (e.g., in tests)
    from base import BaseDriver, DriverCapabilities, PaginationStyle
    from exceptions import (
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


class Fidoo8Driver(BaseDriver):
    """
    Fidoo8Driver - Complete Python driver for Fidoo Public API v2

    Features:
    - Complete CRUD operations on users, cards, expenses, and transactions
    - Cursor-based pagination with offset tokens
    - Automatic retry on rate limits (429) with exponential backoff
    - Comprehensive error handling with actionable messages
    - Debug mode for troubleshooting API calls

    Example:
        >>> # Load from environment
        >>> client = Fidoo8Driver.from_env()
        >>>
        >>> # Get all users
        >>> users = client.list_objects()
        >>> user_fields = client.get_fields("User")
        >>>
        >>> # Query users
        >>> result = client.read("User", limit=50)
        >>> print(f"Found {len(result)} users")
        >>>
        >>> # Cleanup
        >>> client.close()
    """

    # Fidoo API objects (discoverable via list_objects)
    FIDOO_OBJECTS = [
        "User",
        "Card",
        "Transaction",
        "CardTransaction",
        "Expense",
        "ExpenseItem",
        "CashTransaction",
        "TravelReport",
        "TravelRequest",
        "TravelDetail",
        "PersonalBilling",
        "MVCTransaction",
        "CostCenter",
        "Project",
        "AccountAssignment",
        "Vehicle",
        "VATBreakdown",
    ]

    # Map object names to API endpoints
    OBJECT_ENDPOINTS = {
        "User": "/user/get-users",
        "Card": "/card/get-cards",
        "Transaction": "/transaction/get-card-transactions",
        "CardTransaction": "/transaction/get-card-transactions",
        "Expense": "/expense/get-expenses",
        "ExpenseItem": "/expense/get-expense-items",
        "CashTransaction": "/cash-transactions/get-cash-transactions",
        "TravelReport": "/travel/get-travel-reports",
        "TravelRequest": "/travel/get-travel-requests",
        "PersonalBilling": "/personal-billing/get-billings",
        "MVCTransaction": "/mvc-transaction/get-transactions",
        "CostCenter": "/settings/get-cost-centers",
        "Project": "/settings/get-projects",
        "AccountAssignment": "/settings/get-account-assignments",
        "Vehicle": "/settings/get-vehicles",
        "VATBreakdown": "/settings/get-vat-breakdowns",
    }

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        debug: bool = False,
        **kwargs
    ):
        """
        Initialize Fidoo8Driver.

        CRITICAL: Initialization follows strict 4-phase order!
        See: IMPLEMENTATION_NOTES.md - Initialization Order

        Args:
            base_url: Fidoo API base URL (default: https://api.fidoo.com/v2)
            api_key: API key for authentication (or set FIDOO_API_KEY env var)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Max retries on rate limit (default: 3)
            debug: Enable debug logging (default: False)

        Raises:
            AuthenticationError: If API key is invalid or missing
            ConnectionError: If API is unreachable

        Example:
            >>> # Recommended: use from_env()
            >>> driver = Fidoo8Driver.from_env()
            >>>
            >>> # Or explicit credentials
            >>> driver = Fidoo8Driver(
            ...     base_url="https://api-demo.fidoo.com/v2",
            ...     api_key="your_api_key"
            ... )
        """

        # ===== PHASE 1: Set custom attributes =====
        self.driver_name = "Fidoo8Driver"
        self.api_version = "v2"

        # Setup logging
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG if debug else logging.WARNING)

        # ===== PHASE 2: Set parent class attributes =====
        # DO NOT call super().__init__()! Set attributes manually instead.
        resolved_base_url = base_url or "https://api.fidoo.com/v2"
        self.api_url = resolved_base_url.rstrip("/")  # Remove trailing slash
        self.base_url = self.api_url  # For compatibility with BaseDriver
        self.api_key = api_key
        self.timeout = timeout or 30
        self.max_retries = max_retries or 3
        self.debug = debug

        # ===== PHASE 3: Create session =====
        self.session = self._create_session()

        # ===== PHASE 4: Validate connection =====
        self._validate_connection()

    @classmethod
    def from_env(cls, **kwargs) -> "Fidoo8Driver":
        """
        Create driver instance from environment variables.

        Environment Variables:
            FIDOO_API_KEY: API key (required)
            FIDOO_BASE_URL: API base URL (optional, defaults to production)
            FIDOO_TIMEOUT: Request timeout in seconds (optional)
            FIDOO_MAX_RETRIES: Max retries on rate limit (optional)
            FIDOO_DEBUG: Enable debug mode "true"/"false" (optional)

        Returns:
            Configured Fidoo8Driver instance

        Raises:
            AuthenticationError: If FIDOO_API_KEY is not set

        Example:
            >>> # Set environment variables first:
            >>> # export FIDOO_API_KEY="your_key_here"
            >>> # export FIDOO_BASE_URL="https://api-demo.fidoo.com/v2"
            >>>
            >>> driver = Fidoo8Driver.from_env()
            >>> users = driver.read("User", limit=10)
        """
        api_key = os.getenv("FIDOO_API_KEY")
        if not api_key:
            raise AuthenticationError(
                "Missing Fidoo API key. Set FIDOO_API_KEY environment variable.",
                details={
                    "required_env_vars": ["FIDOO_API_KEY"],
                    "optional_env_vars": [
                        "FIDOO_BASE_URL",
                        "FIDOO_TIMEOUT",
                        "FIDOO_MAX_RETRIES",
                        "FIDOO_DEBUG",
                    ],
                    "how_to_get_api_key": "Generate in Fidoo app: Main Administrator → API Keys",
                },
            )

        base_url = os.getenv("FIDOO_BASE_URL")
        timeout = int(os.getenv("FIDOO_TIMEOUT", "30"))
        max_retries = int(os.getenv("FIDOO_MAX_RETRIES", "3"))
        debug = os.getenv("FIDOO_DEBUG", "false").lower() in ("true", "1", "yes")

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
            DriverCapabilities with supported operations
        """
        return DriverCapabilities(
            read=True,
            write=True,
            update=True,
            delete=True,
            batch_operations=False,
            streaming=False,
            pagination=PaginationStyle.CURSOR,
            query_language=None,  # REST API, not SQL/SOQL
            max_page_size=100,
            supports_transactions=False,
            supports_relationships=True,
        )

    # ===== Discovery Methods =====

    def list_objects(self) -> List[str]:
        """
        Discover all available Fidoo objects.

        Returns:
            List of object names (User, Card, Transaction, Expense, etc.)

        Example:
            >>> driver = Fidoo8Driver.from_env()
            >>> objects = driver.list_objects()
            >>> print(objects)
            ['User', 'Card', 'Transaction', 'Expense', ...]
        """
        return self.FIDOO_OBJECTS

    def get_fields(self, object_name: str) -> Dict[str, Any]:
        """
        Get field schema for a Fidoo object.

        Args:
            object_name: Name of object (e.g., "User", "Card", "Expense")

        Returns:
            Dictionary mapping field names to field metadata

        Raises:
            ObjectNotFoundError: If object doesn't exist

        Example:
            >>> driver = Fidoo8Driver.from_env()
            >>> fields = driver.get_fields("User")
            >>> print(fields.keys())
            dict_keys(['userId', 'firstName', 'lastName', 'email', ...])

            >>> # Check field details
            >>> print(fields['email']['type'])
            'string'
        """
        if object_name not in self.FIDOO_OBJECTS:
            raise ObjectNotFoundError(
                f"Object '{object_name}' not found in Fidoo API",
                details={
                    "requested": object_name,
                    "available": self.FIDOO_OBJECTS,
                    "suggestion": "Call list_objects() to see available objects",
                },
            )

        # Return schema for known objects
        # These are extracted from API documentation
        schemas = {
            "User": {
                "userId": {"type": "string", "description": "Unique user identifier (UUID)"},
                "firstName": {"type": "string", "description": "User's first name"},
                "lastName": {"type": "string", "description": "User's last name"},
                "email": {"type": "string", "description": "User's email address"},
                "phone": {"type": "string", "description": "User's phone number"},
                "employeeNumber": {"type": "string", "description": "Employee number"},
                "Position": {"type": "string", "description": "User's position"},
                "userState": {
                    "type": "enum",
                    "values": ["active", "deleted", "new"],
                    "description": "User status",
                },
                "deactivated": {"type": "boolean", "description": "Is user deactivated"},
                "usesApplication": {"type": "boolean", "description": "Has app access"},
                "kycStatus": {
                    "type": "enum",
                    "values": ["unknown", "ok", "failed", "refused"],
                    "description": "KYC status",
                },
                "language": {"type": "string", "description": "Application language"},
                "companyId": {"type": "string", "description": "Company identifier"},
                "LastModified": {"type": "datetime", "description": "Last modification date"},
            },
            "Card": {
                "cardId": {"type": "string", "description": "Unique card identifier (UUID)"},
                "cardState": {
                    "type": "enum",
                    "values": ["first-ordered", "active", "hard-blocked", "soft-blocked", "expired"],
                    "description": "Card status",
                },
                "cardType": {"type": "enum", "values": ["personal", "shared"], "description": "Card type"},
                "maskedNumber": {"type": "string", "description": "Masked PAN"},
                "embossName": {"type": "string", "description": "Cardholder name"},
                "alias": {"type": "string", "description": "Optional card alias"},
                "expiration": {"type": "date", "description": "Card expiry date"},
                "availableBalance": {"type": "number", "description": "Available balance"},
                "accountingBalance": {"type": "number", "description": "Accounting balance"},
                "blockedBalance": {"type": "number", "description": "Blocked balance"},
                "userId": {"type": "string", "description": "Card owner user ID"},
                "connectedUserIds": {"type": "string", "description": "Connected user IDs (team card)"},
            },
            "Expense": {
                "expenseId": {"type": "string", "description": "Unique expense identifier"},
                "ownerUserId": {"type": "string", "description": "Expense owner user ID"},
                "dateTime": {"type": "datetime", "description": "Expense timestamp"},
                "lastEditDateTime": {"type": "datetime", "description": "Last edit timestamp"},
                "name": {"type": "string", "description": "Expense name"},
                "amount": {"type": "number", "description": "Expense amount"},
                "amountCzk": {"type": "number", "description": "Amount in CZK"},
                "currency": {"type": "string", "description": "Currency code"},
                "shortId": {"type": "string", "description": "Short expense ID (e.g., EX-10)"},
                "state": {
                    "type": "enum",
                    "values": ["prepare", "approve", "approve2", "accountantApprove", "personalBill", "export", "exported"],
                    "description": "Expense state",
                },
                "type": {"type": "enum", "values": ["manual", "card-transaction"], "description": "Expense type"},
                "closed": {"type": "boolean", "description": "Is expense closed"},
            },
            "Transaction": {
                "id": {"type": "string", "description": "Transaction ID"},
                "cardId": {"type": "string", "description": "Card ID"},
                "expenseId": {"type": "string", "description": "Related expense ID"},
                "cardEmbossName": {"type": "string", "description": "Card holder name"},
                "transactionDate": {"type": "datetime", "description": "Transaction date"},
                "settlementDate": {"type": "datetime", "description": "Settlement date"},
                "originalAmount": {"type": "number", "description": "Original amount"},
                "originalCurrency": {"type": "string", "description": "Original currency"},
                "signedAmount": {"type": "number", "description": "Signed amount in CZK"},
                "transactionStatus": {"type": "string", "description": "Transaction status"},
                "merchantName": {"type": "string", "description": "Merchant name"},
                "merchantLocation": {"type": "string", "description": "Merchant location"},
                "categoryName": {"type": "string", "description": "Merchant category"},
            },
        }

        return schemas.get(object_name, {"_note": f"Schema for {object_name} not fully documented"})

    # ===== Read Operations =====

    def read(
        self,
        query: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a read operation on a Fidoo object.

        Fidoo API uses object names instead of query language.

        Args:
            query: Object name (e.g., "User", "Card", "Expense")
                   Or empty string to use the last queried object
            limit: Maximum number of records (default: 50, max: 100)
            offset: For compatibility (Fidoo uses cursor tokens, not offset)

        Returns:
            List of records

        Raises:
            ObjectNotFoundError: If object doesn't exist
            ValidationError: If parameters are invalid
            RateLimitError: If rate limited (after retries)
            ConnectionError: If API unreachable

        Example:
            >>> driver = Fidoo8Driver.from_env()
            >>>
            >>> # Get users
            >>> users = driver.read("User", limit=50)
            >>> print(f"Got {len(users)} users")
            >>>
            >>> # Get cards
            >>> cards = driver.read("Card", limit=100)
            >>>
            >>> # Paginate through users
            >>> all_users = []
            >>> for batch in driver.read_batched("User", batch_size=50):
            ...     all_users.extend(batch)
        """
        object_name = query.strip() if query else ""
        if not object_name:
            raise ValidationError(
                "Query (object name) cannot be empty",
                details={"available_objects": self.FIDOO_OBJECTS},
            )

        if object_name not in self.FIDOO_OBJECTS:
            raise ObjectNotFoundError(
                f"Object '{object_name}' not found",
                details={"requested": object_name, "available": self.FIDOO_OBJECTS},
            )

        # Validate page size
        limit = limit or 50
        if limit > 100:
            raise ValidationError(
                f"limit cannot exceed 100 (got: {limit})",
                details={"provided": limit, "maximum": 100},
            )

        # Get endpoint for object
        endpoint = self.OBJECT_ENDPOINTS.get(object_name)
        if not endpoint:
            raise ObjectNotFoundError(f"No endpoint configured for object '{object_name}'")

        # Call endpoint
        return self._call_endpoint_paginated(endpoint, limit=limit)

    def read_batched(
        self,
        query: str,
        batch_size: int = 50,
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Execute read operation and yield results in batches (memory-efficient).

        Args:
            query: Object name (e.g., "User", "Card", "Expense")
            batch_size: Records per batch (default: 50, max: 100)

        Yields:
            Batches of records

        Example:
            >>> driver = Fidoo8Driver.from_env()
            >>> total = 0
            >>> for batch in driver.read_batched("User", batch_size=50):
            ...     process_batch(batch)
            ...     total += len(batch)
            >>> print(f"Processed {total} users")
        """
        object_name = query.strip() if query else ""
        if not object_name:
            raise ValidationError("Query (object name) cannot be empty")

        if object_name not in self.FIDOO_OBJECTS:
            raise ObjectNotFoundError(f"Object '{object_name}' not found")

        if batch_size > 100:
            raise ValidationError(f"batch_size cannot exceed 100 (got: {batch_size})")

        endpoint = self.OBJECT_ENDPOINTS.get(object_name)
        if not endpoint:
            raise ObjectNotFoundError(f"No endpoint configured for object '{object_name}'")

        # Fetch in batches using cursor pagination
        offset_token = None
        while True:
            params = {"limit": batch_size}
            if offset_token:
                params["offsetToken"] = offset_token

            response = self._api_call(endpoint, params=params)
            records = response if isinstance(response, list) else response.get("items", [])

            if records:
                yield records

            # Check for more data
            next_token = response.get("nextOffsetToken") if isinstance(response, dict) else None
            if not next_token:
                break

            offset_token = next_token

    # ===== Write Operations =====

    def create(self, object_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record.

        Args:
            object_name: Object type (e.g., "User")
            data: Field values as dictionary

        Returns:
            Created record with ID

        Raises:
            NotImplementedError: For unsupported objects
            ValidationError: If data is invalid
            ConnectionError: If API fails

        Example:
            >>> driver = Fidoo8Driver.from_env()
            >>> new_user = driver.create("User", {
            ...     "firstName": "John",
            ...     "lastName": "Doe",
            ...     "email": "john@example.com"
            ... })
            >>> print(f"Created user: {new_user['userId']}")
        """
        if object_name == "User":
            return self._api_call("/user/add-user", method="POST", json=data)
        else:
            raise NotImplementedError(f"Create not supported for {object_name}")

    def update(self, object_name: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing record.

        Args:
            object_name: Object type (e.g., "Expense")
            record_id: ID of record to update
            data: Field values to update

        Returns:
            Updated record

        Raises:
            NotImplementedError: For unsupported objects
        """
        if object_name == "Expense":
            payload = {**data, "expenseId": record_id}
            return self._api_call("/expense/edit-expense", method="POST", json=payload)
        else:
            raise NotImplementedError(f"Update not supported for {object_name}")

    def delete(self, object_name: str, record_id: str) -> bool:
        """
        Delete a record.

        Args:
            object_name: Object type (e.g., "User")
            record_id: ID of record to delete

        Returns:
            True if successful

        Raises:
            NotImplementedError: If delete not supported
        """
        if object_name == "User":
            self._api_call("/user/delete-user", method="POST", json={"userId": record_id})
            return True
        else:
            raise NotImplementedError(f"Delete not supported for {object_name}")

    # ===== Internal Methods =====

    def _create_session(self) -> requests.Session:
        """
        Create HTTP session with authentication and retry configuration.

        Returns:
            Configured requests.Session

        Critical: Bug Prevention Pattern #2
        - Do NOT set Content-Type in session headers
        - Let requests library handle it automatically
        """
        session = requests.Session()

        # Set headers that apply to ALL requests
        session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": f"{self.driver_name}-Python-Driver/1.0.0",
            }
        )
        # NOTE: Do NOT set Content-Type here - affects GET requests

        # Add authentication
        # Bug Prevention Pattern #1: Use EXACT header name X-Api-Key
        if self.api_key:
            session.headers["X-Api-Key"] = self.api_key

        # Configure retries for rate limiting
        # Retry on 429, 500, 502, 503, 504
        retry_strategy = requests.adapters.Retry(
            total=self.max_retries,
            backoff_factor=1,  # Exponential backoff: 1s, 2s, 4s, ...
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _validate_connection(self):
        """
        Validate connection at initialization (fail fast).

        Raises:
            AuthenticationError: If credentials invalid
            ConnectionError: If API unreachable
        """
        try:
            # Try a simple endpoint to validate auth
            self._api_call("/user/get-users", params={"limit": 1})
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Invalid Fidoo API key. Check your credentials.",
                    details={"api_url": self.api_url, "status_code": 401},
                )
            elif e.response.status_code == 403:
                raise AuthenticationError(
                    "API key lacks required permissions.",
                    details={"api_url": self.api_url, "status_code": 403},
                )
            raise ConnectionError(f"Cannot connect to Fidoo API: {e}")
        except requests.RequestException as e:
            raise ConnectionError(
                f"Cannot reach Fidoo API at {self.api_url}: {e}",
                details={"api_url": self.api_url, "error": str(e)},
            )

    def _api_call(
        self,
        endpoint: str,
        method: str = "POST",
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make API call with error handling and logging.

        Args:
            endpoint: API endpoint path (relative to base_url)
            method: HTTP method
            params: Query parameters
            json: Request body (JSON)
            **kwargs: Additional requests options

        Returns:
            Response data as dictionary

        Raises:
            AuthenticationError: 401 or 403
            ValidationError: 400
            RateLimitError: 429 (after retries)
            ConnectionError: Network errors or 5xx
        """
        url = urljoin(self.api_url + "/", endpoint.lstrip("/"))

        if self.debug:
            self.logger.debug(f"[{method}] {url} params={params}")

        try:
            response = self.session.request(
                method,
                url,
                params=params,
                json=json,
                timeout=self.timeout,
                **kwargs,
            )
            response.raise_for_status()

            # Parse response
            try:
                data = response.json()
            except ValueError:
                return {"status": "ok", "raw": response.text}

            return self._parse_response(data)

        except requests.HTTPError as e:
            self._handle_http_error(e, endpoint=endpoint)

        except requests.Timeout:
            raise TimeoutError(
                f"Request timed out after {self.timeout} seconds",
                details={"timeout": self.timeout, "endpoint": endpoint},
            )

        except requests.RequestException as e:
            raise ConnectionError(
                f"API request failed: {e}",
                details={"endpoint": endpoint, "error": str(e)},
            )

    def _parse_response(self, data: Any) -> Dict[str, Any]:
        """
        Parse API response and extract data.

        Fidoo API returns varying response structures:
        - Some endpoints return direct arrays
        - Some wrap data with pagination metadata

        Bug Prevention Pattern #3: Try all documented field names

        Args:
            data: Response JSON

        Returns:
            Parsed data (always returns dict or list)
        """
        # Handle direct list response
        if isinstance(data, list):
            return {"items": data}

        # Handle object response
        if isinstance(data, dict):
            # Try all known wrapper field names (case-sensitive!)
            # Bug Prevention: Check multiple patterns
            records = (
                data.get("items")  # Most common
                or data.get("data")
                or data.get("result")
                or data.get("results")
                or data  # Return as-is if no wrapper
            )
            return records if isinstance(records, dict) else {"items": records or []}

        return {"items": []}

    def _call_endpoint_paginated(
        self,
        endpoint: str,
        limit: int = 50,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Call endpoint and return all records (handling pagination).

        Args:
            endpoint: API endpoint path
            limit: Records per request
            **kwargs: Additional params

        Returns:
            All records from endpoint
        """
        all_records = []
        offset_token = None

        while True:
            params = {"limit": limit, **kwargs}
            if offset_token:
                params["offsetToken"] = offset_token

            response = self._api_call(endpoint, params=params)

            # Extract records from response
            records = response if isinstance(response, list) else response.get("items", [])
            all_records.extend(records)

            # Check for more data
            next_token = response.get("nextOffsetToken") if isinstance(response, dict) else None
            if not next_token:
                break

            offset_token = next_token

        return all_records

    def _handle_http_error(self, error: requests.HTTPError, endpoint: str = ""):
        """
        Convert HTTP errors to driver exceptions.

        Args:
            error: HTTP error from requests
            endpoint: API endpoint for context

        Raises:
            Appropriate DriverError subclass
        """
        status_code = error.response.status_code

        try:
            error_data = error.response.json()
            error_msg = error_data.get("error", error_data.get("message", "Unknown error"))
        except ValueError:
            error_msg = error.response.text[:500]

        if status_code == 401:
            raise AuthenticationError(
                f"Authentication failed: {error_msg}",
                details={"status_code": 401, "endpoint": endpoint},
            )

        elif status_code == 403:
            raise AuthenticationError(
                f"Permission denied: {error_msg}",
                details={"status_code": 403, "endpoint": endpoint},
            )

        elif status_code == 400:
            raise ValidationError(
                f"Bad request: {error_msg}",
                details={"status_code": 400, "endpoint": endpoint},
            )

        elif status_code == 429:
            retry_after = error.response.headers.get("Retry-After", "60")
            raise RateLimitError(
                f"API rate limit exceeded: {error_msg}",
                details={
                    "status_code": 429,
                    "retry_after": int(retry_after),
                    "endpoint": endpoint,
                },
            )

        elif status_code >= 500:
            raise ConnectionError(
                f"API server error (HTTP {status_code}): {error_msg}",
                details={"status_code": status_code, "endpoint": endpoint},
            )

        else:
            raise DriverError(
                f"API request failed (HTTP {status_code}): {error_msg}",
                details={"status_code": status_code, "endpoint": endpoint},
            )

    def close(self):
        """Close session and cleanup resources."""
        if self.session:
            self.session.close()

    def __del__(self):
        """Cleanup on object deletion."""
        try:
            self.close()
        except Exception:
            pass
