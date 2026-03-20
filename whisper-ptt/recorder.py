"""Mic capture using sounddevice. Records 16kHz mono WAV to a temp file."""

import logging
import tempfile
import threading

import numpy as np
import sounddevice as sd
from scipy.io import wavfile

logger = logging.getLogger(__name__)


class Recorder:
    def __init__(self, sample_rate=16000, channels=1, device=None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self._frames = []
        self._stream = None
        self._lock = threading.Lock()
        self._recording = False

    def start(self):
        """Begin recording from the default microphone."""
        with self._lock:
            if self._recording:
                return
            self._frames = []
            self._recording = True
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device,
                dtype="int16",
                callback=self._audio_callback,
            )
            self._stream.start()
            logger.info("Recording started")

    def stop(self):
        """Stop recording and save to a temporary WAV file.

        Returns the path to the temp WAV, or None if no audio was captured.
        """
        with self._lock:
            if not self._recording:
                return None
            self._recording = False
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None

        if not self._frames:
            logger.warning("No audio frames captured")
            return None

        audio = np.concatenate(self._frames, axis=0)
        fd, path = tempfile.mkstemp(suffix=".wav")
        try:
            wavfile.write(path, self.sample_rate, audio)
        finally:
            import os
            os.close(fd)
        logger.info("Saved recording to %s (%d samples)", path, len(audio))
        return path

    def cancel(self):
        """Cancel recording and discard audio."""
        with self._lock:
            self._recording = False
            self._frames = []
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None
        logger.info("Recording cancelled")

    @property
    def is_recording(self):
        return self._recording

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            logger.warning("sounddevice status: %s", status)
        if self._recording:
            self._frames.append(indata.copy())
