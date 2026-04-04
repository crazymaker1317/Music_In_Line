"""
app.py — Music In Line Gradio 웹 애플리케이션 메인 진입점

사용자가 캔버스에 선을 그리면, 해당 선을 분석하여
선택한 박자에 맞는 음악(MIDI)을 생성합니다.
"""

import os
import tempfile
import numpy as np
import gradio as gr

from core.line_simplifier import simplify_line, enforce_left_to_right
from core.pitch_mapper import map_y_to_pitch
from core.note_arranger import arrange_notes, notes_to_text
from core.midi_generator import generate_midi
from utils.visualization import plot_line_comparison, plot_piano_roll
from utils.audio_synth import synthesize_wav


# ── 상수 ──────────────────────────────────────────────
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 400


# ── 헬퍼 함수 ────────────────────────────────────────
def _extract_points_from_sketchpad(sketch_data):
    """
    Gradio Sketchpad 데이터에서 좌표 리스트를 추출합니다.

    Sketchpad는 dict를 반환합니다:
    - 'background': 배경 이미지
    - 'layers': 그림 레이어 리스트 (각 레이어는 투명 배경 위 그림)
    - 'composite': 합성된 최종 이미지

    레이어 데이터에서 그려진 선의 좌표를 추출합니다.
    """
    if sketch_data is None:
        return []

    img = None

    if isinstance(sketch_data, dict):
        # 레이어에서 그려진 부분 추출 (투명 배경 위 그림)
        if "layers" in sketch_data and sketch_data["layers"]:
            layers = sketch_data["layers"]
            # 모든 레이어를 합산하여 그려진 부분 감지
            for layer in layers:
                if isinstance(layer, np.ndarray) and layer.size > 0:
                    img = layer
                    break
        # 레이어에서 찾지 못하면 composite 사용
        if img is None and "composite" in sketch_data:
            composite = sketch_data["composite"]
            if isinstance(composite, np.ndarray):
                img = composite
    elif isinstance(sketch_data, np.ndarray):
        img = sketch_data

    if img is None or not isinstance(img, np.ndarray):
        return []

    return _extract_points_from_image(img)


def _extract_points_from_image(img):
    """
    이미지 배열에서 그려진 선의 좌표를 추출합니다.
    레이어 이미지(투명 배경)에서는 알파 채널로,
    합성 이미지에서는 어두운 픽셀(브러시가 검정색)로 감지합니다.
    """
    if img is None or img.size == 0:
        return []

    if len(img.shape) == 3:
        if img.shape[2] == 4:
            # RGBA: 알파 채널로 그려진 부분 감지 (레이어는 투명 배경)
            alpha_mask = img[:, :, 3] > 10
            # RGB 채널로 어두운 부분도 감지 (합성 이미지의 검정 브러시)
            dark_mask = np.all(img[:, :, :3] < 50, axis=2)
            # 둘 다 확인하여 결합
            # 알파가 있고 불투명한 부분 중 어두운 것, 또는 알파가 있는 레이어 부분
            # 전략: 배경이 투명(alpha==0)인 이미지면 alpha만 사용
            bg_transparent = np.mean(img[:, :, 3] == 0) > 0.5
            if bg_transparent:
                mask = alpha_mask
            else:
                # 합성 이미지: 어두운 픽셀 감지 (검정 브러시)
                mask = dark_mask & (img[:, :, 3] > 200)
        else:
            # RGB: 어두운 부분이 그려진 선 (검정 브러시)
            mask = np.all(img[:, :, :3] < 50, axis=2)
    elif len(img.shape) == 2:
        mask = img < 50  # 어두운 부분
    else:
        return []

    # 그려진 픽셀 좌표 추출
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return []

    # X좌표별로 그룹화하여 평균 Y 계산 (노이즈 감소)
    from collections import defaultdict
    x_groups = defaultdict(list)
    for x, y in zip(xs.tolist(), ys.tolist()):
        x_groups[x].append(y)

    points = []
    for x in sorted(x_groups.keys()):
        avg_y = sum(x_groups[x]) / len(x_groups[x])
        points.append((float(x), float(avg_y)))

    # 너무 많은 포인트면 샘플링
    if len(points) > 500:
        step = len(points) // 500
        points = points[::step]

    return points


def _parse_time_signature(ts_str):
    """박자 문자열을 (분자, 분모) 튜플로 변환"""
    mapping = {
        "4/4": (4, 4),
        "3/4": (3, 4),
        "2/4": (2, 4),
    }
    return mapping.get(ts_str, (4, 4))


# ── 메인 콜백 함수들 ─────────────────────────────────

def convert_line(sketch_data, epsilon):
    """
    선 변환하기 버튼 콜백:
    스케치패드에서 원본 좌표를 추출하고 RDP 알고리즘으로 단순화합니다.
    """
    # 좌표 추출
    raw_points = _extract_points_from_sketchpad(sketch_data)
    if not raw_points or len(raw_points) < 2:
        return (
            None,  # 시각화
            "⚠️ 선을 그려주세요! 왼쪽에서 오른쪽으로 선을 그린 후 변환 버튼을 누르세요.",
            []  # state
        )

    # 좌→우 방향 보정 (역방향 포인트 제거)
    points = enforce_left_to_right(raw_points)

    if len(points) < 2:
        return (
            None,
            "⚠️ 유효한 포인트가 부족합니다. 왼쪽에서 오른쪽 방향으로 다시 그려주세요.",
            []
        )

    # RDP 알고리즘으로 단순화
    simplified = simplify_line(points, epsilon)

    # 시각화
    fig = plot_line_comparison(
        points, simplified,
        canvas_width=CANVAS_WIDTH,
        canvas_height=CANVAS_HEIGHT
    )

    status = f"✅ 원본 포인트: {len(points)}개 → 단순화: {len(simplified)}개"

    return fig, status, simplified


def generate_music(simplified_state, time_sig_str, num_measures, bpm):
    """
    음악 생성하기 버튼 콜백:
    저장된 단순화 데이터에서 음표를 배열하고 MIDI/WAV 파일을 생성합니다.
    """
    simplified = simplified_state
    if not simplified or len(simplified) < 2:
        return None, "먼저 선을 그리고 '선 변환하기' 버튼을 눌러주세요.", None, None, None

    time_signature = _parse_time_signature(time_sig_str)

    # 캔버스 크기 결정 (단순화된 데이터의 실제 범위 사용)
    xs = [p[0] for p in simplified]
    ys = [p[1] for p in simplified]
    canvas_w = max(xs) - min(xs) if max(xs) > min(xs) else CANVAS_WIDTH
    canvas_h = CANVAS_HEIGHT  # 항상 고정 캔버스 높이 사용

    # X좌표를 0 기준으로 보정
    min_x = min(xs)
    adjusted_points = [(x - min_x, y) for x, y in simplified]

    # 음표 배열
    notes = arrange_notes(
        adjusted_points,
        canvas_width=canvas_w,
        canvas_height=canvas_h,
        time_signature=time_signature,
        num_measures=int(num_measures)
    )

    if not notes:
        return None, "음표를 생성할 수 없습니다. 더 길거나 복잡한 선을 그려보세요.", None, None, None

    # 음표 텍스트 정보
    note_text = notes_to_text(notes)

    # 피아노 롤 시각화
    piano_roll_fig = plot_piano_roll(notes, time_signature, int(num_measures))

    # MIDI 파일 생성 (보안을 위해 mkstemp 사용)
    fd, midi_path = tempfile.mkstemp(suffix=".mid")
    os.close(fd)
    generate_midi(
        notes,
        bpm=int(bpm),
        time_signature=time_signature,
        output_path=midi_path
    )

    # WAV 파일 생성 (브라우저 재생용)
    fd2, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd2)
    synthesize_wav(
        notes,
        bpm=int(bpm),
        time_signature=time_signature,
        output_path=wav_path
    )

    return midi_path, note_text, piano_roll_fig, wav_path, midi_path


# ── Gradio UI 구성 ────────────────────────────────────

def create_app():
    """Gradio Blocks 앱을 생성합니다."""

    with gr.Blocks(
        title="Music In Line - 프로토타입",
    ) as app:

        gr.Markdown("# 🎼 Music In Line — 프로토타입")
        gr.Markdown("**내가 그린 선이 음악이 되는 마법!** 캔버스에 선을 그리면 음악(MIDI)으로 변환됩니다.")

        # 상태 저장 (단순화된 데이터)
        simplified_state = gr.State([])

        # ── Step 1: 선 그리기 ──
        gr.Markdown("## 🎨 Step 1: 선 그리기")
        gr.Markdown("왼쪽에서 오른쪽으로 자유롭게 선을 그려보세요! "
                     "가로축 = 시간(마디), 세로축 = 음높이(위: 높은 음, 아래: 낮은 음)\n\n"
                     "> 💡 **역방향(오른쪽→왼쪽) 포인트는 자동으로 제거**됩니다.")

        sketchpad = gr.Sketchpad(
            label="선 그리기 캔버스",
            canvas_size=(CANVAS_WIDTH, CANVAS_HEIGHT),
            height=CANVAS_HEIGHT + 100,
            width=CANVAS_WIDTH + 50,
            type="numpy",
            brush=gr.Brush(colors=["#000000"], color_mode="fixed",
                           default_size=5),
            layers=False,
        )

        # ── Step 2: 선 변환 ──
        with gr.Row():
            epsilon_slider = gr.Slider(
                minimum=1, maximum=30, value=5, step=1,
                label="단순화 정도 (epsilon)",
                info="클수록 더 단순화됩니다"
            )
            convert_btn = gr.Button("📐 선 변환하기", variant="primary")

        viz_output = gr.Plot(label="변환 결과 시각화")
        convert_status = gr.Textbox(label="변환 상태", interactive=False)

        # ── Step 3: 설정 ──
        gr.Markdown("## ⚙️ Step 2: 설정")
        with gr.Row():
            time_sig_dropdown = gr.Dropdown(
                choices=["4/4", "3/4", "2/4"],
                value="4/4",
                label="박자 선택"
            )
            num_measures_slider = gr.Slider(
                minimum=2, maximum=8, value=4, step=1,
                label="마디 수"
            )
            bpm_slider = gr.Slider(
                minimum=60, maximum=180, value=120, step=1,
                label="BPM (빠르기)"
            )

        # ── Step 4-5: 음악 생성 ──
        generate_btn = gr.Button("🎵 음악 생성하기", variant="primary", size="lg")

        gr.Markdown("## 🎼 결과")

        # 피아노 롤 시각화
        piano_roll_output = gr.Plot(label="🎵 음표 배치 (피아노 롤)")

        # 오디오 재생
        audio_output = gr.Audio(label="🔊 음악 미리 듣기", type="filepath")

        note_text_output = gr.Textbox(
            label="📝 음표 텍스트 정보",
            lines=10,
            interactive=False
        )
        midi_download = gr.File(label="💾 MIDI 파일 다운로드")

        # ── 이벤트 바인딩 ──

        # 선 변환 버튼
        convert_btn.click(
            fn=convert_line,
            inputs=[sketchpad, epsilon_slider],
            outputs=[viz_output, convert_status, simplified_state]
        )

        # 음악 생성 버튼
        generate_btn.click(
            fn=generate_music,
            inputs=[simplified_state, time_sig_dropdown,
                    num_measures_slider, bpm_slider],
            outputs=[midi_download, note_text_output, piano_roll_output,
                     audio_output, midi_download]
        )

    return app


# ── 메인 실행 ─────────────────────────────────────────

if __name__ == "__main__":
    app = create_app()
    app.launch()
