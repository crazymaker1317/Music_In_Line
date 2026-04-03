"""
midi_generator.py — MIDI 파일 생성 모듈

음표 배열(Note 리스트)을 MIDI 파일로 변환합니다.
midiutil 라이브러리를 사용합니다.
"""

import os
from midiutil import MIDIFile
from core.note_arranger import Note


def generate_midi(notes, bpm=120, time_signature=(4, 4),
                  output_path="output/result.mid"):
    """
    Note 리스트를 MIDI 파일로 생성합니다.

    Args:
        notes: 음표 리스트 (Note 객체들)
        bpm: 빠르기 (기본값 120)
        time_signature: 박자 (분자, 분모), 예: (4, 4)
        output_path: 저장 경로

    Returns:
        생성된 MIDI 파일 경로
    """
    if not notes:
        raise ValueError("음표 리스트가 비어있습니다.")

    # MIDI 파일 생성 (트랙 1개)
    midi = MIDIFile(1)

    track = 0
    channel = 0
    volume = 100  # 음량 (0~127)

    # 트랙 설정
    midi.addTrackName(track, 0, "Music In Line")
    midi.addTempo(track, 0, bpm)

    # 박자표 설정
    numerator = time_signature[0]
    # 분모는 2의 거듭제곱으로 표현 (4 → 2, 8 → 3)
    import math
    denominator_power = int(math.log2(time_signature[1]))
    midi.addTimeSignature(track, 0, numerator, denominator_power, 24, 8)

    # 음표를 MIDI 이벤트로 추가 (동일 피치+시간 중복 방지)
    beats_per_measure = time_signature[0]
    seen = {}  # (pitch, absolute_time) → duration (최대값 유지)
    for note in notes:
        # 절대 시간 계산: 마디 번호 * 마디당 박 수 + 마디 내 시작 위치
        absolute_time = note.measure * beats_per_measure + note.start_beat
        # 3자리 반올림: MIDI 해상도(PPQ=960)에서 충분한 정밀도이며,
        # 부동소수점 연산 오차(예: 0.999999... vs 1.0)를 올바르게 통합
        key = (note.pitch, round(absolute_time, 3))
        # 동일 피치+시간이면 더 긴 duration 유지
        if key in seen:
            if note.duration > seen[key]:
                seen[key] = note.duration
        else:
            seen[key] = note.duration

    for (pitch, absolute_time), duration in seen.items():
        # duration이 0 이하이면 건너뛰기
        if duration <= 0:
            continue
        midi.addNote(
            track=track,
            channel=channel,
            pitch=pitch,
            time=absolute_time,
            duration=duration,
            volume=volume
        )

    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else "output", exist_ok=True)

    # MIDI 파일 저장
    with open(output_path, "wb") as f:
        midi.writeFile(f)

    return output_path
