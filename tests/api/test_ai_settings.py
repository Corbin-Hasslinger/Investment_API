import pytest
from pydantic import SecretStr, ValidationError

from atlas_api.core import config
from atlas_api.core.config import Settings


def test_ai_settings_use_locked_defaults(monkeypatch):
    monkeypatch.setattr(config, "find_env_file", lambda: None)

    settings = Settings(environment="test")

    assert settings.ai_model == "openai/gpt-oss-120b"
    assert settings.ai_reasoning_effort == "medium"
    assert settings.ai_max_completion_tokens == 4096
    assert settings.groq_api_key is None


def test_ai_reasoning_effort_rejects_unknown_values():
    with pytest.raises(ValidationError):
        Settings(
            environment="test",
            ai_reasoning_effort="extreme",
        )


@pytest.mark.parametrize("token_limit", [511, 65537])
def test_ai_max_completion_tokens_rejects_out_of_range_values(token_limit: int):
    with pytest.raises(ValidationError):
        Settings(
            environment="test",
            ai_max_completion_tokens=token_limit,
        )


def test_ai_settings_accept_environment_aliases(monkeypatch):
    monkeypatch.setattr(config, "find_env_file", lambda: None)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL", "test-model")
    monkeypatch.setenv("AI_REASONING_EFFORT", "low")
    monkeypatch.setenv("AI_MAX_COMPLETION_TOKENS", "2048")

    settings = Settings(environment="test")

    assert isinstance(settings.groq_api_key, SecretStr)
    assert settings.groq_api_key.get_secret_value() == "test-key"
    assert settings.ai_model == "test-model"
    assert settings.ai_reasoning_effort == "low"
    assert settings.ai_max_completion_tokens == 2048


def test_groq_api_key_is_required_outside_tests(monkeypatch):
    monkeypatch.setattr(config, "find_env_file", lambda: None)

    with pytest.raises(ValueError, match="GROQ_API_KEY is required"):
        Settings(
            environment="development",
            finnhub_api_key="finnhub-key",
            tickerbot_api_key="tickerbot-key",
        )
