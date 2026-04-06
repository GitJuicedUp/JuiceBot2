#!/usr/bin/env python3
"""JuiceBot 2.0 — CLI entry point."""

import logging
import os
import sys

from src.agent import Agent
from src.config import Config


def _configure_logging(level: str) -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=numeric,
    )


def main() -> None:
    config = Config()
    _configure_logging(config.log_level)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY is not set. LLM calls will fail.", file=sys.stderr)

    agent = Agent(config=config, api_key=api_key)

    print(f"{config.name} v{config.version} — type 'help' for available commands, 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in {"quit", "exit", "bye"}:
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            response = agent.process(user_input)
            print(f"\nJuiceBot: {response}\n")
        except Exception as exc:  # noqa: BLE001
            print(f"\n[Error] {exc}\n", file=sys.stderr)


if __name__ == "__main__":
    main()
