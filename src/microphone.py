"""Microphone streaming for JuiceBot — captures speech and returns after each job."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agent import Agent

logger = logging.getLogger(__name__)

try:
    import speech_recognition as sr

    _SR_AVAILABLE = True
except ImportError:
    _SR_AVAILABLE = False


class MicrophoneStream:
    """Continuous microphone listener that returns to listening after each completed job.

    Flow per iteration:
        1. Listen for speech (microphone open)
        2. Transcribe audio via Whisper API (or Google fallback)
        3. Send transcript to agent and wait for the job to finish
        4. Print response, then immediately return to step 1
    """

    def __init__(
        self,
        api_key: str | None = None,
        language: str = "en-US",
        listen_timeout: int = 10,
        phrase_limit: int = 60,
    ) -> None:
        if not _SR_AVAILABLE:
            raise RuntimeError(
                "speech_recognition is required for microphone mode. "
                "Install it with: pip install speechrecognition pyaudio"
            )
        self._api_key = api_key
        self._language = language
        self._listen_timeout = listen_timeout
        self._phrase_limit = phrase_limit
        self._recognizer = sr.Recognizer()
        self._microphone = sr.Microphone()
        self._active = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, agent: "Agent") -> None:
        """Start the listen-process loop; the microphone stream returns after every job."""
        self._active = True
        self._calibrate()
        print("Microphone stream active — speak to interact, say 'quit' to exit.\n")

        while self._active:
            text = self._listen_once()
            if text is None:
                continue

            print(f"You (mic): {text}")

            if text.lower() in {"quit", "exit", "bye", "stop"}:
                print("Goodbye!")
                break

            try:
                response = agent.process(text)
                print(f"\nJuiceBot: {response}\n")
            except Exception as exc:  # noqa: BLE001
                logger.error("Agent error: %s", exc)

            # Job is complete — stream returns here and microphone resumes listening

    def stop(self) -> None:
        """Stop the microphone stream after the current job finishes."""
        self._active = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _calibrate(self) -> None:
        """Adjust recognizer energy threshold for ambient noise."""
        logger.info("Calibrating microphone for ambient noise…")
        with self._microphone as source:
            self._recognizer.adjust_for_ambient_noise(source, duration=1)
        logger.info("Microphone calibrated.")

    def _listen_once(self) -> str | None:
        """Record one utterance and return transcribed text, or None on failure."""
        try:
            with self._microphone as source:
                logger.debug("Listening…")
                audio = self._recognizer.listen(
                    source,
                    timeout=self._listen_timeout,
                    phrase_time_limit=self._phrase_limit,
                )
        except sr.WaitTimeoutError:
            return None

        return self._transcribe(audio)

    def _transcribe(self, audio: "sr.AudioData") -> str | None:
        """Transcribe *audio* using Whisper API when an API key is available, otherwise Google."""
        try:
            if self._api_key:
                text: str = self._recognizer.recognize_whisper_api(
                    audio, api_key=self._api_key, language=self._language
                )
            else:
                text = self._recognizer.recognize_google(audio, language=self._language)
            return text.strip() or None
        except sr.UnknownValueError:
            logger.debug("Speech not understood.")
            return None
        except sr.RequestError as exc:
            logger.error("Transcription request failed: %s", exc)
            return None
