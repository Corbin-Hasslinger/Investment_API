from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from atlas_api.models import Security
from atlas_api.services.security_service import SecurityService
from atlas_api.tools.errors import InvalidSymbolFormatError, UnsupportedSymbolError


@pytest.fixture
def security_service(security_repository, finnhub_client):
    """Create a SecurityService with mocked dependencies."""
    return SecurityService(
        security_repository=security_repository,
        finnhub_client=finnhub_client,
    )


class TestNormalizeSymbol:
    """Test suite for normalize_symbol normalization behavior."""

    def test_normalize_symbol_whitespace_trim(self, security_service):
        assert security_service.normalize_symbol("aapl") == "AAPL"
        assert security_service.normalize_symbol(" aapl") == "AAPL"
        assert security_service.normalize_symbol("aapl ") == "AAPL"
        assert security_service.normalize_symbol(" aapl ") == "AAPL"

    def test_normalize_symbol_case_conversion(self, security_service):
        assert security_service.normalize_symbol("aapl") == "AAPL"
        assert security_service.normalize_symbol("AaPl") == "AAPL"
        assert security_service.normalize_symbol("AAPL") == "AAPL"

    def test_normalize_symbol_valid_lengths(self, security_service):
        assert security_service.normalize_symbol("A") == "A"
        assert security_service.normalize_symbol("MSFT") == "MSFT"
        assert security_service.normalize_symbol("AAPL") == "AAPL"

    def test_normalize_symbol_with_dots(self, security_service):
        assert security_service.normalize_symbol("brk.a") == "BRK.A"
        assert security_service.normalize_symbol("BRK.A") == "BRK.A"

    def test_normalize_symbol_with_hyphens(self, security_service):
        assert security_service.normalize_symbol("brk-b") == "BRK-B"
        assert security_service.normalize_symbol("BRK-B") == "BRK-B"

    def test_normalize_symbol_rejects_empty(self, security_service):
        with pytest.raises(InvalidSymbolFormatError):
            security_service.normalize_symbol("")

    def test_normalize_symbol_rejects_whitespace_only(self, security_service):
        with pytest.raises(InvalidSymbolFormatError):
            security_service.normalize_symbol("   ")

    def test_normalize_symbol_rejects_too_long(self, security_service):
        with pytest.raises(InvalidSymbolFormatError):
            security_service.normalize_symbol("TOOLONG1234")

    def test_normalize_symbol_rejects_invalid_characters(self, security_service):
        with pytest.raises(InvalidSymbolFormatError):
            security_service.normalize_symbol("AAPL$")
        
        with pytest.raises(InvalidSymbolFormatError):
            security_service.normalize_symbol("AAPL1")

    def test_normalize_symbol_rejects_spaces_in_middle(self, security_service):
        with pytest.raises(InvalidSymbolFormatError):
            security_service.normalize_symbol("AA PL")

class TestResolveSecurityWithMocks:
    """Test suite for resolve_security with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_resolve_security_returns_existing_security(
        self,
        security_repository: MagicMock,
        security_service: SecurityService,
    ):
        """When Security exists locally, return it without calling Finnhub."""
        existing = Security(
            id=uuid4(),
            symbol="AAPL",
            name="Apple Inc",
            exchange="NASDAQ",
            currency="USD",
        )
        security_repository.get_security_by_symbol.return_value = existing

        result = await security_service.resolve_security("aapl")

        assert result.id == existing.id
        assert result.symbol == "AAPL"
        security_repository.get_security_by_symbol.assert_called_once_with("AAPL")

    @pytest.mark.asyncio
    async def test_resolve_security_creates_new_security_if_valid_upstream(
        self,
        security_repository: MagicMock,
        finnhub_client: MagicMock,
        security_service: SecurityService,
    ):
        """When Security missing but valid upstream, create and return it."""
        security_repository.get_security_by_symbol.return_value = None
        # Mock successful Finnhub response
        finnhub_client.symbol_lookup = AsyncMock(return_value={
            "name": "Microsoft Corporation",
            "exchange": "NASDAQ",
            "currency": "USD",
        })
        created = Security(
            id=uuid4(),
            symbol="MSFT",
            name="Microsoft Corporation",
            exchange="NASDAQ",
            currency="USD",
        )
        security_repository.create_security.return_value = created

        result = await security_service.resolve_security("msft")

        assert result.symbol == "MSFT"
        security_repository.create_security.assert_called_once()
        security_repository.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_resolve_security_raises_unsupported_if_not_found_upstream(
        self,
        security_repository: MagicMock,
        finnhub_client: MagicMock,
        security_service: SecurityService,
    ):
        """When Security missing and invalid upstream, raise UnsupportedSymbolError."""
        security_repository.get_security_by_symbol.return_value = None
        finnhub_client.symbol_lookup = AsyncMock(side_effect=UnsupportedSymbolError(
            "FAKEZZ not found on Finnhub"
        ))

        with pytest.raises(UnsupportedSymbolError):
            await security_service.resolve_security("fakezz")

        security_repository.create_security.assert_not_called()

    @pytest.mark.asyncio
    async def test_resolve_security_rejects_incomplete_upstream_profile(
        self,
        security_repository: MagicMock,
        finnhub_client: MagicMock,
        security_service: SecurityService,
    ):
        """Incomplete upstream data must not be persisted as a Security."""
        security_repository.get_security_by_symbol.return_value = None
        finnhub_client.symbol_lookup = AsyncMock(
            return_value={
                "name": "Apple Inc.",
                "exchange": "",
                "currency": "USD",
            }
        )

        with pytest.raises(UnsupportedSymbolError):
            await security_service.resolve_security("AAPL")

        security_repository.create_security.assert_not_called()
        security_repository.commit.assert_not_called()
        security_repository.refresh.assert_not_called()