"""Faster-whisper wrapper. Loads model once at startup."""

import logging

from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self, model_size="small.en", device="cpu", compute_type=None):
        if compute_type is None:
            compute_type = "float16" if device == "cuda" else "int8"
        logger.info(
            "Loading whisper model '%s' on %s (compute_type=%s)...",
            model_size, device, compute_type,
        )
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info("Model loaded")

    def transcribe(self, audio_path):
        """Transcribe a WAV file and return the text as a single string."""
        segments, info = self.model.transcribe(audio_path, beam_size=5)
        logger.info(
            "Detected language '%s' (prob %.2f)", info.language, info.language_probability
        )
        text = " ".join(seg.text for seg in segments).strip()
        logger.info("Transcription: %s", text)
        return text
