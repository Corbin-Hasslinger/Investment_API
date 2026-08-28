import pytest
from pydantic import SecretStr, ValidationError

from atlas_api.core import config
from atlas_api.core.config import Settings


def test_ai_settings_use_locked_defaults(monkeypatch):
    monkeypatch.setattr(config, "find_env_file", lambda: None)

    settings = Settings(environment="test")

    assert settings.ai_model == "openai/gpt-oss-120b"
    assert settings.ai_reasoning_effort == "medium"
    assert settings.groq_api_key is None


def test_ai_reasoning_effort_rejects_unknown_values():
    with pytest.raises(ValidationError):
        Settings(
            environment="test",
            ai_reasoning_effort="extreme",
        )


def test_ai_settings_accept_environment_aliases(monkeypatch):
    monkeypatch.setattr(config, "find_env_file", lambda: None)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL", "test-model")
    monkeypatch.setenv("AI_REASONING_EFFORT", "low")

    settings = Settings(environment="test")

    assert isinstance(settings.groq_api_key, SecretStr)
    assert settings.groq_api_key.get_secret_value() == "test-key"
    assert settings.ai_model == "test-model"
    assert settings.ai_reasoning_effort == "low"
