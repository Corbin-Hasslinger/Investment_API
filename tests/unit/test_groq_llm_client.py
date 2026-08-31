import json
from collections.abc import Callable, Iterator, Mapping
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    PermissionDeniedError,
    RateLimitError,
)

from atlas_api.clients.groq_llm_client import GroqLLMClient
from atlas_api.schemas.ai import PortfolioExplanationContent
from atlas_api.tools.errors import (
    UpstreamRateLimitedError,
    UpstreamResponseError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)

API_KEY = "test-key"
MODEL = "openai/gpt-oss-120b"
REASONING_EFFORT = "medium"
SCHEMA_NAME = "portfolio_explanation"

# Provider messages carry the key and raw body; Atlas must never surface either.
LEAKY_MESSAGE = f"upstream failure for {API_KEY} with response body"

VALID_CONTENT: dict[str, Any] = {
    "summary": "The portfolio is concentrated.",
    "strengths": [],
    "risks": [],
    "concentration": [],
    "performance": [],
    "limitations": [],
}


def build_response(content: str | None) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def build_status_error(
    error_type: type[APIStatusError], status_code: int
) -> APIStatusError:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(
        status_code, request=request, json={"error": "response body"}
    )
    return error_type(LEAKY_MESSAGE, response=response, body={"key": API_KEY})


def await_kwargs(create: AsyncMock) -> Mapping[str, Any]:
    assert create.await_args is not None
    return create.await_args.kwargs


@pytest.fixture
def groq_constructor() -> Iterator[MagicMock]:
    with patch("atlas_api.clients.groq_llm_client.AsyncGroq") as constructor:
        yield constructor


@pytest.fixture
def create() -> AsyncMock:
    return AsyncMock(return_value=build_response(json.dumps(VALID_CONTENT)))


@pytest.fixture
def client(groq_constructor: MagicMock, create: AsyncMock) -> GroqLLMClient:
    groq_constructor.return_value.chat.completions.create = create
    return GroqLLMClient(
        api_key=API_KEY,
        model=MODEL,
        reasoning_effort=REASONING_EFFORT,
    )


async def generate(client: GroqLLMClient) -> PortfolioExplanationContent:
    return await client.generate_structured(
        system_prompt="System instructions",
        user_prompt="User data",
        output_type=PortfolioExplanationContent,
        schema_name=SCHEMA_NAME,
    )


def test_client_constructs_sdk_with_api_key_and_request_timeout(
    client: GroqLLMClient,
    groq_constructor: MagicMock,
) -> None:
    groq_constructor.assert_called_once_with(
        api_key=API_KEY,
        timeout=GroqLLMClient.REQUEST_TIMEOUT,
    )


@pytest.mark.asyncio
async def test_generate_structured_sends_configured_model_and_reasoning_effort(
    client: GroqLLMClient,
    create: AsyncMock,
) -> None:
    await generate(client)

    create.assert_awaited_once()
    request = await_kwargs(create)
    assert request["model"] == MODEL
    assert request["reasoning_effort"] == REASONING_EFFORT


@pytest.mark.asyncio
async def test_generate_structured_sends_system_and_user_messages(
    client: GroqLLMClient,
    create: AsyncMock,
) -> None:
    await generate(client)

    assert await_kwargs(create)["messages"] == [
        {"role": "system", "content": "System instructions"},
        {"role": "user", "content": "User data"},
    ]


@pytest.mark.asyncio
async def test_generate_structured_requests_strict_json_schema_response_format(
    client: GroqLLMClient,
    create: AsyncMock,
) -> None:
    await generate(client)

    response_format = await_kwargs(create)["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["name"] == SCHEMA_NAME
    assert response_format["json_schema"]["strict"] is True
    assert (
        response_format["json_schema"]["schema"]
        == PortfolioExplanationContent.model_json_schema()
    )


@pytest.mark.asyncio
async def test_generate_structured_returns_parsed_atlas_model(
    client: GroqLLMClient,
) -> None:
    result = await generate(client)

    assert isinstance(result, PortfolioExplanationContent)
    assert result.summary == "The portfolio is concentrated."
    assert result.strengths == []
    assert result.limitations == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        SimpleNamespace(choices=[]),
        build_response(None),
        build_response(""),
        build_response("{not valid json"),
        build_response('{"summary": "Only a summary"}'),
        build_response(json.dumps({**VALID_CONTENT, "unexpected": "not allowed"})),
    ],
    ids=[
        "empty_choices",
        "missing_content",
        "empty_content",
        "invalid_json",
        "incomplete_schema",
        "unexpected_field",
    ],
)
async def test_generate_structured_rejects_malformed_responses(
    client: GroqLLMClient,
    create: AsyncMock,
    response: SimpleNamespace,
) -> None:
    create.return_value = response

    with pytest.raises(UpstreamResponseError):
        await generate(client)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("build_error", "expected_error"),
    [
        (
            lambda: APITimeoutError(request=httpx.Request("POST", "https://groq")),
            UpstreamTimeoutError,
        ),
        (
            lambda: build_status_error(RateLimitError, 429),
            UpstreamRateLimitedError,
        ),
        (
            lambda: APIConnectionError(
                message=LEAKY_MESSAGE,
                request=httpx.Request("POST", "https://groq"),
            ),
            UpstreamUnavailableError,
        ),
        (
            lambda: build_status_error(InternalServerError, 500),
            UpstreamUnavailableError,
        ),
        (
            lambda: build_status_error(BadRequestError, 400),
            UpstreamResponseError,
        ),
        (
            lambda: build_status_error(AuthenticationError, 401),
            UpstreamResponseError,
        ),
        (
            lambda: build_status_error(PermissionDeniedError, 403),
            UpstreamResponseError,
        ),
    ],
    ids=[
        "timeout",
        "rate_limited",
        "connection",
        "internal_server",
        "bad_request",
        "authentication",
        "permission_denied",
    ],
)
async def test_generate_structured_translates_provider_errors(
    client: GroqLLMClient,
    create: AsyncMock,
    build_error: Callable[[], Exception],
    expected_error: type[Exception],
) -> None:
    create.side_effect = build_error()

    with pytest.raises(expected_error) as exc:
        await generate(client)

    message = str(exc.value)
    assert API_KEY not in message
    assert "response body" not in message
