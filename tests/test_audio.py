"""Unit tests for music_in_line.audio module."""

import os
import tempfile

import numpy as np
import pytest

from music_in_line.audio import (
    events_to_midi,
    generate_outputs,
    midi_to_wav,
    save_midi_file,
    save_wav_file,
)


SAMPLE_EVENTS = [
    (0.0, 60, 0.5),
    (0.5, 64, 0.5),
    (1.0, 67, 0.5),
]


class TestEventsToMidi:
    def test_returns_pretty_midi(self):
        pm = events_to_midi(SAMPLE_EVENTS)
        assert pm is not None
        assert len(pm.instruments) == 1

    def test_correct_note_count(self):
        pm = events_to_midi(SAMPLE_EVENTS)
        assert len(pm.instruments[0].notes) == 3

    def test_note_pitches(self):
        pm = events_to_midi(SAMPLE_EVENTS)
        pitches = [n.pitch for n in pm.instruments[0].notes]
        assert pitches == [60, 64, 67]

    def test_note_timing(self):
        pm = events_to_midi(SAMPLE_EVENTS)
        starts = [n.start for n in pm.instruments[0].notes]
        assert starts == pytest.approx([0.0, 0.5, 1.0])


class TestMidiToWav:
    def test_returns_numpy_array(self):
        pm = events_to_midi(SAMPLE_EVENTS)
        audio = midi_to_wav(pm)
        assert isinstance(audio, np.ndarray)
        assert len(audio) > 0

    def test_normalized_range(self):
        pm = events_to_midi(SAMPLE_EVENTS)
        audio = midi_to_wav(pm)
        assert np.max(np.abs(audio)) <= 1.0


class TestSaveMidiFile:
    def test_creates_file(self):
        pm = events_to_midi(SAMPLE_EVENTS)
        path = save_midi_file(pm)
        try:
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)

    def test_custom_path(self):
        pm = events_to_midi(SAMPLE_EVENTS)
        fd, custom_path = tempfile.mkstemp(suffix=".mid")
        os.close(fd)
        try:
            result = save_midi_file(pm, path=custom_path)
            assert result == custom_path
            assert os.path.exists(custom_path)
        finally:
            os.unlink(custom_path)


class TestSaveWavFile:
    def test_creates_file(self):
        audio = np.random.uniform(-1, 1, 22050).astype(np.float64)
        path = save_wav_file(audio)
        try:
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)


class TestGenerateOutputs:
    def test_returns_paths_and_audio(self):
        midi_path, wav_path, audio = generate_outputs(SAMPLE_EVENTS)
        try:
            assert os.path.exists(midi_path)
            assert os.path.exists(wav_path)
            assert isinstance(audio, np.ndarray)
            assert len(audio) > 0
        finally:
            os.unlink(midi_path)
            os.unlink(wav_path)
