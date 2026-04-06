"""Core conversational agent for JuiceBot 2.0."""

from __future__ import annotations

import logging
import random
import time
from typing import Any

import openai

from src.config import Config
from src.commands import handle_help, handle_run, handle_status, handle_reset

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are JuiceBot, an autonomous AI agent specialised in task automation, "
    "web search, code generation, data analysis, and file management. "
    "Respond clearly and concisely. Use markdown formatting when appropriate."
)


class Agent:
    """JuiceBot conversational agent with command routing and retry logic."""

    def __init__(self, config: Config | None = None, api_key: str | None = None) -> None:
        self.config = config or Config()
        self.history: list[dict[str, str]] = []
        self.active: bool = True

        self._client = openai.OpenAI(api_key=api_key)
        self._command_handlers = {
            "help": handle_help,
            "status": handle_status,
            "reset": handle_reset,
            "run": handle_run,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, user_input: str) -> str:
        """Route *user_input* to a command handler or the LLM."""
        user_input = user_input.strip()
        if not user_input:
            return ""

        tokens = user_input.split(maxsplit=1)
        command = tokens[0].lower()

        if command in self._command_handlers:
            args = tokens[1].split() if len(tokens) > 1 else []
            logger.debug("Dispatching command '%s' with args %s", command, args)
            return self._command_handlers[command](self, *args)

        return self.chat(user_input)

    def chat(self, message: str) -> str:
        """Send *message* to the LLM and return the assistant reply."""
        self.history.append({"role": "user", "content": message})
        reply = self._call_with_retry()
        self.history.append({"role": "assistant", "content": reply})
        return reply

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_messages(self) -> list[dict[str, str]]:
        history = self.history[-self.config.max_history_messages :]
        return [{"role": "system", "content": _SYSTEM_PROMPT}] + history

    def _call_with_retry(self) -> str:
        last_error: Exception | None = None
        timeout_s = self.config.timeout / 1000
        messages = self._build_messages()

        for attempt in range(1, self.config.retry_attempts + 1):
            try:
                response: Any = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,  # type: ignore[arg-type]
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    timeout=timeout_s,
                )
                return response.choices[0].message.content or ""
            except openai.RateLimitError as exc:
                last_error = exc
                wait = random.uniform(1, 2**attempt)
                logger.warning("Rate limit hit (attempt %d/%d); retrying in %.1fs", attempt, self.config.retry_attempts, wait)
                time.sleep(wait)
            except openai.APITimeoutError as exc:
                last_error = exc
                logger.warning("Request timed out (attempt %d/%d)", attempt, self.config.retry_attempts)
            except openai.OpenAIError as exc:
                last_error = exc
                logger.error("OpenAI error on attempt %d: %s", attempt, exc)
                break

        raise RuntimeError(f"Failed after {self.config.retry_attempts} attempt(s): {last_error}") from last_error
