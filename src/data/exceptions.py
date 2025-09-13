"""
Custom exceptions for data management components.

Provides specific exception types for better error handling
and debugging in the trading system data pipeline.
"""

from typing import Optional


class DataError(Exception):
    """Base exception for all data-related errors."""

    def __init__(self, message: str, symbol: Optional[str] = None) -> None:
        """Initialize data error.

        Args:
            message: Error description
            symbol: Trading symbol related to error (if applicable)
        """
        self.symbol = symbol
        super().__init__(message)


class DataNotAvailableError(DataError):
    """Raised when requested data is not available."""

    pass


class DataValidationError(DataError):
    """Raised when data fails validation checks."""

    pass


class ExchangeConnectionError(DataError):
    """Raised when connection to exchange fails."""

    pass


class RateLimitExceededError(DataError):
    """Raised when API rate limits are exceeded."""

    pass


class InvalidSymbolError(DataError):
    """Raised when invalid trading symbol is provided."""

    pass


class DataCacheError(DataError):
    """Raised when data caching operations fail."""

    pass
