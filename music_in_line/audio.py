"""Audio generation: MIDI file creation, WAV synthesis, piano-roll visualisation."""

import tempfile
import os

import numpy as np
import pretty_midi
from scipy.io import wavfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def create_midi(midi_notes, bpm=120):
    """Create a PrettyMIDI object from a list of note dicts.

    Args:
        midi_notes: list of ``{'pitch', 'start', 'end', …}`` dicts.
        bpm: tempo in BPM.

    Returns:
        ``PrettyMIDI`` object.
    """
    midi_obj = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    instrument = pretty_midi.Instrument(program=0)  # Acoustic Grand Piano

    for note_info in midi_notes:
        note = pretty_midi.Note(
            velocity=100,
            pitch=note_info["pitch"],
            start=note_info["start"],
            end=note_info["end"],
        )
        instrument.notes.append(note)

    midi_obj.instruments.append(instrument)
    return midi_obj


def save_midi(midi_obj, path=None):
    """Write a PrettyMIDI object to disk and return the file path."""
    if path is None:
        fd, path = tempfile.mkstemp(suffix=".mid")
        os.close(fd)
    midi_obj.write(path)
    return path


def midi_to_wav(midi_notes, sample_rate=22050):
    """Synthesise a WAV file from note dicts using sine-wave + ADSR envelope.

    Returns:
        Path to the generated ``.wav`` file, or *None* if *midi_notes* is empty.
    """
    if not midi_notes:
        return None

    total_time = max(n["end"] for n in midi_notes) + 0.5
    num_samples = int(total_time * sample_rate)
    audio = np.zeros(num_samples)

    for note_info in midi_notes:
        freq = 440.0 * (2.0 ** ((note_info["pitch"] - 69) / 12.0))
        start_sample = int(note_info["start"] * sample_rate)
        end_sample = int(note_info["end"] * sample_rate)
        n_samples = end_sample - start_sample
        if n_samples <= 0:
            continue
        t = np.arange(n_samples) / sample_rate

        wave = np.sin(2 * np.pi * freq * t)

        # Simple ADSR envelope
        envelope = np.ones_like(t)
        attack = min(int(0.01 * sample_rate), len(t))
        release = min(int(0.05 * sample_rate), len(t))
        if attack > 0:
            envelope[:attack] = np.linspace(0, 1, attack)
        if release > 0:
            envelope[-release:] = np.linspace(1, 0, release)
        wave *= envelope

        end_idx = min(end_sample, num_samples)
        audio[start_sample:end_idx] += wave[: end_idx - start_sample]

    # Normalise
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.8

    fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    wavfile.write(wav_path, sample_rate, (audio * 32767).astype(np.int16))
    return wav_path


def plot_piano_roll(midi_notes):
    """Return a matplotlib *Figure* showing a piano-roll visualisation."""
    fig, ax = plt.subplots(figsize=(10, 4))

    for note in midi_notes:
        rect = patches.Rectangle(
            (note["start"], note["pitch"]),
            note["end"] - note["start"],
            0.8,
            linewidth=1,
            edgecolor="black",
            facecolor="steelblue",
            alpha=0.7,
        )
        ax.add_patch(rect)
        ax.text(
            note["start"] + 0.02,
            note["pitch"] + 0.3,
            note["note_name"],
            fontsize=7,
            color="white",
        )

    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("MIDI Pitch")
    ax.set_title("Generated Piano Roll")

    if midi_notes:
        all_ends = [n["end"] for n in midi_notes]
        all_pitches = [n["pitch"] for n in midi_notes]
        ax.set_xlim(-0.1, max(all_ends) + 0.5)
        ax.set_ylim(min(all_pitches) - 2, max(all_pitches) + 2)

    plt.tight_layout()
    return fig
