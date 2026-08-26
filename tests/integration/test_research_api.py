from unittest.mock import AsyncMock, MagicMock

from sqlmodel import select

from atlas_api.clients.finnhub_client import FinnhubClient
from atlas_api.core.db import get_session
from atlas_api.di import get_finnhub_client
from atlas_api.models.positions import Position
from atlas_api.models.securities import Security


def test_get_company_research_uses_real_di_graph_with_mocked_finnhub(
    client,
    override_dependency,
    session,
) -> None:
    finnhub_client = MagicMock(spec=FinnhubClient)
    finnhub_client.get_company_profile = AsyncMock(
        return_value={
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "exchange": "NASDAQ",
            "finnhubIndustry": "Technology",
            "country": "US",
            "currency": "USD",
            "ipo": "1980-12-12",
            "marketCapitalization": "3200.12",
            "shareOutstanding": "15600.50",
        }
    )
    finnhub_client.get_basic_financials = AsyncMock(
        return_value={
            "metric": {
                "peTTM": "31.824",
                "beta": "1.234",
                "epsTTM": "6.421",
            }
        }
    )
    finnhub_client.get_company_news = AsyncMock(
        return_value=[
            {
                "id": 123456,
                "headline": "Apple announces results",
                "source": "Reuters",
                "summary": "Quarterly results released.",
                "url": "https://example.com/news/apple-results",
                "image": "",
                "datetime": 1_724_497_200,
            }
        ]
    )

    def override_session():
        yield session

    override_dependency(get_session, override_session)
    override_dependency(get_finnhub_client, lambda: finnhub_client)

    response = client.get("/research/company/aapl")

    assert response.status_code == 200
    body = response.json()
    assert body["company"]["symbol"] == "AAPL"
    assert body["company"]["name"] == "Apple Inc."
    assert body["company"]["market_cap"] == "3200120000.00"
    assert body["valuation"]["pe_ratio_ttm"] == "31.82"
    assert body["performance"]["beta"] == "1.23"
    assert body["fundamentals"]["eps_ttm"] == "6.42"
    assert body["news"][0]["id"] == 123456
    assert body["news"][0]["image_url"] is None

    finnhub_client.get_company_profile.assert_awaited_once_with("AAPL")
    finnhub_client.get_basic_financials.assert_awaited_once_with("AAPL")
    finnhub_client.get_company_news.assert_awaited_once()
    news_args = finnhub_client.get_company_news.await_args.args
    assert news_args[0] == "AAPL"

    assert session.exec(select(Security)).all() == []
    assert session.exec(select(Position)).all() == []
