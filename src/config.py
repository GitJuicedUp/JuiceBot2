"""Configuration loader for JuiceBot, sourced from config/juicebot.manifest.json."""

import json
import os
from pathlib import Path
from typing import Any


_MANIFEST_PATH = Path(__file__).parent.parent / "config" / "juicebot.manifest.json"


def load_manifest(path: Path = _MANIFEST_PATH) -> dict[str, Any]:
    """Load and return the parsed manifest JSON."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


class Config:
    """Runtime configuration derived from the JuiceBot manifest."""

    def __init__(self, manifest: dict[str, Any] | None = None) -> None:
        if manifest is None:
            manifest = load_manifest()

        agent = manifest.get("agent", {})
        cfg = manifest.get("config", {})

        self.name: str = manifest.get("name", "JuiceBot")
        self.version: str = manifest.get("version", "2.0.0")
        self.description: str = manifest.get("description", "")

        self.model: str = os.environ.get("JUICEBOT_MODEL", agent.get("model", "gpt-4"))
        self.max_tokens: int = int(agent.get("maxTokens", 4096))
        self.temperature: float = float(agent.get("temperature", 0.7))
        self.capabilities: list[str] = agent.get("capabilities", [])

        self.log_level: str = cfg.get("logLevel", "info")
        self.timeout: int = int(cfg.get("timeout", 30000))
        self.retry_attempts: int = int(cfg.get("retryAttempts", 3))
        self.output_format: str = cfg.get("outputFormat", "markdown")
        self.max_history_messages: int = int(cfg.get("maxHistoryMessages", 40))
        self.mic_language: str = cfg.get("micLanguage", "en-US")
        self.mic_listen_timeout: int = int(cfg.get("micListenTimeout", 10))
        self.mic_phrase_limit: int = int(cfg.get("micPhraseLimit", 60))

        self.commands: list[dict[str, Any]] = manifest.get("commands", [])

    def command_names(self) -> list[str]:
        return [cmd["name"] for cmd in self.commands]
