"""Smoke tests for JuiceBot 2.0 — validate config loading and command routing."""

import json
import pathlib
import types

from src.config import Config, load_manifest


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def test_load_manifest_returns_dict():
    manifest = load_manifest()
    assert isinstance(manifest, dict)
    assert manifest.get("name") == "JuiceBot"
    assert manifest.get("version") == "2.0.0"


def test_config_defaults():
    cfg = Config()
    assert cfg.name == "JuiceBot"
    assert cfg.version == "2.0.0"
    assert cfg.model == "gpt-4"
    assert cfg.max_tokens == 4096
    assert 0.0 <= cfg.temperature <= 1.0
    assert cfg.log_level == "info"
    assert cfg.retry_attempts == 3


def test_config_command_names():
    cfg = Config()
    names = cfg.command_names()
    for expected in ("help", "run", "status", "reset"):
        assert expected in names


def test_config_capabilities():
    cfg = Config()
    assert len(cfg.capabilities) > 0


def test_config_accepts_custom_manifest():
    custom = {
        "name": "TestBot",
        "version": "9.9.9",
        "agent": {"model": "gpt-3.5-turbo", "maxTokens": 512, "temperature": 0.5},
        "config": {
            "logLevel": "debug",
            "timeout": 5000,
            "retryAttempts": 1,
            "outputFormat": "text",
            "maxHistoryMessages": 10,
            "micLanguage": "fr-FR",
            "micListenTimeout": 5,
            "micPhraseLimit": 30,
        },
        "commands": [{"name": "test", "description": "test cmd"}],
    }
    cfg = Config(manifest=custom)
    assert cfg.name == "TestBot"
    assert cfg.version == "9.9.9"
    assert cfg.model == "gpt-3.5-turbo"
    assert cfg.max_tokens == 512
    assert cfg.log_level == "debug"
    assert cfg.retry_attempts == 1


# ---------------------------------------------------------------------------
# Manifest file
# ---------------------------------------------------------------------------

def test_manifest_file_exists():
    manifest_path = pathlib.Path(__file__).parent.parent / "config" / "juicebot.manifest.json"
    assert manifest_path.is_file(), "config/juicebot.manifest.json must exist"


def test_manifest_json_valid():
    manifest_path = pathlib.Path(__file__).parent.parent / "config" / "juicebot.manifest.json"
    with open(manifest_path, encoding="utf-8") as fh:
        data = json.load(fh)
    assert "name" in data
    assert "version" in data
    assert "agent" in data
    assert "commands" in data


# ---------------------------------------------------------------------------
# Command handlers (no LLM required)
# ---------------------------------------------------------------------------

def _make_agent() -> object:
    """Build a minimal fake Agent without an OpenAI client."""
    cfg = Config()

    agent = types.SimpleNamespace(
        config=cfg,
        history=[],
        active=True,
    )
    return agent


def test_handle_help_contains_commands():
    from src.commands import handle_help
    agent = _make_agent()
    output = handle_help(agent)
    assert "help" in output
    assert "run" in output
    assert "status" in output
    assert "reset" in output


def test_handle_status_shows_model():
    from src.commands import handle_status
    agent = _make_agent()
    output = handle_status(agent)
    assert "gpt-4" in output
    assert "active" in output


def test_handle_reset_clears_history():
    from src.commands import handle_reset
    agent = _make_agent()
    agent.history = [{"role": "user", "content": "hi"}]
    output = handle_reset(agent)
    assert agent.history == []
    assert agent.active is True
    assert "reset" in output.lower()
