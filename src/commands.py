"""Command handlers for JuiceBot (help, run, status, reset)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agent import Agent

logger = logging.getLogger(__name__)


def handle_help(agent: "Agent", *_args: str) -> str:
    """Return a formatted list of available commands."""
    lines = [f"**{agent.config.name} v{agent.config.version}** — available commands:\n"]
    for cmd in agent.config.commands:
        args_hint = ""
        if "args" in cmd:
            args_hint = " " + " ".join(f"<{a}>" for a in cmd["args"])
        lines.append(f"  `{cmd['name']}{args_hint}` — {cmd['description']}")
    lines.append("\nCapabilities: " + ", ".join(agent.config.capabilities))
    return "\n".join(lines)


def handle_status(agent: "Agent", *_args: str) -> str:
    """Return the current agent status."""
    history_len = len(agent.history)
    return (
        f"**{agent.config.name} Status**\n"
        f"- Model: `{agent.config.model}`\n"
        f"- Temperature: `{agent.config.temperature}`\n"
        f"- Max tokens: `{agent.config.max_tokens}`\n"
        f"- Output format: `{agent.config.output_format}`\n"
        f"- Conversation messages: `{history_len}`\n"
        f"- State: `{'active' if agent.active else 'inactive'}`"
    )


def handle_reset(agent: "Agent", *_args: str) -> str:
    """Clear conversation history and reset agent state."""
    agent.history.clear()
    agent.active = True
    logger.info("Agent state reset.")
    return "Agent state and conversation history have been reset."


def handle_music(agent: "Agent", *args: str) -> str:
    """Generate music from a text prompt using the Lyria 3 API."""
    from src.music import MusicGenerator

    prompt = " ".join(args).strip()
    if not prompt:
        return "Usage: `music <prompt>` — describe the music you want to generate."

    clip = "--clip" in args
    if clip:
        prompt_words = [w for w in args if w != "--clip"]
        prompt = " ".join(prompt_words).strip()
        if not prompt:
            return "Usage: `music [--clip] <prompt>` — describe the music you want to generate."

    import os

    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        return (
            "GOOGLE_CLOUD_PROJECT is not set. "
            "Please set it to your Google Cloud project ID before using the music command."
        )

    logger.info("Generating music: clip=%s, prompt=%s", clip, prompt)

    try:
        generator = MusicGenerator(project=project)
        result = generator.generate(prompt, clip=clip)
        return result
    except RuntimeError as exc:
        return f"Music generation unavailable: {exc}"
    except Exception as exc:  # noqa: BLE001
        logger.error("Music generation failed: %s", exc)
        return f"Music generation failed: {exc}"


def handle_run(agent: "Agent", *args: str) -> str:
    """Execute a named task using the workflow engine."""
    from src.workflow import Workflow

    task = " ".join(args).strip()
    if not task:
        return "Usage: `run <task>` — please provide a task description."

    logger.info("Running task: %s", task)

    def _plan_step() -> str:
        return agent.chat(f"Create a concise, numbered action plan for this task: {task}")

    def _execute_step() -> str:
        return agent.chat(
            f"Now execute the following task step-by-step, using your capabilities "
            f"({', '.join(agent.config.capabilities)}): {task}"
        )

    def _summarize_step() -> str:
        return agent.chat("Summarize the outcome of the task you just completed in 2-3 sentences.")

    workflow = (
        Workflow(name=task)
        .add_step("plan", _plan_step)
        .add_step("execute", _execute_step)
        .add_step("summarize", _summarize_step)
    )

    result = workflow.run()

    if result.success:
        final = result.steps[-1].result or ""
        return f"{final}\n\n---\n_{result.summary()}_"
    else:
        return f"Task failed.\n\n_{result.summary()}_"
