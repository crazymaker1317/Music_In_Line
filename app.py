"""
app.py — Music In Line Gradio 웹 애플리케이션 메인 진입점

사용자가 캔버스에 선을 그리면, 해당 선을 분석하여
선택한 박자에 맞는 음악(MIDI)을 생성합니다.
"""

import json
import tempfile
import numpy as np
import gradio as gr

from core.line_simplifier import simplify_line, enforce_left_to_right
from core.pitch_mapper import map_y_to_pitch
from core.note_arranger import arrange_notes, notes_to_text
from core.midi_generator import generate_midi
from utils.visualization import plot_line_comparison


# ── 상수 ──────────────────────────────────────────────
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 400


# ── 헬퍼 함수 ────────────────────────────────────────
def _extract_points_from_sketchpad(sketch_data):
    """
    Gradio Sketchpad 데이터에서 좌표 리스트를 추출합니다.

    Sketchpad는 여러 형태의 데이터를 반환할 수 있습니다:
    - dict with 'composite' key (이미지 데이터)
    - numpy array (이미지)
    - dict with 'layers' key

    이미지 데이터에서는 그려진 선의 좌표를 추출합니다.
    """
    if sketch_data is None:
        return []

    # Sketchpad가 이미지(numpy array 또는 dict)를 반환하는 경우
    img = None
    if isinstance(sketch_data, dict):
        if "composite" in sketch_data:
            img = sketch_data["composite"]
        elif "layers" in sketch_data and sketch_data["layers"]:
            img = sketch_data["layers"][-1]
    elif isinstance(sketch_data, np.ndarray):
        img = sketch_data

    if img is None:
        return []

    if isinstance(img, np.ndarray):
        return _extract_points_from_image(img)

    return []


def _extract_points_from_image(img):
    """
    이미지 배열에서 그려진 선의 좌표를 추출합니다.
    검은색이 아닌 픽셀을 찾아 좌표로 변환합니다.
    """
    if img is None or img.size == 0:
        return []

    # RGBA 또는 RGB 이미지에서 그려진 부분 감지
    if len(img.shape) == 3:
        if img.shape[2] == 4:
            # RGBA: 알파 채널이 0이 아닌 부분 또는 RGB 채널 합이 큰 부분
            mask = img[:, :, 3] > 10
        else:
            # RGB: 검은색(배경)이 아닌 부분
            mask = np.any(img[:, :, :3] > 10, axis=2)
    elif len(img.shape) == 2:
        mask = img > 10
    else:
        return []

    # 그려진 픽셀 좌표 추출
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return []

    # X좌표 기준으로 정렬하고 각 X에서 평균 Y 계산
    coords = list(zip(xs.tolist(), ys.tolist()))
    coords.sort(key=lambda c: c[0])

    # X좌표별로 그룹화하여 평균 Y 계산 (노이즈 감소)
    from collections import defaultdict
    x_groups = defaultdict(list)
    for x, y in coords:
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
            "선을 그려주세요! 왼쪽에서 오른쪽으로 선을 그린 후 변환 버튼을 누르세요.",
            []  # state
        )

    # 좌→우 방향 보정
    points = enforce_left_to_right(raw_points)

    # RDP 알고리즘으로 단순화
    simplified = simplify_line(points, epsilon)

    # 시각화
    fig = plot_line_comparison(
        points, simplified,
        canvas_width=CANVAS_WIDTH,
        canvas_height=CANVAS_HEIGHT
    )

    status = f"원본 포인트: {len(points)}개 → 단순화: {len(simplified)}개"

    return fig, status, simplified


def generate_music(simplified_state, time_sig_str, num_measures, bpm):
    """
    음악 생성하기 버튼 콜백:
    저장된 2차 데이터에서 음표를 배열하고 MIDI 파일을 생성합니다.
    """
    simplified = simplified_state
    if not simplified or len(simplified) < 2:
        return None, "먼저 선을 그리고 '선 변환하기' 버튼을 눌러주세요.", None

    time_signature = _parse_time_signature(time_sig_str)

    # 캔버스 크기 결정 (단순화된 데이터의 실제 범위 사용)
    xs = [p[0] for p in simplified]
    ys = [p[1] for p in simplified]
    canvas_w = max(xs) - min(xs) if max(xs) > min(xs) else CANVAS_WIDTH
    canvas_h = max(ys) - min(ys) if max(ys) > min(ys) else CANVAS_HEIGHT

    # X좌표를 0 기준으로 보정
    min_x = min(xs)
    adjusted_points = [(x - min_x, y) for x, y in simplified]

    # 음표 배열
    notes = arrange_notes(
        adjusted_points,
        canvas_width=canvas_w,
        canvas_height=canvas_h,
        time_signature=time_signature,
        num_measures=num_measures
    )

    if not notes:
        return None, "음표를 생성할 수 없습니다. 더 길거나 복잡한 선을 그려보세요.", None

    # 음표 텍스트 정보
    note_text = notes_to_text(notes)

    # MIDI 파일 생성 (보안을 위해 mkstemp 사용)
    fd, midi_path = tempfile.mkstemp(suffix=".mid")
    import os
    os.close(fd)
    generate_midi(
        notes,
        bpm=bpm,
        time_signature=time_signature,
        output_path=midi_path
    )

    return midi_path, note_text, midi_path


# ── Gradio UI 구성 ────────────────────────────────────

def create_app():
    """Gradio Blocks 앱을 생성합니다."""

    with gr.Blocks(
        title="Music In Line - 프로토타입",
    ) as app:

        gr.Markdown("# 🎼 Music In Line — 프로토타입")
        gr.Markdown("**내가 그린 선이 음악이 되는 마법!** 캔버스에 선을 그리면 음악(MIDI)으로 변환됩니다.")

        # 상태 저장 (2차 데이터)
        simplified_state = gr.State([])

        # ── Step 1: 선 그리기 ──
        gr.Markdown("## 🎨 Step 1: 선 그리기")
        gr.Markdown("왼쪽에서 오른쪽으로 자유롭게 선을 그려보세요! "
                     "가로축 = 시간(마디), 세로축 = 음높이(위: 높은 음, 아래: 낮은 음)")

        sketchpad = gr.Sketchpad(
            label="선 그리기 캔버스",
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            type="numpy"
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
        note_text_output = gr.Textbox(
            label="📝 음표 텍스트 정보",
            lines=10,
            interactive=False
        )
        midi_download = gr.File(label="🔊 MIDI 파일 다운로드")

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
            outputs=[midi_download, note_text_output, midi_download]
        )

    return app


# ── 메인 실행 ─────────────────────────────────────────

if __name__ == "__main__":
    app = create_app()
    app.launch()
