"""
test_note_arranger.py — 음표 배열 모듈 테스트
"""

import pytest
from core.note_arranger import arrange_notes, notes_to_text, Note


class TestArrangeNotes:
    """arrange_notes 함수 테스트"""

    def test_empty_input(self):
        """빈 입력 처리"""
        result = arrange_notes([], 800, 400, (4, 4), 4)
        assert result == []

    def test_single_point(self):
        """포인트 하나만 있으면 음표 없음 (최소 2개 필요)"""
        result = arrange_notes([(100, 200)], 800, 400, (4, 4), 4)
        assert result == []

    def test_simple_straight_line(self):
        """직선(2포인트) → 각 마디에 음표가 생성됨"""
        points = [(0, 200), (800, 200)]
        result = arrange_notes(points, 800, 400, (4, 4), 4)
        assert len(result) > 0
        # 모든 음표가 유효한 measure 번호를 가짐
        for note in result:
            assert 0 <= note.measure < 4

    def test_different_time_signatures(self):
        """같은 입력에 대해 박자가 다르면 결과가 달라질 수 있음"""
        points = [(0, 100), (200, 300), (400, 100), (600, 300), (800, 100)]

        result_44 = arrange_notes(points, 800, 400, (4, 4), 4)
        result_34 = arrange_notes(points, 800, 400, (3, 4), 4)
        result_24 = arrange_notes(points, 800, 400, (2, 4), 4)

        # 4/4 박자는 마디당 4박, 3/4는 3박, 2/4는 2박
        for note in result_44:
            measure_notes = [n for n in result_44 if n.measure == note.measure]
            total = sum(n.duration for n in measure_notes)
            assert abs(total - 4.0) < 0.5, f"4/4 마디 {note.measure} 총 박: {total}"

    def test_note_pitches_in_range(self):
        """생성된 음표의 pitch가 유효 범위 내에 있는지 확인"""
        points = [(0, 0), (200, 400), (400, 0), (600, 400), (800, 200)]
        result = arrange_notes(points, 800, 400, (4, 4), 4)
        for note in result:
            assert 60 <= note.pitch <= 84, f"pitch {note.pitch}가 범위를 벗어남"

    def test_note_has_positive_duration(self):
        """모든 음표의 duration이 양수인지 확인"""
        points = [(0, 100), (100, 200), (200, 150), (400, 300),
                  (500, 100), (600, 250), (700, 50), (800, 200)]
        result = arrange_notes(points, 800, 400, (4, 4), 4)
        for note in result:
            assert note.duration > 0, f"음표 duration이 0 이하: {note}"


class TestNotesToText:
    """notes_to_text 함수 테스트"""

    def test_empty_notes(self):
        """빈 음표 리스트"""
        result = notes_to_text([])
        assert "음표가 생성되지 않았습니다" in result

    def test_single_note(self):
        """음표 하나"""
        notes = [Note(pitch=60, start_beat=0.0, duration=4.0, measure=0)]
        result = notes_to_text(notes)
        assert "C4" in result
        assert "마디 1" in result

    def test_multiple_measures(self):
        """여러 마디에 걸친 음표"""
        notes = [
            Note(pitch=60, start_beat=0.0, duration=2.0, measure=0),
            Note(pitch=64, start_beat=2.0, duration=2.0, measure=0),
            Note(pitch=67, start_beat=0.0, duration=4.0, measure=1),
        ]
        result = notes_to_text(notes)
        assert "마디 1" in result
        assert "마디 2" in result
