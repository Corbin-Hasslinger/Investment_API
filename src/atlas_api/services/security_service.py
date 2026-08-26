import re

from atlas_api.clients.finnhub_client import FinnhubClient
from atlas_api.models import Security
from atlas_api.repositories import SecurityRepository
from atlas_api.schemas.security import SecurityRead
from atlas_api.tools.errors import (
    InvalidSymbolFormatError,
    SecurityNotFoundError,
    UnsupportedSymbolError,
)

SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z.-]*$")
SYMBOL_MIN_LENGTH = 1
SYMBOL_MAX_LENGTH = 10

class SecurityService:
    def __init__(self, 
                 security_repository: SecurityRepository,
                 finnhub_client: FinnhubClient,
                 ):
        self.security_repository = security_repository
        self.finnhub_client = finnhub_client

    def _to_read(self, model: Security) -> SecurityRead:
        return SecurityRead.model_validate(model, from_attributes=True)
    
    def normalize_symbol(self, symbol: str) -> str:
        """Transform raw user input to canonical symbol format.
        
        Process:
        1. Trim whitespace
        2. Convert to uppercase
        3. Validate length (1-10 chars)
        4. Validate character set (A-Z, dot, hyphen)
        
        Raises:
            InvalidSymbolFormatError: if symbol is invalid after normalization"""
        
        normalized = symbol.upper().strip()
        if not (SYMBOL_MIN_LENGTH <= len(normalized) <= SYMBOL_MAX_LENGTH):
            raise InvalidSymbolFormatError(f"Symbol '{symbol}' must be between {SYMBOL_MIN_LENGTH} and {SYMBOL_MAX_LENGTH} characters long.")
        if not SYMBOL_PATTERN.match(normalized):
            raise InvalidSymbolFormatError(f"Symbol '{symbol}' contains invalid characters. Only letters, dots, and hyphens are allowed.")
        return normalized

    async def resolve_security(self, symbol: str) -> SecurityRead:
        """Resolve a security by its symbol, creating one if necessary and valid.
        
        Command operation: may create a new Security row.
        
        Process:
        1. normalize_symbol(symbol)
        2. Check local database for existing security record
        3. If found: return existing Security
        4. If not found: validate against Finnhub, create Security if valid, return it"""
        
        normalized = self.normalize_symbol(symbol)

        security = self.security_repository.get_security_by_symbol(normalized)
        if security:
            return self._to_read(security)
        
        security_info = await self.finnhub_client.get_company_profile(normalized)
        if not security_info:
            raise UnsupportedSymbolError(
                f"Symbol '{normalized}' is not supported by Finnhub."
            )
                 
        required_fields = ("name", "exchange", "currency")
        if any(not security_info.get(field) for field in required_fields):
            raise UnsupportedSymbolError(
                f"Finnhub returned incomplete profile data for '{normalized}'."
            )

        security = self.security_repository.create_security(
            Security(
                symbol=normalized,
                name=str(security_info["name"]),
                exchange=str(security_info["exchange"]),
                currency=str(security_info["currency"]),
            )
        )
        self.security_repository.commit()
        self.security_repository.refresh(security)
        return self._to_read(security)
    
    def get_security(self, symbol: str) -> SecurityRead:
        """Retrieve a security by its symbol from the database.
        
        Query operation: no database mutation, safe for market-data lookups.
        
        Raises:
            InvalidSymbolFormatError: if the symbol is invalid after normalization
            SecurityNotFoundError: if the security does not exist in the database"""
        
        normalized = self.normalize_symbol(symbol)
        security = self.security_repository.get_security_by_symbol(normalized)
        if not security:
            raise SecurityNotFoundError(f"Security with symbol '{normalized}' not found.")
        return self._to_read(security)
