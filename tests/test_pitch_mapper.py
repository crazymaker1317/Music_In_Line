"""
test_pitch_mapper.py — Y좌표 → MIDI pitch 매핑 모듈 테스트
"""

import pytest
from core.pitch_mapper import map_y_to_pitch, pitch_to_note_name, _get_scale_pitches


class TestMapYToPitch:
    """map_y_to_pitch 함수 테스트"""

    def test_top_of_canvas(self):
        """캔버스 상단(y=0) → 최고 음높이"""
        result = map_y_to_pitch(0, 400, pitch_min=60, pitch_max=84)
        assert result == 84  # C6

    def test_bottom_of_canvas(self):
        """캔버스 하단(y=canvas_height) → 최저 음높이"""
        result = map_y_to_pitch(400, 400, pitch_min=60, pitch_max=84)
        assert result == 60  # C4

    def test_middle_of_canvas(self):
        """캔버스 중앙 → 중간 음높이"""
        result = map_y_to_pitch(200, 400, pitch_min=60, pitch_max=84)
        # 중앙은 raw_pitch = 72, C 메이저 스케일에서 72 = C5
        assert result == 72

    def test_result_in_c_major_scale(self):
        """결과가 C 메이저 스케일 음에 속하는지 확인"""
        c_major_offsets = {0, 2, 4, 5, 7, 9, 11}
        for y in range(0, 401, 10):
            pitch = map_y_to_pitch(y, 400, pitch_min=60, pitch_max=84)
            assert pitch % 12 in c_major_offsets, \
                f"y={y}에서 pitch={pitch}가 C 메이저 스케일에 속하지 않음"

    def test_result_in_range(self):
        """결과가 pitch 범위 내에 있는지 확인"""
        for y in range(0, 401, 10):
            pitch = map_y_to_pitch(y, 400, pitch_min=60, pitch_max=84)
            assert 60 <= pitch <= 84

    def test_invalid_canvas_height(self):
        """canvas_height <= 0이면 ValueError"""
        with pytest.raises(ValueError):
            map_y_to_pitch(100, 0)
        with pytest.raises(ValueError):
            map_y_to_pitch(100, -10)

    def test_y_out_of_bounds_clamp(self):
        """Y좌표가 캔버스 범위를 벗어나면 클램핑"""
        # y < 0 → 상단으로 취급
        top = map_y_to_pitch(-10, 400, pitch_min=60, pitch_max=84)
        assert top == 84
        # y > canvas_height → 하단으로 취급
        bottom = map_y_to_pitch(500, 400, pitch_min=60, pitch_max=84)
        assert bottom == 60


class TestPitchToNoteName:
    """pitch_to_note_name 함수 테스트"""

    def test_middle_c(self):
        """MIDI 60 = C4"""
        assert pitch_to_note_name(60) == "C4"

    def test_a4(self):
        """MIDI 69 = A4"""
        assert pitch_to_note_name(69) == "A4"

    def test_c6(self):
        """MIDI 84 = C6"""
        assert pitch_to_note_name(84) == "C6"


class TestGetScalePitches:
    """_get_scale_pitches 함수 테스트"""

    def test_c_major_range(self):
        """C4~C6 범위의 C 메이저 스케일"""
        pitches = _get_scale_pitches(60, 84, "C_major")
        assert 60 in pitches  # C4
        assert 84 in pitches  # C6
        # 검은 건반(반음)은 포함되지 않아야 함
        assert 61 not in pitches  # C#4
        assert 63 not in pitches  # D#4

    def test_unsupported_scale(self):
        """지원하지 않는 스케일이면 ValueError"""
        with pytest.raises(ValueError):
            _get_scale_pitches(60, 84, "D_minor")
