"""Unit tests for music_in_line.core module."""

import pytest
import numpy as np

from music_in_line.core import (
    C_MAJOR_NOTES,
    MIDI_HIGH,
    MIDI_LOW,
    SIXTEENTH_NOTE_DURATION,
    normalize_coordinates,
    pitch_ratio_to_midi,
    process_line,
    process_line_rule_based,
    smooth_melody,
    snap_to_c_major,
    time_ratio_to_seconds,
    validate_coordinates,
)


class TestValidateCoordinates:
    def test_none_input(self):
        valid, msg = validate_coordinates(None)
        assert not valid
        assert "Drawing Error" in msg

    def test_empty_list(self):
        valid, msg = validate_coordinates([])
        assert not valid
        assert "Drawing Error" in msg

    def test_single_point(self):
        valid, msg = validate_coordinates([(0, 0)])
        assert not valid
        assert "at least two points" in msg

    def test_two_points(self):
        valid, msg = validate_coordinates([(0, 0), (100, 100)])
        assert valid
        assert msg == ""

    def test_many_points(self):
        valid, msg = validate_coordinates([(i, i) for i in range(100)])
        assert valid


class TestNormalizeCoordinates:
    def test_origin(self):
        result = normalize_coordinates([(0, 256)], canvas_width=512, canvas_height=256)
        t, p = result[0]
        assert t == pytest.approx(0.0)
        assert p == pytest.approx(0.0)  # bottom of canvas = low pitch

    def test_top_right(self):
        result = normalize_coordinates([(512, 0)], canvas_width=512, canvas_height=256)
        t, p = result[0]
        assert t == pytest.approx(1.0)
        assert p == pytest.approx(1.0)  # top of canvas = high pitch

    def test_center(self):
        result = normalize_coordinates([(256, 128)], canvas_width=512, canvas_height=256)
        t, p = result[0]
        assert t == pytest.approx(0.5)
        assert p == pytest.approx(0.5)

    def test_clipping(self):
        result = normalize_coordinates([(-10, -10)], canvas_width=512, canvas_height=256)
        t, p = result[0]
        assert t == pytest.approx(0.0)
        assert p == pytest.approx(1.0)


class TestPitchMapping:
    def test_low_boundary(self):
        assert pitch_ratio_to_midi(0.0) == MIDI_LOW

    def test_high_boundary(self):
        assert pitch_ratio_to_midi(1.0) == MIDI_HIGH

    def test_mid(self):
        mid = pitch_ratio_to_midi(0.5)
        assert MIDI_LOW <= mid <= MIDI_HIGH


class TestSnapToCMajor:
    def test_c3_stays(self):
        assert snap_to_c_major(48) == 48  # C3

    def test_c_sharp_snaps_to_c_or_d(self):
        result = snap_to_c_major(49)  # C#3
        assert result in (48, 50)  # C3 or D3

    def test_all_notes_in_scale(self):
        for note in range(MIDI_LOW, MIDI_HIGH + 1):
            snapped = snap_to_c_major(note)
            assert snapped in C_MAJOR_NOTES

    def test_boundary_notes(self):
        assert snap_to_c_major(MIDI_LOW) in C_MAJOR_NOTES
        assert snap_to_c_major(MIDI_HIGH) in C_MAJOR_NOTES


class TestTimeMapping:
    def test_zero(self):
        assert time_ratio_to_seconds(0.0) == pytest.approx(0.0)

    def test_one(self):
        expected = 32 * SIXTEENTH_NOTE_DURATION
        assert time_ratio_to_seconds(1.0) == pytest.approx(expected)

    def test_half(self):
        expected = 16 * SIXTEENTH_NOTE_DURATION
        assert time_ratio_to_seconds(0.5) == pytest.approx(expected)


class TestProcessLineRuleBased:
    def test_two_points_horizontal(self):
        coords = [(0, 128), (512, 128)]
        events = process_line_rule_based(coords, canvas_width=512, canvas_height=256)
        assert len(events) == 2
        # Same pitch for a horizontal line at mid-height
        assert events[0][1] == events[1][1]

    def test_ascending_line(self):
        coords = [(0, 256), (256, 128), (512, 0)]
        events = process_line_rule_based(coords, canvas_width=512, canvas_height=256)
        assert len(events) == 3
        # Pitches should be ascending (y=256 bottom=low, y=0 top=high)
        assert events[0][1] <= events[1][1] <= events[2][1]

    def test_events_have_positive_duration(self):
        coords = [(0, 0), (100, 100), (200, 200)]
        events = process_line_rule_based(coords, canvas_width=512, canvas_height=256)
        for start, pitch, dur in events:
            assert dur > 0

    def test_events_sorted_by_time(self):
        coords = [(300, 50), (100, 200), (500, 100)]
        events = process_line_rule_based(coords, canvas_width=512, canvas_height=256)
        times = [e[0] for e in events]
        assert times == sorted(times)


class TestSmoothMelody:
    def test_no_smoothing_small_intervals(self):
        events = [(0.0, 60, 0.5), (0.5, 62, 0.5)]
        smoothed = smooth_melody(events)
        assert len(smoothed) == 2

    def test_smoothing_large_interval(self):
        events = [(0.0, 48, 1.0), (1.0, 60, 0.5)]
        smoothed = smooth_melody(events)
        assert len(smoothed) > 2  # passing tone inserted

    def test_passing_tone_in_scale(self):
        events = [(0.0, 48, 1.0), (1.0, 60, 0.5)]
        smoothed = smooth_melody(events)
        for _, pitch, _ in smoothed:
            assert pitch in C_MAJOR_NOTES

    def test_single_event(self):
        events = [(0.0, 60, 0.5)]
        smoothed = smooth_melody(events)
        assert len(smoothed) == 1


class TestProcessLine:
    def test_invalid_input_returns_error(self):
        success, msg, events = process_line([])
        assert not success
        assert "Drawing Error" in msg
        assert events == []

    def test_rule_based_mode(self):
        coords = [(0, 200), (256, 128), (512, 50)]
        success, summary, events = process_line(coords, mode="Rule-based")
        assert success
        assert len(events) == 3
        assert "Note:" in summary

    def test_ai_assisted_mode(self):
        coords = [(0, 256), (512, 0)]  # large pitch jump
        success, summary, events = process_line(coords, mode="AI-Assisted")
        assert success
        assert len(events) >= 2
        assert "Note:" in summary

    def test_summary_contains_note_names(self):
        coords = [(0, 128), (512, 128)]
        success, summary, events = process_line(coords, mode="Rule-based")
        assert success
        # Summary should contain standard note names
        assert any(n in summary for n in ["C", "D", "E", "F", "G", "A", "B"])
