"""Gradio web application for the Music In Line prototype."""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from music_in_line.audio import generate_outputs
from music_in_line.core import process_line, CANVAS_WIDTH, CANVAS_HEIGHT


def extract_coordinates_from_image(
    image: np.ndarray,
) -> List[Tuple[float, float]]:
    """Extract a polyline of (x, y) coordinates from a sketchpad image.

    Strategy:
      1. Convert to grayscale if needed.
      2. Find non-white pixels (drawn strokes).
      3. Group by x-column and take the mean y per column.
      4. Sort by x to produce a left-to-right polyline.

    If multiple separate strokes exist, they are joined into one
    continuous sequence sorted by x-coordinate.
    """
    if image is None:
        return []

    # Handle RGBA or RGB images -> grayscale
    if image.ndim == 3:
        if image.shape[2] == 4:
            # Use alpha channel: drawn areas typically have high alpha
            alpha = image[:, :, 3]
            gray = 255 - alpha  # high alpha -> low gray value (drawn)
        else:
            gray = np.mean(image[:, :, :3], axis=2)
    else:
        gray = image.astype(float)

    # Threshold: drawn pixels are darker than background
    threshold = 200
    drawn_mask = gray < threshold

    ys, xs = np.where(drawn_mask)
    if len(xs) == 0:
        return []

    # Group by x-column, take mean y per column
    unique_xs = np.unique(xs)
    coords: List[Tuple[float, float]] = []
    for ux in unique_xs:
        mean_y = float(np.mean(ys[xs == ux]))
        coords.append((float(ux), mean_y))

    # Sort by x
    coords.sort(key=lambda c: c[0])

    # Subsample to keep a reasonable number of points (e.g., ~64)
    if len(coords) > 64:
        indices = np.linspace(0, len(coords) - 1, 64, dtype=int)
        coords = [coords[i] for i in indices]

    return coords


def generate_music(
    sketchpad_data: Optional[dict],
    mode: str,
) -> Tuple[Optional[Tuple[int, np.ndarray]], Optional[str], str]:
    """Main callback for the Gradio interface.

    Returns ((sample_rate, audio_array), midi_path, summary_text).
    """
    # Extract the composite image from the sketchpad data
    if sketchpad_data is None:
        return None, None, "Drawing Error: Please draw a line with at least two points."

    # Gradio Sketchpad returns a dict with "composite" key or just an ndarray
    if isinstance(sketchpad_data, dict):
        image = sketchpad_data.get("composite")
        if image is None:
            # Try layers
            layers = sketchpad_data.get("layers", [])
            if layers:
                image = layers[0]
    elif isinstance(sketchpad_data, np.ndarray):
        image = sketchpad_data
    else:
        return None, None, "Drawing Error: Unexpected input format."

    if image is None:
        return None, None, "Drawing Error: Please draw a line with at least two points."

    # Get canvas dimensions from the image
    h, w = image.shape[:2]

    # Extract coordinates
    coords = extract_coordinates_from_image(image)

    # Process through the core pipeline
    success, summary, events = process_line(
        coords,
        mode=mode,
        canvas_width=w,
        canvas_height=h,
    )

    if not success:
        return None, None, summary

    # Generate MIDI and audio
    midi_path, _wav_path, audio = generate_outputs(events)

    audio_tuple = (22050, (audio * 32767).astype(np.int16))
    return audio_tuple, midi_path, summary


def build_interface():
    """Build and return the Gradio Blocks interface."""
    import gradio as gr

    with gr.Blocks(title="Visual Composition Prototype") as demo:
        gr.Markdown("# 🎵 Visual Composition Prototype")
        gr.Markdown(
            "Draw a line on the canvas below. The **vertical position** "
            "controls pitch (higher = higher note) and the **horizontal "
            "position** controls timing (left to right)."
        )

        with gr.Row():
            with gr.Column(scale=2):
                sketchpad = gr.Sketchpad(
                    label="Drawing Canvas",
                    canvas_size=(CANVAS_WIDTH, CANVAS_HEIGHT),
                    type="numpy",
                )
            with gr.Column(scale=1):
                mode = gr.Radio(
                    choices=["Rule-based", "AI-Assisted"],
                    value="Rule-based",
                    label="Composition Mode",
                )
                generate_btn = gr.Button("🎶 Generate Music", variant="primary")

        with gr.Row():
            audio_output = gr.Audio(label="Audio Preview", type="numpy")
            midi_download = gr.File(label="Download MIDI")

        summary_output = gr.Textbox(
            label="Generated Notes",
            lines=10,
            interactive=False,
        )

        generate_btn.click(
            fn=generate_music,
            inputs=[sketchpad, mode],
            outputs=[audio_output, midi_download, summary_output],
        )

    return demo


if __name__ == "__main__":
    demo = build_interface()
    demo.launch()
