"""Tests for music_in_line.core."""

import numpy as np
import pytest

from music_in_line.core import (
    extract_coordinates_from_image,
    detect_musical_peaks,
    map_to_midi,
    smooth_melody,
)


# ── extract_coordinates_from_image ────────────────────────────────────────


class TestExtractCoordinates:
    """Tests for coordinate extraction from sketchpad images."""

    def _make_image_dict(self, img):
        return {"composite": img}

    def test_blank_image_returns_none(self):
        img = np.full((256, 512), 255, dtype=np.uint8)
        assert extract_coordinates_from_image(self._make_image_dict(img)) is None

    def test_single_pixel(self):
        img = np.full((256, 512), 255, dtype=np.uint8)
        img[100, 50] = 0
        coords = extract_coordinates_from_image(self._make_image_dict(img))
        assert coords is not None
        assert coords.shape == (1, 2)
        assert coords[0, 0] == 50
        assert coords[0, 1] == 100

    def test_horizontal_line(self):
        img = np.full((256, 512), 255, dtype=np.uint8)
        img[128, 10:100] = 0
        coords = extract_coordinates_from_image(self._make_image_dict(img))
        assert coords is not None
        assert len(coords) == 90
        np.testing.assert_array_equal(coords[:, 1], 128)

    def test_rgb_image_conversion(self):
        img = np.full((256, 512, 3), 255, dtype=np.uint8)
        img[50, 200, :] = 0
        coords = extract_coordinates_from_image(self._make_image_dict(img))
        assert coords is not None
        assert coords[0, 0] == 200
        assert coords[0, 1] == 50

    def test_rgba_image_conversion(self):
        img = np.full((256, 512, 4), 255, dtype=np.uint8)
        img[30, 100, :3] = 0
        coords = extract_coordinates_from_image(self._make_image_dict(img))
        assert coords is not None
        assert coords[0, 0] == 100

    def test_sorted_by_x(self):
        img = np.full((256, 512), 255, dtype=np.uint8)
        img[10, 300] = 0
        img[20, 100] = 0
        img[30, 200] = 0
        coords = extract_coordinates_from_image(self._make_image_dict(img))
        assert list(coords[:, 0]) == [100, 200, 300]

    def test_brush_width_median(self):
        """Multiple y-pixels at the same x should collapse to median."""
        img = np.full((256, 512), 255, dtype=np.uint8)
        img[48:53, 100] = 0  # rows 48,49,50,51,52 → median 50
        coords = extract_coordinates_from_image(self._make_image_dict(img))
        assert len(coords) == 1
        assert coords[0, 1] == 50.0


# ── detect_musical_peaks ──────────────────────────────────────────────────


class TestDetectMusicalPeaks:
    def test_includes_endpoints(self):
        coords = np.array([[i, 128] for i in range(100)])
        notes = detect_musical_peaks(coords)
        assert notes[0]["index"] == 0
        assert notes[-1]["index"] == 99

    def test_detects_peak(self):
        # V-shape: goes down then up → valley in the middle
        y = list(range(100, 50, -1)) + list(range(50, 101))
        coords = np.array([[i, y[i]] for i in range(len(y))])
        notes = detect_musical_peaks(coords, min_distance=5)
        indices = [n["index"] for n in notes]
        assert 50 in indices  # valley at index 50

    def test_min_distance(self):
        rng = np.random.default_rng(42)
        y = np.sin(np.linspace(0, 4 * np.pi, 200)) * 50 + 128
        y += rng.normal(0, 2, 200)
        coords = np.column_stack([np.arange(200), y])
        notes_tight = detect_musical_peaks(coords, min_distance=5)
        notes_loose = detect_musical_peaks(coords, min_distance=30)
        assert len(notes_tight) >= len(notes_loose)


# ── map_to_midi ───────────────────────────────────────────────────────────


class TestMapToMidi:
    def _simple_notes_data(self):
        return [
            {"x": 0, "y": 0, "index": 0},
            {"x": 256, "y": 128, "index": 1},
            {"x": 512, "y": 256, "index": 2},
        ]

    def test_output_structure(self):
        midi_notes = map_to_midi(self._simple_notes_data())
        assert len(midi_notes) == 3
        for n in midi_notes:
            assert "pitch" in n
            assert "start" in n
            assert "end" in n
            assert "note_name" in n

    def test_pitch_range(self):
        midi_notes = map_to_midi(self._simple_notes_data())
        for n in midi_notes:
            assert 60 <= n["pitch"] <= 84

    def test_c_major_snap(self):
        c_major = {0, 2, 4, 5, 7, 9, 11}
        midi_notes = map_to_midi(self._simple_notes_data())
        for n in midi_notes:
            assert n["pitch"] % 12 in c_major

    def test_time_ordering(self):
        midi_notes = map_to_midi(self._simple_notes_data())
        starts = [n["start"] for n in midi_notes]
        assert starts == sorted(starts)

    def test_min_duration(self):
        notes_data = [
            {"x": 0, "y": 128, "index": 0},
            {"x": 1, "y": 128, "index": 1},  # very close to previous
        ]
        midi_notes = map_to_midi(notes_data)
        for n in midi_notes:
            assert n["end"] - n["start"] >= 0.1

    def test_top_is_high_pitch(self):
        notes_data = [{"x": 0, "y": 0, "index": 0}]  # top of canvas
        midi_notes = map_to_midi(notes_data)
        assert midi_notes[0]["pitch"] == 84  # C6

    def test_bottom_is_low_pitch(self):
        notes_data = [{"x": 0, "y": 256, "index": 0}]  # bottom of canvas
        midi_notes = map_to_midi(notes_data)
        assert midi_notes[0]["pitch"] == 60  # C4


# ── smooth_melody ─────────────────────────────────────────────────────────


class TestSmoothMelody:
    def test_empty_input(self):
        assert smooth_melody([]) == []

    def test_no_change_small_intervals(self):
        notes = [
            {"pitch": 60, "start": 0.0, "end": 0.5, "note_name": "C4"},
            {"pitch": 62, "start": 0.5, "end": 1.0, "note_name": "D4"},
        ]
        result = smooth_melody(notes)
        assert len(result) == 2

    def test_passing_tone_inserted(self):
        notes = [
            {"pitch": 60, "start": 0.0, "end": 0.5, "note_name": "C4"},
            {"pitch": 72, "start": 1.0, "end": 1.5, "note_name": "C5"},
        ]
        result = smooth_melody(notes, max_interval=7)
        assert len(result) == 3  # original 2 + 1 passing tone
        assert result[1]["pitch"] == 66  # midpoint

    def test_short_note_extended(self):
        notes = [
            {"pitch": 60, "start": 0.0, "end": 0.05, "note_name": "C4"},
        ]
        result = smooth_melody(notes)
        assert result[0]["end"] - result[0]["start"] >= 0.1
