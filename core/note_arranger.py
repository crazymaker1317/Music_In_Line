"""
note_arranger.py — 직선 데이터 → 음표 배열 모듈

단순화된 직선 세그먼트 데이터와 박자 정보를 바탕으로
마디별 음표를 생성합니다.
"""

from dataclasses import dataclass
from core.pitch_mapper import map_y_to_pitch


@dataclass
class Note:
    """음표 하나를 나타내는 데이터 클래스"""
    pitch: int         # MIDI pitch (0-127). 쉼표의 경우 의미 없음.
    start_beat: float  # 마디 내 시작 위치 (박 단위)
    duration: float    # 음표 길이 (박 단위, 예: 1.0 = 4분음표)
    measure: int       # 소속 마디 번호 (0부터 시작)
    is_rest: bool = False  # True이면 쉼표(무음)


def _get_points_in_measure(points, measure_start_x, measure_end_x):
    """
    주어진 마디 영역(X범위)에 속하는 포인트들을 추출합니다.
    마디 경계에서의 보간(interpolation)도 수행합니다.

    Args:
        points: 전체 단순화된 좌표 리스트
        measure_start_x: 마디 시작 X좌표
        measure_end_x: 마디 끝 X좌표

    Returns:
        해당 마디 영역의 포인트 리스트
    """
    measure_points = []

    for i in range(len(points)):
        x, y = points[i]

        # 이전 점과 현재 점 사이에 마디 시작 경계가 있으면 보간점 추가
        if i > 0:
            prev_x, prev_y = points[i - 1]
            if prev_x < measure_start_x <= x and x - prev_x > 0:
                t = (measure_start_x - prev_x) / (x - prev_x)
                interp_y = prev_y + t * (y - prev_y)
                measure_points.append((measure_start_x, interp_y))

        # 마디 영역에 포함되는 점 추가
        if measure_start_x <= x <= measure_end_x:
            measure_points.append((x, y))

        # 이전 점과 현재 점 사이에 마디 끝 경계가 있으면 보간점 추가
        if i > 0:
            prev_x, prev_y = points[i - 1]
            if prev_x <= measure_end_x < x and x - prev_x > 0:
                t = (measure_end_x - prev_x) / (x - prev_x)
                interp_y = prev_y + t * (y - prev_y)
                measure_points.append((measure_end_x, interp_y))

    # X좌표 기준으로 정렬하고 중복 제거
    measure_points.sort(key=lambda p: p[0])
    unique_points = []
    for pt in measure_points:
        if not unique_points or abs(pt[0] - unique_points[-1][0]) > 1e-6:
            unique_points.append(pt)

    return unique_points


def _normalize_durations(durations, beats_per_measure):
    """
    음표 duration 리스트를 마디의 총 박자에 맞게 정규화합니다.

    Args:
        durations: 원래 duration 비율 리스트
        beats_per_measure: 마디당 박 수

    Returns:
        합이 beats_per_measure인 정규화된 duration 리스트
    """
    total = sum(durations)
    if total <= 0:
        n = len(durations)
        return [beats_per_measure / n] * n if n > 0 else []

    scale = beats_per_measure / total
    return [d * scale for d in durations]


def _quantize_duration(duration):
    """
    duration을 음악적으로 의미 있는 값으로 퀀타이즈합니다.
    허용 값: 0.25 (16분음표), 0.5 (8분음표), 1.0 (4분음표),
             1.5 (점4분음표), 2.0 (2분음표), 3.0 (점2분음표), 4.0 (온음표)

    Args:
        duration: 원래 duration (박 단위)

    Returns:
        퀀타이즈된 duration
    """
    allowed = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
    return min(allowed, key=lambda d: abs(d - duration))


def _select_top_points(points, max_count):
    """
    기울기 변화량이 큰 상위 포인트들을 선택합니다.
    첫 점과 끝 점은 항상 포함됩니다.

    Args:
        points: 포인트 리스트
        max_count: 최대 포인트 수

    Returns:
        선택된 포인트 리스트 (X좌표 순)
    """
    if len(points) <= max_count:
        return points

    # 각 중간 포인트의 기울기 변화량 계산
    angle_changes = []
    for i in range(1, len(points) - 1):
        prev_x, prev_y = points[i - 1]
        curr_x, curr_y = points[i]
        next_x, next_y = points[i + 1]

        # 이전 세그먼트와 다음 세그먼트의 기울기 차이
        dx1 = curr_x - prev_x
        dy1 = curr_y - prev_y
        dx2 = next_x - curr_x
        dy2 = next_y - curr_y

        slope1 = dy1 / dx1 if dx1 != 0 else float('inf')
        slope2 = dy2 / dx2 if dx2 != 0 else float('inf')

        if slope1 == float('inf') or slope2 == float('inf'):
            change = float('inf')
        else:
            change = abs(slope2 - slope1)

        angle_changes.append((i, change))

    # 기울기 변화량이 큰 순으로 정렬
    angle_changes.sort(key=lambda x: x[1], reverse=True)

    # 상위 포인트 인덱스 선택 (첫/끝 점은 항상 포함)
    selected_indices = {0, len(points) - 1}
    for idx, _ in angle_changes[:max_count - 2]:
        selected_indices.add(idx)

    # X좌표 순으로 정렬하여 반환
    return [points[i] for i in sorted(selected_indices)]


def _fix_measure_duration(notes, measure_idx, beats_per_measure):
    """
    특정 마디의 음표 총 길이가 beats_per_measure와 정확히 일치하도록 보정합니다.
    마지막 음표의 duration을 조정합니다.

    Args:
        notes: 전체 음표 리스트 (in-place 수정)
        measure_idx: 보정할 마디 번호
        beats_per_measure: 마디당 박 수
    """
    measure_notes = [n for n in notes if n.measure == measure_idx]
    if not measure_notes:
        return

    total_duration = sum(n.duration for n in measure_notes)
    diff = beats_per_measure - total_duration

    if abs(diff) > 0.001:
        # 마지막 음표의 duration을 조정
        last_note = measure_notes[-1]
        new_dur = last_note.duration + diff
        if new_dur >= 0.125:
            last_note.duration = new_dur
        elif len(measure_notes) > 1:
            # 마지막 음표가 너무 짧아지면 제거하고 그 이전 음표를 늘림
            notes.remove(last_note)
            prev_note = measure_notes[-2]
            # 이전 음표의 duration을 조정하여 마디를 채움
            recalc_total = sum(
                n.duration for n in notes if n.measure == measure_idx
            )
            prev_note.duration += (beats_per_measure - recalc_total)
        else:
            # 음표가 하나뿐이면 최소값으로 설정
            last_note.duration = max(new_dur, 0.25)


def arrange_notes(simplified_points, canvas_width, canvas_height,
                  time_signature, num_measures):
    """
    단순화된 직선 데이터를 박자에 맞게 음표로 변환합니다.

    Args:
        simplified_points: 단순화된 좌표 리스트
        canvas_width: 캔버스 가로 크기
        canvas_height: 캔버스 세로 크기
        time_signature: 박자 (분자, 분모), 예: (4, 4)
        num_measures: 총 마디 수

    Returns:
        생성된 Note 리스트
    """
    if not simplified_points or len(simplified_points) < 2:
        return []

    beats_per_measure = time_signature[0]  # 분자가 마디당 박 수
    measure_width = canvas_width / num_measures  # 마디당 캔버스 폭

    all_notes = []

    for measure_idx in range(num_measures):
        measure_start_x = measure_idx * measure_width
        measure_end_x = (measure_idx + 1) * measure_width

        # 해당 마디 영역의 포인트 추출
        measure_points = _get_points_in_measure(
            simplified_points, measure_start_x, measure_end_x
        )

        if len(measure_points) == 0:
            continue

        if len(measure_points) == 1:
            # 포인트가 하나뿐이면 마디 전체 길이 음표 하나
            pitch = map_y_to_pitch(measure_points[0][1], canvas_height)
            all_notes.append(Note(
                pitch=pitch,
                start_beat=0.0,
                duration=float(beats_per_measure),
                measure=measure_idx
            ))
            continue

        # 꺾이는 점이 박자 비트 수의 4배보다 많으면 상위 포인트만 선택
        key_points = measure_points
        if len(key_points) - 1 > beats_per_measure * 4:
            key_points = _select_top_points(
                key_points, max_count=beats_per_measure * 4
            )

        # 각 포인트 간 X 거리를 duration 비율로 사용
        raw_durations = []
        for i in range(len(key_points) - 1):
            dx = key_points[i + 1][0] - key_points[i][0]
            raw_durations.append(max(dx, 0.001))

        # 정규화하여 마디 총 박자에 맞춤
        normalized = _normalize_durations(raw_durations, beats_per_measure)

        # 각 음표 배치 — 마디 경계를 넘지 않도록 클리핑
        current_beat = 0.0
        for i, dur in enumerate(normalized):
            # 마디 경계를 이미 넘었으면 더 이상 음표를 추가하지 않음
            if current_beat >= beats_per_measure:
                break

            pitch = map_y_to_pitch(key_points[i][1], canvas_height)
            quantized_dur = _quantize_duration(dur)

            # 음표가 마디 경계를 넘지 않도록 클리핑
            remaining = beats_per_measure - current_beat
            if quantized_dur > remaining:
                quantized_dur = remaining

            # 너무 짧은 음표(0에 가까운)는 건너뛰기
            if quantized_dur < 0.125:
                continue

            all_notes.append(Note(
                pitch=pitch,
                start_beat=current_beat,
                duration=quantized_dur,
                measure=measure_idx
            ))
            current_beat += quantized_dur

        # 마디 내 음표 총 길이를 정확히 맞추기 위한 보정
        _fix_measure_duration(all_notes, measure_idx, beats_per_measure)

    return all_notes


def notes_to_text(notes):
    """
    Note 리스트를 사람이 읽을 수 있는 텍스트로 변환합니다.

    Args:
        notes: Note 리스트

    Returns:
        음표 정보 텍스트 문자열
    """
    from core.pitch_mapper import pitch_to_note_name

    # duration → 음표 이름 매핑
    duration_names = {
        0.25: "16분음표",
        0.5: "8분음표",
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

        dur_name = duration_names.get(note.duration, f"{note.duration}박")
        if note.is_rest:
            lines.append(f"  쉼표 - {dur_name} (시작: {note.start_beat:.1f}박)")
        else:
            note_name = pitch_to_note_name(note.pitch)
            lines.append(f"  {note_name} - {dur_name} (시작: {note.start_beat:.1f}박)")

    return "\n".join(lines) if lines else "음표가 생성되지 않았습니다."
