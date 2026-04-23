"""
beat_grid_sampler.py — Baet-grid 샘플링 기반 음표 배열 모듈

기존 RDP 알고리즘과는 다른 새로운 샘플링 방식입니다.

개념:
- 캔버스를 가로축으로 `num_measures * cells_per_measure` 개의 비트 칸으로
  나눕니다. (기본: 4마디 × 16셀 = 64 셀, 즉 16분음표 단위.)
- 세로축은 1.00(도) ~ 13.00(높은 도) 범위의 음높이 값으로 해석됩니다.
  1 = 도, 2 = 도#, 3 = 레, 4 = 레#, 5 = 미, 6 = 파, 7 = 파#,
  8 = 솔, 9 = 솔#, 10 = 라, 11 = 라#, 12 = 시, 13 = 높은 도.
- 각 셀 안에 포함된 점들의 세로축 값 평균을 반올림하여
  그 셀의 음높이 정수값(1~13)으로 사용합니다.
- 연속된 셀이 동일한 정수값을 가지면 하나의 음표로 병합합니다.
- 한 셀 안의 점 개수가 임계값(기본 2) 이하이면 그 셀은 쉼표로 처리합니다.
- 한 셀 안에 같은 X값을 지닌 점이 여러 개이면(예: '@' 같이 선이 되돌아오는
  복잡한 그림), 가장 먼저 찍힌 점 하나만을 인식합니다.
"""

from core.note_arranger import Note


# 1..13 정수 → 한글 음명 (디버깅/표시용)
PITCH_VALUE_NAMES_KR = {
    1: "도", 2: "도#", 3: "레", 4: "레#", 5: "미", 6: "파",
    7: "파#", 8: "솔", 9: "솔#", 10: "라", 11: "라#", 12: "시",
    13: "높은 도",
}

# 마디 하나당 비트 칸 수 (16분음표 단위)
DEFAULT_CELLS_PER_MEASURE = 16
# 쉼표 판단 기준: 한 셀 안에 들어간 점이 이 값 이하이면 쉼표
DEFAULT_REST_POINT_THRESHOLD = 2
# 음높이 정수값 1에 해당하는 MIDI pitch (C4 = 60). 13이면 C5 = 72.
PITCH_VALUE_BASE_MIDI = 60


def pitch_value_to_midi(value: int) -> int:
    """1..13 정수 음높이 값을 MIDI pitch(60..72)로 변환합니다."""
    return PITCH_VALUE_BASE_MIDI + int(value) - 1


def y_to_pitch_value(y: float, canvas_height: float) -> float:
    """
    캔버스 Y좌표를 1.0~13.0 범위의 연속적인 음높이 값으로 변환합니다.

    캔버스 상단(y=0)이 13.0 (높은 도), 하단(y=canvas_height)이 1.0 (도)
    에 대응합니다.
    """
    if canvas_height <= 0:
        raise ValueError("canvas_height는 0보다 커야 합니다.")
    normalized = max(0.0, min(1.0, y / canvas_height))
    # 위쪽이 높은 음: normalized=0 → 13.0, normalized=1 → 1.0
    return 13.0 - normalized * 12.0


def sample_beat_grid(points, canvas_width, canvas_height,
                      num_measures: int = 4,
                      time_signature=(4, 4),
                      cells_per_measure: int = DEFAULT_CELLS_PER_MEASURE,
                      rest_threshold: int = DEFAULT_REST_POINT_THRESHOLD):
    """
    포인트 리스트를 Baet-grid 샘플링 방식으로 음표 리스트로 변환합니다.

    Args:
        points: 원본 좌표 리스트 [(x, y), ...] — 사용자가 그린 모든 점.
        canvas_width: 캔버스 가로 크기 (픽셀 또는 임의 단위).
        canvas_height: 캔버스 세로 크기.
        num_measures: 총 마디 수 (기본 4).
        time_signature: 박자 (분자, 분모). 개념 증명 단계에서는 (4, 4) 전제.
        cells_per_measure: 마디당 비트 칸 수 (기본 16 = 16분음표 단위).
        rest_threshold: 한 셀의 점 개수가 이 값 이하이면 쉼표로 처리.

    Returns:
        Note 리스트. 쉼표는 `is_rest=True`로 표시됩니다.
        동일 음높이가 연속된 셀들은 하나의 음표로 병합되며,
        마디 경계를 넘는 병합은 마디별로 분할됩니다.
    """
    if canvas_width <= 0 or canvas_height <= 0:
        return []
    if num_measures <= 0 or cells_per_measure <= 0:
        return []

    total_cells = num_measures * cells_per_measure
    cell_width = canvas_width / total_cells

    # 각 셀에 속한 점들의 Y 값을 수집
    # 예외 처리: 한 셀 안에 같은 X값을 가진 점이 여러 개이면(학생이 '@' 같이
    # 선이 되돌아오는 복잡한 그림을 그린 경우), 가장 먼저 찍힌 점만 인식한다.
    cell_y_values: list[list[float]] = [[] for _ in range(total_cells)]
    cell_seen_x: list[set[float]] = [set() for _ in range(total_cells)]
    for x, y in points:
        if x < 0 or x > canvas_width:
            continue
        cell_idx = int(x / cell_width) if cell_width > 0 else 0
        if cell_idx >= total_cells:
            cell_idx = total_cells - 1
        if cell_idx < 0:
            cell_idx = 0
        if x in cell_seen_x[cell_idx]:
            continue
        cell_seen_x[cell_idx].add(x)
        cell_y_values[cell_idx].append(y)

    # 각 셀의 음높이 정수값 (또는 None = 쉼표) 산출
    cell_pitches: list[int | None] = []
    for ys in cell_y_values:
        if len(ys) <= rest_threshold:
            cell_pitches.append(None)
            continue
        avg_y = sum(ys) / len(ys)
        raw = y_to_pitch_value(avg_y, canvas_height)
        # 1..13 범위로 클램프한 뒤 반올림
        clamped = max(1.0, min(13.0, raw))
        cell_pitches.append(int(round(clamped)))

    # 연속된 동일 값 (또는 연속된 쉼표)을 하나의 음표로 병합
    beats_per_measure = time_signature[0]
    # 마디당 박 수 / 마디당 셀 수 = 셀 하나의 박 길이
    # 4/4 + 16셀 → 4 / 16 = 0.25 박 (16분음표)
    beat_per_cell = beats_per_measure / cells_per_measure

    notes: list[Note] = []
    i = 0
    while i < total_cells:
        current = cell_pitches[i]
        run = 1
        while i + run < total_cells and cell_pitches[i + run] == current:
            run += 1

        # 이 묶음을 마디 경계에 맞춰 분할
        measure_idx = i // cells_per_measure
        cell_in_measure = i % cells_per_measure
        start_beat = cell_in_measure * beat_per_cell
        remaining = run

        while remaining > 0:
            cells_left_in_measure = cells_per_measure - cell_in_measure
            take = min(remaining, cells_left_in_measure)
            duration = take * beat_per_cell

            if current is None:
                notes.append(Note(
                    pitch=0,
                    start_beat=start_beat,
                    duration=duration,
                    measure=measure_idx,
                    is_rest=True,
                ))
            else:
                notes.append(Note(
                    pitch=pitch_value_to_midi(current),
                    start_beat=start_beat,
                    duration=duration,
                    measure=measure_idx,
                    is_rest=False,
                ))

            remaining -= take
            if remaining > 0:
                measure_idx += 1
                cell_in_measure = 0
                start_beat = 0.0

        i += run

    return notes


def beat_grid_summary(notes) -> str:
    """
    Baet-grid 샘플링 결과를 사용자 친화적인 한국어 텍스트로 요약합니다.
    """
    if not notes:
        return "음표가 생성되지 않았습니다."

    # duration → 음표 이름
    duration_names = {
        0.25: "16분음표",
        0.5: "8분음표",
        0.75: "점8분음표",
        1.0: "4분음표",
        1.5: "점4분음표",
        2.0: "2분음표",
        3.0: "점2분음표",
        4.0: "온음표",
    }

    lines = []
    current_measure = -1
    for note in notes:
        if note.measure != current_measure:
            current_measure = note.measure
            lines.append(f"\n--- 마디 {current_measure + 1} ---")

        dur_name = duration_names.get(
            round(note.duration, 3), f"{note.duration}박"
        )
        if note.is_rest:
            lines.append(f"  쉼표 - {dur_name}")
        else:
            value = note.pitch - PITCH_VALUE_BASE_MIDI + 1
            name = PITCH_VALUE_NAMES_KR.get(value, f"pitch{note.pitch}")
            lines.append(f"  {name} - {dur_name}")

    return "\n".join(lines)
