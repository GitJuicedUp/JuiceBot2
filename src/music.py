"""Lyria 3 music generation integration for JuiceBot."""

from __future__ import annotations

import base64
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from google import genai  # type: ignore[import-untyped]

    _GENAI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _GENAI_AVAILABLE = False

_MUSIC_CLIP_MODEL = "lyria-3-clip-preview"
_MUSIC_PRO_MODEL = "lyria-3-pro-preview"

# Directory where generated audio files are saved (relative to repo root)
_OUTPUT_DIR = Path(__file__).parent.parent / "audio" / "music" / "generated"


class MusicGenerator:
    """Generate music from text prompts using the Lyria 3 API on Vertex AI.

    Requires:
    - ``GOOGLE_CLOUD_PROJECT`` env var (or *project* constructor argument)
    - Google Cloud credentials with Vertex AI permissions
    """

    def __init__(
        self,
        project: str | None = None,
        location: str | None = None,
        output_dir: Path | None = None,
    ) -> None:
        if not _GENAI_AVAILABLE:
            raise RuntimeError(
                "google-genai is required for music generation. "
                "Install it with: pip install google-genai"
            )
        self._project = project or os.environ.get("GOOGLE_CLOUD_PROJECT", "")
        self._location = location or os.environ.get("GOOGLE_CLOUD_REGION", "global")
        self._output_dir = output_dir or _OUTPUT_DIR
        self._client: Any = genai.Client(
            vertexai=True, project=self._project, location=self._location
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, prompt: str, clip: bool = False, save: bool = True) -> str:
        """Generate music from *prompt* and return a summary string.

        Parameters
        ----------
        prompt:
            Text description of the music to generate.
        clip:
            When *True*, use the 30-second clip model; otherwise use the
            full-track (up to 3-minute) model.
        save:
            When *True*, write any returned audio data to a file in
            *output_dir* and include the path in the returned summary.

        Returns
        -------
        str
            A human-readable summary including saved file paths and/or
            any text content returned by the model.
        """
        model = _MUSIC_CLIP_MODEL if clip else _MUSIC_PRO_MODEL
        logger.info("Generating music with model '%s', prompt: %s", model, prompt)

        interaction = self._client.interactions.create(model=model, input=prompt)
        return self._process_interaction(interaction, save=save)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_interaction(self, interaction: Any, *, save: bool) -> str:
        """Parse an interaction response and return a summary string."""
        text_parts: list[str] = []
        file_paths: list[str] = []

        for output in interaction.outputs:
            if output.type == "text":
                cleaned = self._clean_text(output.text)
                if cleaned:
                    text_parts.append(cleaned)
            elif output.type == "audio":
                if save:
                    path = self._save_audio(output.data)
                    file_paths.append(str(path))
                    logger.info("Audio saved to: %s", path)

        lines: list[str] = []
        if text_parts:
            lines.extend(text_parts)
        if file_paths:
            lines.append("Generated audio file(s):")
            for fp in file_paths:
                lines.append(f"  {fp}")
        if not lines:
            lines.append("Music generation completed (no audio output returned).")

        return "\n".join(lines)

    @staticmethod
    def _clean_text(text: str) -> str:
        """Remove model-specific section tags and normalise whitespace."""
        text = re.sub(r"\[\[.*?\]\]", "", text)
        text = re.sub(
            r"\s*\[(\d+\.\d+)(?::(\d+\.\d+))?:?\]:?",
            lambda m: f"\n\n[{m.group(1)}:{m.group(2)}] " if m.group(2) else f"\n\n[{m.group(1)}] ",
            text,
        )
        text = text.replace("[:]", "\n\n")
        return text.strip()

    def _save_audio(self, data: str | bytes) -> Path:
        """Decode base64 *data* and write it to a numbered WAV file."""
        self._output_dir.mkdir(parents=True, exist_ok=True)

        # Determine next available index
        existing = sorted(self._output_dir.glob("track_*.wav"))
        idx = len(existing) + 1
        path = self._output_dir / f"track_{idx:04d}.wav"

        raw = base64.b64decode(data) if isinstance(data, str) else data
        path.write_bytes(raw)
        return path
