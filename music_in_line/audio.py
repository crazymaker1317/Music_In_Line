"""Audio generation: MIDI file creation and WAV conversion."""

from __future__ import annotations

import os
import tempfile
from typing import List, Optional, Tuple

import numpy as np
import pretty_midi


def events_to_midi(
    events: List[Tuple[float, int, float]],
    bpm: float = 120.0,
    instrument_program: int = 0,
) -> pretty_midi.PrettyMIDI:
    """Convert a list of (start_sec, midi_note, duration_sec) to a PrettyMIDI object."""
    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    instrument = pretty_midi.Instrument(program=instrument_program)

    for start, pitch, duration in events:
        note = pretty_midi.Note(
            velocity=100,
            pitch=int(pitch),
            start=float(start),
            end=float(start + duration),
        )
        instrument.notes.append(note)

    pm.instruments.append(instrument)
    return pm


def midi_to_wav(
    pm: pretty_midi.PrettyMIDI,
    sample_rate: int = 22050,
) -> np.ndarray:
    """Synthesise a PrettyMIDI object to a WAV-compatible numpy array using sine waves."""
    audio = pm.synthesize(fs=sample_rate)
    # Normalize to [-1, 1]
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak
    return audio


def save_midi_file(
    pm: pretty_midi.PrettyMIDI,
    path: Optional[str] = None,
) -> str:
    """Write the PrettyMIDI object to a .mid file and return the path."""
    if path is None:
        fd, path = tempfile.mkstemp(suffix=".mid")
        os.close(fd)
    pm.write(path)
    return path


def save_wav_file(
    audio: np.ndarray,
    sample_rate: int = 22050,
    path: Optional[str] = None,
) -> str:
    """Write a numpy audio array to a .wav file and return the path."""
    from scipy.io import wavfile

    if path is None:
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

    # Convert float [-1, 1] to int16
    audio_int16 = np.int16(audio * 32767)
    wavfile.write(path, sample_rate, audio_int16)
    return path


def generate_outputs(
    events: List[Tuple[float, int, float]],
    sample_rate: int = 22050,
) -> Tuple[str, str, np.ndarray]:
    """Generate both MIDI and WAV files from note events.

    Returns (midi_path, wav_path, audio_array).
    """
    pm = events_to_midi(events)
    midi_path = save_midi_file(pm)
    audio = midi_to_wav(pm, sample_rate=sample_rate)
    wav_path = save_wav_file(audio, sample_rate=sample_rate)
    return midi_path, wav_path, audio
