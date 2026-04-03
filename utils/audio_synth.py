"""
audio_synth.py — 간단한 오디오 합성 모듈

Note 리스트를 WAV 파일로 변환합니다.
사인파 합성을 사용하여 외부 사운드폰트 의존성 없이 동작합니다.
"""

import math
import struct
import wave

from core.note_arranger import Note


def synthesize_wav(notes, bpm=120, time_signature=(4, 4),
                   output_path="output/result.wav",
                   sample_rate=44100):
    """
    Note 리스트를 WAV 파일로 합성합니다.

    Args:
        notes: 음표 리스트 (Note 객체들)
        bpm: 빠르기 (기본값 120)
        time_signature: 박자 (분자, 분모)
        output_path: 저장 경로
        sample_rate: 샘플링 레이트 (기본 44100 Hz)

    Returns:
        생성된 WAV 파일 경로
    """
    if not notes:
        raise ValueError("음표 리스트가 비어있습니다.")

    beats_per_measure = time_signature[0]
    seconds_per_beat = 60.0 / bpm

    # 전체 음악 길이 계산 (초)
    max_end_time = 0.0
    for note in notes:
        abs_start_beat = note.measure * beats_per_measure + note.start_beat
        end_beat = abs_start_beat + note.duration
        end_time = end_beat * seconds_per_beat
        if end_time > max_end_time:
            max_end_time = end_time

    total_samples = int(max_end_time * sample_rate) + sample_rate  # 1초 여유
    audio_buffer = [0.0] * total_samples

    # 각 음표를 사인파로 합성
    for note in notes:
        abs_start_beat = note.measure * beats_per_measure + note.start_beat
        start_sec = abs_start_beat * seconds_per_beat
        duration_sec = note.duration * seconds_per_beat

        # MIDI pitch → 주파수 (Hz)
        frequency = 440.0 * (2.0 ** ((note.pitch - 69) / 12.0))

        start_sample = int(start_sec * sample_rate)
        num_samples = int(duration_sec * sample_rate)

        # ADSR 엔벨로프 (어택-디케이-서스테인-릴리스)
        attack_samples = min(int(0.02 * sample_rate), num_samples // 4)
        release_samples = min(int(0.05 * sample_rate), num_samples // 4)
        sustain_level = 0.7

        for j in range(num_samples):
            idx = start_sample + j
            if idx >= total_samples:
                break

            # 엔벨로프 계산
            if j < attack_samples:
                envelope = j / attack_samples
            elif j >= num_samples - release_samples:
                remaining = num_samples - j
                envelope = sustain_level * (remaining / release_samples)
            else:
                envelope = sustain_level

            # 사인파 + 2차 하모닉스 (더 풍부한 소리)
            t = j / sample_rate
            sample = (0.7 * math.sin(2.0 * math.pi * frequency * t)
                      + 0.2 * math.sin(4.0 * math.pi * frequency * t)
                      + 0.1 * math.sin(6.0 * math.pi * frequency * t))

            audio_buffer[idx] += sample * envelope * 0.3

    # 클리핑 방지
    max_val = max(abs(s) for s in audio_buffer) if audio_buffer else 1.0
    if max_val > 1.0:
        audio_buffer = [s / max_val for s in audio_buffer]

    # WAV 파일 저장
    import os
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with wave.open(output_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)

        for sample in audio_buffer:
            clamped = max(-1.0, min(1.0, sample))
            packed = struct.pack('<h', int(clamped * 32767))
            wf.writeframes(packed)

    return output_path
