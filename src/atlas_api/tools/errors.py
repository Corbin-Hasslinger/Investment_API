
class PortfolioNotFoundError(Exception):
    """Exception raised when a portfolio is not found."""
    pass
class PortfolioAlreadyExistsError(Exception):
    """Exception raised when a portfolio already exists."""
    pass

class InvalidPortfolioDataError(Exception):
    """Exception raised when the provided portfolio data is invalid."""
    pass