from uuid import uuid4

import pytest
from pydantic import ValidationError

from atlas_api.schemas.ai import (
    PortfolioExplanationRead,
    SecurityExplanationContent,
    SecurityExplanationRead,
)


def test_valid_portfolio_explanation_is_accepted():
    payload = {
        "portfolio_id": str(uuid4()),
        "data_retrieved_at": "2026-08-28T12:00:00Z",
        "generated_at": "2026-08-28T12:00:05Z",
        "explanation": {
            "summary": "The portfolio is concentrated in one holding.",
            "strengths": [],
            "risks": [],
            "concentration": [
                {
                    "observation": "AAPL is the largest holding.",
                    "evidence": ["AAPL allocation_percent: 62.50"],
                }
            ],
            "performance": [],
            "limitations": [],
        },
    }

    result = PortfolioExplanationRead.model_validate(payload)

    assert result.portfolio_id
    assert result.data_retrieved_at.tzinfo is not None
    assert result.generated_at.tzinfo is not None


def test_valid_security_explanation_is_accepted():
    payload = {
        "symbol": "AAPL",
        "data_retrieved_at": "2026-08-28T12:00:00Z",
        "generated_at": "2026-08-28T12:00:05Z",
        "explanation": {
            "summary": "The supplied evidence shows strong profitability.",
            "valuation": [],
            "growth_and_profitability": [],
            "financial_health": [],
            "performance": [],
            "recent_developments": [],
            "risks": [],
            "limitations": ["Debt data was unavailable."],
        },
    }

    result = SecurityExplanationRead.model_validate(payload)

    assert result.symbol == "AAPL"
    assert result.explanation.summary


def test_ai_response_rejects_extra_fields():
    payload = {
        "symbol": "AAPL",
        "data_retrieved_at": "2026-08-28T12:00:00Z",
        "generated_at": "2026-08-28T12:00:05Z",
        "unexpected": "not allowed",
        "explanation": {
            "summary": "Summary",
            "valuation": [],
            "growth_and_profitability": [],
            "financial_health": [],
            "performance": [],
            "recent_developments": [],
            "risks": [],
            "limitations": [],
        },
    }

    with pytest.raises(ValidationError):
        SecurityExplanationRead.model_validate(payload)


def test_ai_response_rejects_extra_nested_fields():
    payload = {
        "symbol": "AAPL",
        "data_retrieved_at": "2026-08-28T12:00:00Z",
        "generated_at": "2026-08-28T12:00:05Z",
        "explanation": {
            "summary": "Summary",
            "valuation": [
                {
                    "observation": "Observation",
                    "evidence": ["Evidence"],
                    "unexpected": "not allowed",
                }
            ],
            "growth_and_profitability": [],
            "financial_health": [],
            "performance": [],
            "recent_developments": [],
            "risks": [],
            "limitations": [],
        },
    }

    with pytest.raises(ValidationError):
        SecurityExplanationRead.model_validate(payload)


def test_security_explanation_requires_all_sections():
    payload = {
        "summary": "Summary",
        "valuation": [],
    }

    with pytest.raises(ValidationError):
        SecurityExplanationContent.model_validate(payload)


def test_naive_timestamps_are_rejected():
    payload = {
        "portfolio_id": str(uuid4()),
        "data_retrieved_at": "2026-08-28T12:00:00",
        "generated_at": "2026-08-28T12:00:05",
        "explanation": {
            "summary": "Summary",
            "strengths": [],
            "risks": [],
            "concentration": [],
            "performance": [],
            "limitations": [],
        },
    }

    with pytest.raises(ValidationError):
        PortfolioExplanationRead.model_validate(payload)


def test_security_explanation_rejects_naive_timestamps():
    payload = {
        "symbol": "AAPL",
        "data_retrieved_at": "2026-08-28T12:00:00",
        "generated_at": "2026-08-28T12:00:05",
        "explanation": {
            "summary": "Summary",
            "valuation": [],
            "growth_and_profitability": [],
            "financial_health": [],
            "performance": [],
            "recent_developments": [],
            "risks": [],
            "limitations": [],
        },
    }

    with pytest.raises(ValidationError):
        SecurityExplanationRead.model_validate(payload)


def test_json_serialization():
    payload = {
        "portfolio_id": str(uuid4()),
        "data_retrieved_at": "2026-08-28T12:00:00Z",
        "generated_at": "2026-08-28T12:00:05Z",
        "explanation": {
            "summary": "Summary",
            "strengths": [],
            "risks": [],
            "concentration": [],
            "performance": [],
            "limitations": [],
        },
    }

    result = PortfolioExplanationRead.model_validate(payload)
    dumped = result.model_dump(mode="json")

    assert dumped["portfolio_id"] == str(result.portfolio_id)
    assert dumped["data_retrieved_at"].endswith("Z")
    assert dumped["generated_at"].endswith("Z")


def test_security_json_serialization():
    payload = {
        "symbol": "AAPL",
        "data_retrieved_at": "2026-08-28T12:00:00Z",
        "generated_at": "2026-08-28T12:00:05Z",
        "explanation": {
            "summary": "Summary",
            "valuation": [],
            "growth_and_profitability": [],
            "financial_health": [],
            "performance": [],
            "recent_developments": [],
            "risks": [],
            "limitations": [],
        },
    }

    result = SecurityExplanationRead.model_validate(payload)
    dumped = result.model_dump(mode="json")

    assert dumped["symbol"] == "AAPL"
    assert dumped["data_retrieved_at"].endswith("Z")
    assert dumped["generated_at"].endswith("Z")


def test_ai_json_schemas_are_closed_and_require_all_fields():
    portfolio_schema = PortfolioExplanationRead.model_json_schema()
    security_schema = SecurityExplanationRead.model_json_schema()

    assert portfolio_schema["additionalProperties"] is False
    assert security_schema["additionalProperties"] is False

    definitions = portfolio_schema["$defs"]
    assert definitions["PortfolioExplanationContent"]["additionalProperties"] is False
    assert definitions["ExplanationInsightRead"]["additionalProperties"] is False
    assert set(definitions["PortfolioExplanationContent"]["required"]) == {
        "summary",
        "strengths",
        "risks",
        "concentration",
        "performance",
        "limitations",
    }

    security_definitions = security_schema["$defs"]
    assert security_definitions["SecurityExplanationContent"][
        "additionalProperties"
    ] is False
    assert set(security_definitions["SecurityExplanationContent"]["required"]) == {
        "summary",
        "valuation",
        "growth_and_profitability",
        "financial_health",
        "performance",
        "recent_developments",
        "risks",
        "limitations",
    }
