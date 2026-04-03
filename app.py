"""🎵 Visual Composition Prototype — draw a line, hear a melody."""

import gradio as gr

from music_in_line.core import (
    extract_coordinates_from_image,
    detect_musical_peaks,
    map_to_midi,
    smooth_melody,
)
from music_in_line.audio import (
    create_midi,
    save_midi,
    midi_to_wav,
    plot_piano_roll,
)


def generate_music(image_dict, mode):
    """Main pipeline: Sketchpad image → piano roll + audio + MIDI file."""
    # --- Phase 1: coordinate extraction ---
    if image_dict is None:
        return None, None, None, "⚠️ 그림을 그려주세요."

    coords = extract_coordinates_from_image(image_dict)

    if coords is None or len(coords) < 2:
        return (
            None,
            None,
            None,
            "⚠️ 그림을 다시 그려주세요. 최소 2개 이상의 점이 필요합니다.",
        )

    warning = ""
    if len(coords) < 5:
        warning = "⚠️ 선이 너무 짧습니다. 좀 더 길게 그려주세요.\n"

    # --- Phase 2: music conversion ---
    notes_data = detect_musical_peaks(coords)
    midi_notes = map_to_midi(notes_data)

    if mode == "스무딩 적용":
        midi_notes = smooth_melody(midi_notes)

    # --- Phase 3: output ---
    midi_obj = create_midi(midi_notes)
    midi_path = save_midi(midi_obj)
    wav_path = midi_to_wav(midi_notes)
    fig = plot_piano_roll(midi_notes)

    status = warning + f"✅ {len(midi_notes)}개의 음표가 생성되었습니다."
    return fig, wav_path, midi_path, status


# ── Gradio UI ──────────────────────────────────────────────────────────────

def build_app():
    """Construct and return the Gradio Blocks application."""
    with gr.Blocks(title="Visual Composition Prototype") as demo:
        gr.Markdown("# 🎵 Visual Composition Prototype")

        with gr.Row():
            with gr.Column(scale=3):
                sketchpad = gr.Sketchpad(
                    canvas_size=(512, 256),
                    type="numpy",
                    image_mode="L",
                    brush=gr.Brush(
                        default_size=3,
                        colors=["#000000"],
                        color_mode="fixed",
                    ),
                    label="Draw a line here",
                )

            with gr.Column(scale=1):
                mode = gr.Radio(
                    choices=["기본 모드", "스무딩 적용"],
                    value="기본 모드",
                    label="Mode",
                )
                btn = gr.Button("🎵 Generate Music", variant="primary")
                status = gr.Textbox(label="Status", interactive=False)

        piano_roll = gr.Plot(label="Piano Roll")

        with gr.Row():
            audio_out = gr.Audio(label="Audio Player", type="filepath")
            midi_file = gr.File(label="MIDI Download")

        btn.click(
            fn=generate_music,
            inputs=[sketchpad, mode],
            outputs=[piano_roll, audio_out, midi_file, status],
        )

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch()
