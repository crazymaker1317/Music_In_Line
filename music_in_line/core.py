"""Core music processing: coordinate extraction, pitch mapping, and scale snapping."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np

# Canvas dimensions (pixels)
CANVAS_WIDTH = 512
CANVAS_HEIGHT = 256

# MIDI pitch range: C3 (48) to C5 (72)
MIDI_LOW = 48
MIDI_HIGH = 72

# C Major scale semitone offsets within an octave (C, D, E, F, G, A, B)
C_MAJOR_OFFSETS = [0, 2, 4, 5, 7, 9, 11]

# Build the full set of C-Major MIDI notes in [MIDI_LOW, MIDI_HIGH]
C_MAJOR_NOTES: List[int] = []
for _octave_start in range(0, 128, 12):
    for _offset in C_MAJOR_OFFSETS:
        _note = _octave_start + _offset
        if MIDI_LOW <= _note <= MIDI_HIGH:
            C_MAJOR_NOTES.append(_note)
# Ensure the boundary notes are included even if not in the scale
if MIDI_LOW not in C_MAJOR_NOTES:
    C_MAJOR_NOTES.insert(0, MIDI_LOW)
if MIDI_HIGH not in C_MAJOR_NOTES:
    C_MAJOR_NOTES.append(MIDI_HIGH)
C_MAJOR_NOTES = sorted(set(C_MAJOR_NOTES))

# Timing: map x-axis to 16th-note grid at 120 BPM
BPM = 120
SIXTEENTH_NOTE_DURATION = 60.0 / BPM / 4  # seconds per 16th note


def validate_coordinates(
    coordinates: List[Tuple[float, float]],
) -> Tuple[bool, str]:
    """Validate that the coordinate list has at least two points.

    Returns (is_valid, error_message).
    """
    if coordinates is None or len(coordinates) < 2:
        return False, "Drawing Error: Please draw a line with at least two points."
    return True, ""


def normalize_coordinates(
    coordinates: List[Tuple[float, float]],
    canvas_width: int = CANVAS_WIDTH,
    canvas_height: int = CANVAS_HEIGHT,
) -> List[Tuple[float, float]]:
    """Normalize raw pixel coordinates to (time_ratio, pitch_ratio) in [0, 1].

    * x -> time_ratio (0 = left edge, 1 = right edge)
    * y -> pitch_ratio (0 = bottom / low pitch, 1 = top / high pitch)

    Note: In most canvas systems y=0 is the *top*, so we invert the y-axis
    so that drawing higher visually produces a higher pitch.
    """
    normalized: List[Tuple[float, float]] = []
    for x, y in coordinates:
        time_ratio = np.clip(x / max(canvas_width, 1), 0.0, 1.0)
        # Invert y so that top-of-canvas = high pitch
        pitch_ratio = np.clip(1.0 - y / max(canvas_height, 1), 0.0, 1.0)
        normalized.append((float(time_ratio), float(pitch_ratio)))
    return normalized


def pitch_ratio_to_midi(pitch_ratio: float) -> int:
    """Map a pitch ratio in [0, 1] to a raw MIDI note in [MIDI_LOW, MIDI_HIGH]."""
    return int(round(MIDI_LOW + pitch_ratio * (MIDI_HIGH - MIDI_LOW)))


def snap_to_c_major(midi_note: int) -> int:
    """Snap a MIDI note to the nearest note in the C Major scale."""
    idx = int(np.argmin([abs(midi_note - n) for n in C_MAJOR_NOTES]))
    return C_MAJOR_NOTES[idx]


def time_ratio_to_seconds(
    time_ratio: float, total_sixteenths: int = 32
) -> float:
    """Map a time ratio in [0, 1] to seconds on a 16th-note grid."""
    grid_position = round(time_ratio * total_sixteenths)
    return grid_position * SIXTEENTH_NOTE_DURATION


def process_line_rule_based(
    coordinates: List[Tuple[float, float]],
    canvas_width: int = CANVAS_WIDTH,
    canvas_height: int = CANVAS_HEIGHT,
    total_sixteenths: int = 32,
) -> List[Tuple[float, int, float]]:
    """Convert raw coordinates to a list of (start_time, midi_note, duration).

    Rule-based mode:
      - y → MIDI pitch snapped to C Major
      - x → time on 16th-note grid
    """
    normalized = normalize_coordinates(coordinates, canvas_width, canvas_height)

    events: List[Tuple[float, int, float]] = []
    for i, (t_ratio, p_ratio) in enumerate(normalized):
        raw_pitch = pitch_ratio_to_midi(p_ratio)
        snapped_pitch = snap_to_c_major(raw_pitch)
        start = time_ratio_to_seconds(t_ratio, total_sixteenths)
        events.append((start, snapped_pitch, 0.0))  # duration filled below

    # Sort by start time
    events.sort(key=lambda e: e[0])

    # Compute durations: each note lasts until the next note starts
    result: List[Tuple[float, int, float]] = []
    for i, (start, pitch, _) in enumerate(events):
        if i < len(events) - 1:
            duration = max(events[i + 1][0] - start, SIXTEENTH_NOTE_DURATION)
        else:
            duration = SIXTEENTH_NOTE_DURATION  # last note gets one 16th
        result.append((start, pitch, duration))

    return result


def smooth_melody(
    events: List[Tuple[float, int, float]],
) -> List[Tuple[float, int, float]]:
    """AI-assisted heuristic: smooth the melody by adding passing tones.

    This is a lightweight heuristic that:
      1. Detects large pitch jumps (> 4 semitones).
      2. Inserts an intermediate passing tone halfway through the duration.
    The passing tone is snapped to C Major.
    """
    if len(events) < 2:
        return list(events)

    smoothed: List[Tuple[float, int, float]] = []
    for i in range(len(events) - 1):
        start, pitch, duration = events[i]
        next_pitch = events[i + 1][1]
        interval = abs(next_pitch - pitch)

        if interval > 4:
            # Split duration in half
            half_dur = duration / 2.0
            smoothed.append((start, pitch, half_dur))
            # Insert passing tone
            mid_pitch = (pitch + next_pitch) // 2
            mid_pitch = snap_to_c_major(mid_pitch)
            smoothed.append((start + half_dur, mid_pitch, half_dur))
        else:
            smoothed.append((start, pitch, duration))

    # Append the last note unchanged
    smoothed.append(events[-1])
    return smoothed


def process_line(
    coordinates: List[Tuple[float, float]],
    mode: str = "Rule-based",
    canvas_width: int = CANVAS_WIDTH,
    canvas_height: int = CANVAS_HEIGHT,
) -> Tuple[bool, str, List[Tuple[float, int, float]]]:
    """High-level entry point: validate, map, and optionally smooth.

    Returns (success, message, events) where events is a list of
    (start_time_sec, midi_note, duration_sec).
    """
    is_valid, err = validate_coordinates(coordinates)
    if not is_valid:
        return False, err, []

    events = process_line_rule_based(
        coordinates,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
    )

    if mode == "AI-Assisted":
        events = smooth_melody(events)

    # Build human-readable summary
    note_names = [
        "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
    ]
    lines = []
    for start, pitch, dur in events:
        name = note_names[pitch % 12] + str(pitch // 12 - 1)
        lines.append(f"Note: {name}, Start: {start:.2f}s, Duration: {dur:.2f}s")
    summary = "\n".join(lines)

    return True, summary, events
