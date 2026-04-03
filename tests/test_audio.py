"""Tests for music_in_line.audio."""

import os

import numpy as np
import pytest

from music_in_line.audio import create_midi, save_midi, midi_to_wav, plot_piano_roll


SAMPLE_NOTES = [
    {"pitch": 60, "start": 0.0, "end": 0.5, "note_name": "C4"},
    {"pitch": 64, "start": 0.5, "end": 1.0, "note_name": "E4"},
    {"pitch": 67, "start": 1.0, "end": 1.5, "note_name": "G4"},
]


# ── create_midi / save_midi ───────────────────────────────────────────────


class TestCreateMidi:
    def test_returns_pretty_midi(self):
        import pretty_midi
        midi_obj = create_midi(SAMPLE_NOTES)
        assert isinstance(midi_obj, pretty_midi.PrettyMIDI)

    def test_instrument_count(self):
        midi_obj = create_midi(SAMPLE_NOTES)
        assert len(midi_obj.instruments) == 1

    def test_note_count(self):
        midi_obj = create_midi(SAMPLE_NOTES)
        assert len(midi_obj.instruments[0].notes) == 3

    def test_save_midi_creates_file(self, tmp_path):
        midi_obj = create_midi(SAMPLE_NOTES)
        path = str(tmp_path / "test.mid")
        result = save_midi(midi_obj, path)
        assert os.path.isfile(result)
        assert result == path

    def test_save_midi_auto_path(self):
        midi_obj = create_midi(SAMPLE_NOTES)
        path = save_midi(midi_obj)
        try:
            assert os.path.isfile(path)
        finally:
            os.unlink(path)


# ── midi_to_wav ───────────────────────────────────────────────────────────


class TestMidiToWav:
    def test_empty_returns_none(self):
        assert midi_to_wav([]) is None

    def test_creates_wav_file(self):
        path = midi_to_wav(SAMPLE_NOTES)
        try:
            assert path is not None
            assert os.path.isfile(path)
            assert path.endswith(".wav")
        finally:
            if path:
                os.unlink(path)

    def test_wav_is_readable(self):
        from scipy.io import wavfile
        path = midi_to_wav(SAMPLE_NOTES)
        try:
            sr, data = wavfile.read(path)
            assert sr == 22050
            assert len(data) > 0
        finally:
            if path:
                os.unlink(path)

    def test_audio_not_silent(self):
        from scipy.io import wavfile
        path = midi_to_wav(SAMPLE_NOTES)
        try:
            _, data = wavfile.read(path)
            assert np.max(np.abs(data)) > 0
        finally:
            if path:
                os.unlink(path)


# ── plot_piano_roll ───────────────────────────────────────────────────────


class TestPlotPianoRoll:
    def test_returns_figure(self):
        import matplotlib.figure
        fig = plot_piano_roll(SAMPLE_NOTES)
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_empty_notes(self):
        fig = plot_piano_roll([])
        assert fig is not None
