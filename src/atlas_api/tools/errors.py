class PortfolioNotFoundError(Exception):
    """Exception raised when a portfolio is not found."""


class PortfolioAlreadyExistsError(Exception):
    """Exception raised when a portfolio already exists."""


class InvalidPortfolioDataError(Exception):
    """Exception raised when the provided portfolio data is invalid."""


class PositionAlreadyExistsError(Exception):
    """Exception raised when a position already exists."""


class PositionNotFoundError(Exception):
    """Exception raised when a position is not found."""


class InvalidPositionDataError(Exception):
    """Exception raised when the provided position data is invalid."""


class SecurityAlreadyExistsError(Exception):
    """Exception raised when a security already exists."""


class SecurityNotFoundError(Exception):
    """Exception raised when a security is not found."""


class InvalidSecurityDataError(Exception):
    """Exception raised when the provided security data is invalid."""


class InvalidSymbolFormatError(Exception):
    """Exception raised when a stock symbol has an invalid format."""


class UnsupportedSymbolError(Exception):
    """Exception raised when a stock symbol is not supported."""


class UpstreamTimeoutError(Exception):
    """Exception raised when an upstream API call times out."""


class UpstreamRateLimitedError(Exception):
    """Exception raised when an upstream API call is rate-limited."""


class UpstreamUnavailableError(Exception):
    """Exception raised when an upstream API is unavailable."""


class UpstreamResponseError(Exception):
    """Exception raised when an upstream API returns an unexpected response."""
