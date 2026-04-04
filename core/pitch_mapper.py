"""
pitch_mapper.py — Y좌표 → MIDI pitch 매핑 모듈

캔버스의 Y좌표를 MIDI 음높이(pitch)로 변환하고,
선택된 음계(스케일)에 맞게 퀀타이즈합니다.
"""

# C 메이저 스케일의 음 이름과 MIDI pitch 오프셋 (C=0 기준)
C_MAJOR_OFFSETS = [0, 2, 4, 5, 7, 9, 11]  # C, D, E, F, G, A, B

# MIDI pitch → 음 이름 매핑 (옥타브 포함)
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def _get_scale_pitches(pitch_min: int, pitch_max: int,
                       scale: str = "C_major") -> list[int]:
    """
    지정된 범위 내에서 스케일에 속하는 MIDI pitch 목록을 생성합니다.

    Args:
        pitch_min: 최저 MIDI pitch
        pitch_max: 최고 MIDI pitch
        scale: 스케일 이름 (현재 "C_major"만 지원)

    Returns:
        스케일에 속하는 MIDI pitch 리스트 (오름차순)
    """
    if scale != "C_major":
        raise ValueError(f"지원하지 않는 스케일: {scale}. 현재 'C_major'만 지원됩니다.")

    pitches = []
    for midi_pitch in range(pitch_min, pitch_max + 1):
        # MIDI pitch를 12로 나눈 나머지가 C 메이저 스케일 오프셋에 해당하는지 확인
        if (midi_pitch % 12) in C_MAJOR_OFFSETS:
            pitches.append(midi_pitch)
    return pitches


def _quantize_to_scale(pitch: float, scale_pitches: list[int]) -> int:
    """
    주어진 pitch 값을 스케일 내 가장 가까운 음으로 퀀타이즈합니다.

    Args:
        pitch: 연속적인 MIDI pitch 값 (float)
        scale_pitches: 스케일에 속하는 MIDI pitch 리스트

    Returns:
        가장 가까운 스케일 음의 MIDI pitch (int)
    """
    if not scale_pitches:
        return round(pitch)

    closest = min(scale_pitches, key=lambda p: abs(p - pitch))
    return closest


def map_y_to_pitch(y: float, canvas_height: float,
                   pitch_min: int = 60, pitch_max: int = 84,
                   scale: str = "C_major") -> int:
    """
    캔버스 Y좌표를 MIDI pitch로 변환합니다.

    캔버스 상단(y=0)이 높은 음, 하단(y=canvas_height)이 낮은 음에 대응합니다.

    Args:
        y: 캔버스 Y좌표 (0 = 상단, canvas_height = 하단)
        canvas_height: 캔버스 세로 크기
        pitch_min: 최저 MIDI pitch (기본 C4 = 60)
        pitch_max: 최고 MIDI pitch (기본 C6 = 84)
        scale: 퀀타이즈할 스케일 (기본 C 메이저)

    Returns:
        퀀타이즈된 MIDI pitch 값 (정수)
    """
    if canvas_height <= 0:
        raise ValueError("canvas_height는 0보다 커야 합니다.")

    # Y좌표를 0~1 범위로 정규화 (상단=0, 하단=1)
    normalized = max(0.0, min(1.0, y / canvas_height))

    # 상단이 높은 음이므로 반전: normalized=0 → pitch_max, normalized=1 → pitch_min
    raw_pitch = pitch_max - normalized * (pitch_max - pitch_min)

    # 스케일에 맞게 퀀타이즈
    scale_pitches = _get_scale_pitches(pitch_min, pitch_max, scale)
    return _quantize_to_scale(raw_pitch, scale_pitches)


def pitch_to_note_name(pitch: int) -> str:
    """
    MIDI pitch 값을 음 이름(예: 'C4', 'E5')으로 변환합니다.

    Args:
        pitch: MIDI pitch 값 (0~127)

    Returns:
        음 이름 문자열
    """
    octave = (pitch // 12) - 1
    note_index = pitch % 12
    return f"{NOTE_NAMES[note_index]}{octave}"
