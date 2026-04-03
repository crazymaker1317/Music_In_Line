"""Core processing: coordinate extraction, peak detection, MIDI mapping, smoothing."""

import numpy as np
from scipy.signal import find_peaks


def extract_coordinates_from_image(image_dict):
    """Extract (x, y) coordinates of drawn pixels from a Sketchpad image.

    Args:
        image_dict: gr.Sketchpad output dict; ``image_dict['composite']``
                    is the actual image as a numpy array.

    Returns:
        np.ndarray of shape (N, 2) sorted by x, or *None* if nothing was drawn.
    """
    img = image_dict["composite"]

    # Convert to grayscale if needed
    if len(img.shape) == 3:
        img = np.mean(img[:, :, :3], axis=2)

    # Detect drawn pixels (dark on white background)
    threshold = 128
    ys, xs = np.where(img < threshold)

    if len(xs) == 0:
        return None

    # Group by x and take median y (compensates for brush width)
    coords = []
    for x_val in sorted(set(xs)):
        mask = xs == x_val
        y_median = np.median(ys[mask])
        coords.append([x_val, y_median])

    return np.array(coords)


def detect_musical_peaks(coords, min_distance=10):
    """Detect peaks and valleys in y-values to use as note positions.

    Args:
        coords: np.ndarray of shape (N, 2), [x, y] pairs sorted by x.
        min_distance: Minimum distance between peaks.

    Returns:
        List of dicts with keys ``x``, ``y``, ``index``.
    """
    y_vals = coords[:, 1]
    x_vals = coords[:, 0]

    peaks, _ = find_peaks(-y_vals, distance=min_distance)
    valleys, _ = find_peaks(y_vals, distance=min_distance)

    key_points = sorted(set([0] + list(peaks) + list(valleys) + [len(coords) - 1]))

    notes_data = []
    for idx in key_points:
        notes_data.append({
            "x": float(x_vals[idx]),
            "y": float(y_vals[idx]),
            "index": int(idx),
        })
    return notes_data


def map_to_midi(
    notes_data,
    canvas_height=256,
    canvas_width=512,
    midi_low=60,
    midi_high=84,
    total_duration=4.0,
):
    """Map detected note data to MIDI pitches and times.

    Mapping rules:
        - y → MIDI pitch (top=high, bottom=low), snapped to C-major.
        - x → time in seconds (0 … *total_duration*).

    Returns:
        List of dicts: ``{'pitch', 'start', 'end', 'note_name'}``.
    """
    # Build C-major pitch set within range
    c_major_offsets = [0, 2, 4, 5, 7, 9, 11]
    c_major_notes = sorted({
        octave_start + offset
        for octave_start in range(midi_low - 12, midi_high + 13, 12)
        for offset in c_major_offsets
        if midi_low <= octave_start + offset <= midi_high
    })

    def snap_to_scale(midi_pitch):
        return min(c_major_notes, key=lambda n: abs(n - midi_pitch))

    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    midi_notes = []
    for i, note in enumerate(notes_data):
        # y → pitch (canvas top is y=0 → high pitch)
        pitch_raw = midi_high - (note["y"] / canvas_height) * (midi_high - midi_low)
        pitch = snap_to_scale(int(round(pitch_raw)))

        # x → time
        start_time = (note["x"] / canvas_width) * total_duration

        # duration until next note (last note gets 0.5 s default)
        if i < len(notes_data) - 1:
            next_start = (notes_data[i + 1]["x"] / canvas_width) * total_duration
            duration = next_start - start_time
        else:
            duration = 0.5

        duration = max(duration, 0.1)

        octave = (pitch // 12) - 1
        note_name = f"{note_names[pitch % 12]}{octave}"

        midi_notes.append({
            "pitch": pitch,
            "start": round(start_time, 3),
            "end": round(start_time + duration, 3),
            "note_name": note_name,
        })

    return midi_notes


def smooth_melody(midi_notes, max_interval=7):
    """Rule-based post-processing to make the melody smoother.

    1. Insert a passing tone when the interval exceeds *max_interval* semitones.
    2. Extend notes shorter than 0.08 s to 0.1 s.

    Returns:
        New list of note dicts (same format as input).
    """
    if not midi_notes:
        return midi_notes

    note_names_list = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    def _make_note_name(pitch):
        octave = (pitch // 12) - 1
        return f"{note_names_list[pitch % 12]}{octave}"

    smoothed: list[dict] = []

    for i, note in enumerate(midi_notes):
        # Extend short notes
        duration = note["end"] - note["start"]
        end = note["end"] if duration >= 0.08 else round(note["start"] + 0.1, 3)
        current = {**note, "end": end, "note_name": note["note_name"]}

        if smoothed:
            prev = smoothed[-1]
            interval = abs(current["pitch"] - prev["pitch"])
            if interval > max_interval:
                mid_pitch = (prev["pitch"] + current["pitch"]) // 2
                mid_time = round((prev["end"] + current["start"]) / 2, 3)
                half_dur = round(max((current["start"] - prev["end"]) / 2, 0.05), 3)
                passing = {
                    "pitch": mid_pitch,
                    "start": round(mid_time - half_dur, 3),
                    "end": round(mid_time + half_dur, 3),
                    "note_name": _make_note_name(mid_pitch),
                }
                smoothed.append(passing)

        smoothed.append(current)

    return smoothed
