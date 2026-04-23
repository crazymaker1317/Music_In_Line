"""
visualization.py — 선 변환 결과 시각화 모듈

원본 곡선과 단순화된 직선 데이터를 matplotlib으로 시각화합니다.
"""

import platform
import matplotlib
matplotlib.use('Agg')  # GUI 없는 환경에서도 동작하도록 백엔드 설정
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np


# ── 한글 폰트 설정 ─────────────────────────────────────
def _setup_korean_font():
    """
    시스템에서 한글 폰트를 찾아 matplotlib에 설정합니다.
    한글 폰트를 찾지 못하면 False를 반환합니다.
    """
    system = platform.system()

    # 시스템별 한글 폰트 후보 목록
    if system == 'Windows':
        candidates = ['Malgun Gothic', 'NanumGothic', 'Gulim', 'Batang',
                       'NanumBarunGothic', 'Dotum']
    elif system == 'Darwin':
        candidates = ['AppleGothic', 'Apple SD Gothic Neo', 'NanumGothic']
    else:
        candidates = ['NanumGothic', 'NanumBarunGothic', 'UnDotum',
                       'Noto Sans CJK KR', 'Noto Sans CJK']

    available = {f.name for f in fm.fontManager.ttflist}

    for font_name in candidates:
        if font_name in available:
            plt.rcParams['font.family'] = font_name
            plt.rcParams['axes.unicode_minus'] = False
            return True

    return False


_HAS_KOREAN_FONT = _setup_korean_font()


def _label(korean, english):
    """한글 폰트가 있으면 한글, 없으면 영문 라벨을 반환합니다."""
    return korean if _HAS_KOREAN_FONT else english


def plot_line_comparison(original_points, simplified_points,
                         canvas_width=800, canvas_height=400,
                         num_measures=4):
    """
    원본 곡선과 단순화된 직선을 겹쳐서 비교 시각화합니다.

    Args:
        original_points: 원본 좌표 리스트 [(x1, y1), ...]
        simplified_points: 단순화된 좌표 리스트 [(x1, y1), ...]
        canvas_width: 캔버스 가로 크기
        canvas_height: 캔버스 세로 크기
        num_measures: 마디 수 (가이드라인 표시용)

    Returns:
        matplotlib Figure 객체
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 5))

    # 원본 곡선 그리기
    if original_points:
        orig_x = [p[0] for p in original_points]
        orig_y = [p[1] for p in original_points]
        ax.plot(orig_x, orig_y, 'b-', alpha=0.3, linewidth=1,
                label=_label('원본 곡선', 'Original curve'))

    # 단순화된 직선 그리기
    if simplified_points:
        simp_x = [p[0] for p in simplified_points]
        simp_y = [p[1] for p in simplified_points]
        ax.plot(simp_x, simp_y, 'r-o', linewidth=2, markersize=6,
                label=_label('단순화된 직선', 'Simplified line'))

    # 마디 구분선 그리기
    measure_width = canvas_width / num_measures
    for i in range(num_measures + 1):
        x = i * measure_width
        ax.axvline(x=x, color='gray', linestyle='--', alpha=0.5)
        if i < num_measures:
            label_text = _label(f'마디 {i + 1}', f'M{i + 1}')
            ax.text(x + measure_width / 2, canvas_height * 0.02,
                    label_text, ha='center', fontsize=9, color='gray')

    # 축 설정
    ax.set_xlim(0, canvas_width)
    ax.set_ylim(0, canvas_height)
    ax.invert_yaxis()  # Y축 반전 (캔버스 좌표계: 위=0)
    ax.set_xlabel(_label('시간 (X축)', 'Time (X)'))
    ax.set_ylabel(_label('음높이 (Y축) — 위: 높은 음, 아래: 낮은 음',
                         'Pitch (Y) — top: high, bottom: low'))
    ax.set_title(_label('선 변환 결과', 'Line Conversion Result'))
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.2)

    plt.tight_layout()
    return fig


def plot_piano_roll(notes, time_signature=(4, 4), num_measures=4):
    """
    음표 배열을 피아노 롤(piano roll) 형태로 시각화합니다.

    Args:
        notes: Note 리스트
        time_signature: 박자 (분자, 분모)
        num_measures: 총 마디 수

    Returns:
        matplotlib Figure 객체
    """
    from core.pitch_mapper import pitch_to_note_name

    if not notes:
        fig, ax = plt.subplots(1, 1, figsize=(12, 4))
        ax.text(0.5, 0.5, _label('음표가 없습니다', 'No notes'),
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        return fig

    beats_per_measure = time_signature[0]
    total_beats = beats_per_measure * num_measures

    # 피치 범위 계산 — 쉼표는 제외
    pitched_notes = [n for n in notes if not getattr(n, "is_rest", False)]
    if pitched_notes:
        pitches = [n.pitch for n in pitched_notes]
        pitch_min = min(pitches) - 2
        pitch_max = max(pitches) + 2
    else:
        # 모든 음표가 쉼표인 경우 기본 범위 사용 (C4~C5 부근)
        pitch_min = 58
        pitch_max = 74

    fig, ax = plt.subplots(1, 1, figsize=(12, 4))

    # 마디 구분선
    for i in range(num_measures + 1):
        beat_x = i * beats_per_measure
        ax.axvline(x=beat_x, color='gray', linestyle='--', alpha=0.5)
        if i < num_measures:
            label_text = _label(f'마디 {i + 1}', f'M{i + 1}')
            ax.text(beat_x + beats_per_measure / 2, pitch_max + 0.5,
                    label_text, ha='center', fontsize=9, color='gray')

    # 박 구분선 (보조)
    for i in range(total_beats + 1):
        ax.axvline(x=i, color='lightgray', linestyle='-', alpha=0.3)

    # 음표를 사각형으로 표시 (쉼표는 별도로 처리)
    colors = plt.cm.Set2(np.linspace(0, 1, num_measures))
    rest_y = (pitch_min + pitch_max) / 2.0  # 쉼표 표시용 Y 위치
    for note in notes:
        abs_start = note.measure * beats_per_measure + note.start_beat
        if getattr(note, "is_rest", False):
            # 쉼표: 반투명 회색 해치 사각형 + '𝄽' 표기
            rect = plt.Rectangle(
                (abs_start, pitch_min + 0.2),
                note.duration, pitch_max - pitch_min - 0.4,
                facecolor='lightgray', edgecolor='gray',
                linewidth=0.5, alpha=0.25, hatch='//'
            )
            ax.add_patch(rect)
            if note.duration >= 0.25:
                ax.text(abs_start + note.duration / 2, rest_y,
                        _label('쉼표', 'rest'),
                        ha='center', va='center', fontsize=7,
                        color='dimgray', fontweight='bold')
            continue
        color = colors[note.measure % len(colors)]
        rect = plt.Rectangle(
            (abs_start, note.pitch - 0.4),
            note.duration, 0.8,
            facecolor=color, edgecolor='black', linewidth=0.5, alpha=0.8
        )
        ax.add_patch(rect)
        # 음표 이름 표시
        note_name = pitch_to_note_name(note.pitch)
        if note.duration >= 0.5:
            ax.text(abs_start + note.duration / 2, note.pitch,
                    note_name, ha='center', va='center', fontsize=7,
                    fontweight='bold')

    # Y축 설정 — 피치를 음 이름으로 표시
    y_ticks = list(range(pitch_min, pitch_max + 1))
    y_labels = []
    for p in y_ticks:
        if p % 12 in [0, 2, 4, 5, 7, 9, 11]:  # Natural notes (white keys)
            y_labels.append(pitch_to_note_name(p))
        else:
            y_labels.append('')
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, fontsize=7)

    ax.set_xlim(0, total_beats)
    ax.set_ylim(pitch_min - 0.5, pitch_max + 1.5)
    ax.set_xlabel(_label(f'박 (beat) — {time_signature[0]}/{time_signature[1]} 박자',
                         f'Beat — {time_signature[0]}/{time_signature[1]} time'))
    ax.set_ylabel(_label('음높이', 'Pitch'))
    ax.set_title(_label('음표 배치 (피아노 롤)', 'Note Placement (Piano Roll)'))

    plt.tight_layout()
    return fig


def plot_beat_grid(points, notes, canvas_width=800, canvas_height=400,
                   num_measures=4, cells_per_measure=16):
    """
    Baet-grid 샘플링 결과를 시각화합니다.
    원본 그린 점과, 총 `num_measures * cells_per_measure`개의 비트 칸으로
    구분된 그리드, 각 칸에 배정된 음높이 값을 함께 표시합니다.
    """
    from core.beat_grid_sampler import PITCH_VALUE_BASE_MIDI, PITCH_VALUE_NAMES_KR

    total_cells = num_measures * cells_per_measure
    fig, ax = plt.subplots(1, 1, figsize=(12, 5))

    # 원본 포인트
    if points:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        ax.scatter(xs, ys, s=3, c='steelblue', alpha=0.5,
                   label=_label('그린 점', 'drawn points'))

    # 비트 칸 구분선
    cell_width = canvas_width / total_cells
    for c in range(total_cells + 1):
        x = c * cell_width
        if c % cells_per_measure == 0:
            ax.axvline(x=x, color='gray', linestyle='-', alpha=0.6)
        else:
            ax.axvline(x=x, color='lightgray', linestyle=':', alpha=0.4)

    # 마디 라벨
    measure_width = canvas_width / num_measures
    for i in range(num_measures):
        label_text = _label(f'마디 {i + 1}', f'M{i + 1}')
        ax.text(i * measure_width + measure_width / 2, canvas_height * 0.02,
                label_text, ha='center', fontsize=9, color='gray')

    # 각 셀의 배정된 음높이(또는 쉼표) 표시
    cell_pitch_value = [None] * total_cells
    beats_per_measure = 4  # Baet-grid은 4/4 전제
    beat_per_cell = beats_per_measure / cells_per_measure
    for note in notes:
        measure_start_cell = note.measure * cells_per_measure
        start_cell = measure_start_cell + int(round(note.start_beat / beat_per_cell))
        num_cells_in_note = max(1, int(round(note.duration / beat_per_cell)))
        for k in range(num_cells_in_note):
            idx = start_cell + k
            if 0 <= idx < total_cells:
                if getattr(note, "is_rest", False):
                    cell_pitch_value[idx] = 0  # 쉼표 표기
                else:
                    cell_pitch_value[idx] = note.pitch - PITCH_VALUE_BASE_MIDI + 1

    for c in range(total_cells):
        v = cell_pitch_value[c]
        if v is None:
            continue
        cx = (c + 0.5) * cell_width
        if v == 0:
            cy = canvas_height * 0.5
            ax.add_patch(plt.Rectangle(
                (c * cell_width, 0), cell_width, canvas_height,
                facecolor='lightgray', alpha=0.15, hatch='//',
                edgecolor='none'
            ))
            ax.text(cx, cy, _label('쉼', 'R'),
                    ha='center', va='center', fontsize=8, color='dimgray',
                    fontweight='bold')
        else:
            # 음높이 13=상단, 1=하단
            cy = canvas_height * (1.0 - (v - 1) / 12.0)
            ax.add_patch(plt.Rectangle(
                (c * cell_width, cy - canvas_height * 0.02),
                cell_width, canvas_height * 0.04,
                facecolor='tomato', alpha=0.7, edgecolor='darkred',
                linewidth=0.5
            ))
            name = PITCH_VALUE_NAMES_KR.get(v, str(v)) if _HAS_KOREAN_FONT else str(v)
            ax.text(cx, cy, name, ha='center', va='center',
                    fontsize=7, fontweight='bold')

    ax.set_xlim(0, canvas_width)
    ax.set_ylim(0, canvas_height)
    ax.invert_yaxis()
    ax.set_xlabel(_label('시간 (X축) — 64개 비트 칸',
                          'Time (X) — 64 beat cells'))
    ax.set_ylabel(_label('음높이 (위: 높은 도=13, 아래: 도=1)',
                          'Pitch (top: high C=13, bottom: C=1)'))
    ax.set_title(_label('Baet-grid 샘플링 결과',
                         'Baet-grid Sampling Result'))
    if points:
        ax.legend(loc='upper right')
    ax.grid(False)

    plt.tight_layout()
    return fig
