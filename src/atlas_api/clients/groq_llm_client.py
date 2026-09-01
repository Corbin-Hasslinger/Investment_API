from typing import Literal, cast

from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncGroq,
    RateLimitError,
)
from pydantic import ValidationError

from atlas_api.clients.llm_client import OutputModel
from atlas_api.tools.errors import (
    UpstreamRateLimitedError,
    UpstreamResponseError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)


class GroqLLMClient:
    REQUEST_TIMEOUT = 60.0

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        reasoning_effort: str,
        max_completion_tokens: int,
    ):
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.max_completion_tokens = max_completion_tokens
        self.client = AsyncGroq(
            api_key=api_key,
            timeout=self.REQUEST_TIMEOUT,
        )

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_type: type[OutputModel],
    ) -> OutputModel:
        schema_name = output_type.__name__
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                reasoning_effort=cast(
                    'Literal["none", "default", "low", "medium", "high"]',
                    self.reasoning_effort,
                ),
                max_completion_tokens=self.max_completion_tokens,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "strict": True,
                        "schema": output_type.model_json_schema(),
                    },
                },
            )
        except APITimeoutError as exc:
            raise UpstreamTimeoutError("The Groq AI provider timed out.") from exc
        except RateLimitError as exc:
            raise UpstreamRateLimitedError(
                "The Groq AI provider rate limit was exceeded."
            ) from exc
        except APIConnectionError as exc:
            raise UpstreamUnavailableError(
                "The Groq AI provider could not be reached."
            ) from exc
        except APIStatusError as exc:
            if exc.status_code in {401, 403}:
                raise UpstreamUnavailableError(
                    "The Groq AI provider configuration is unavailable."
                ) from exc

            if exc.status_code >= 500:
                raise UpstreamUnavailableError(
                    "The Groq AI provider is unavailable."
                ) from exc

            raise UpstreamResponseError(
                "The Groq AI provider rejected the request."
            ) from exc

        if not response.choices:
            raise UpstreamResponseError("Groq returned no completion choices.")

        content = response.choices[0].message.content

        if not isinstance(content, str) or not content:
            raise UpstreamResponseError("Groq returned an invalid content format.")

        try:
            return output_type.model_validate_json(content)
        except ValidationError as exc:
            raise UpstreamResponseError(
                "Groq returned a response that did not match the requested schema."
            ) from exc
