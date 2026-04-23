"""
test_beat_grid_sampler.py — Baet-grid 샘플링 모듈 테스트
"""

import pytest
from core.beat_grid_sampler import (
    sample_beat_grid,
    beat_grid_summary,
    y_to_pitch_value,
    pitch_value_to_midi,
    PITCH_VALUE_BASE_MIDI,
)


class TestYToPitchValue:
    """y_to_pitch_value 함수 테스트 (Y좌표 → 1.0~13.0)"""

    def test_top_is_highest_pitch(self):
        """캔버스 상단(y=0)은 13.0(높은 도)에 대응"""
        assert y_to_pitch_value(0, 400) == pytest.approx(13.0)

    def test_bottom_is_lowest_pitch(self):
        """캔버스 하단(y=canvas_height)은 1.0(도)에 대응"""
        assert y_to_pitch_value(400, 400) == pytest.approx(1.0)

    def test_middle(self):
        """중간값은 7.0(파) 근처"""
        assert y_to_pitch_value(200, 400) == pytest.approx(7.0)

    def test_invalid_height(self):
        """canvas_height가 0 이하이면 ValueError"""
        with pytest.raises(ValueError):
            y_to_pitch_value(10, 0)

    def test_out_of_range_clamped(self):
        """범위를 벗어나도 1.0~13.0 사이로 클램프되어 반환"""
        v_above = y_to_pitch_value(-50, 400)
        v_below = y_to_pitch_value(500, 400)
        assert 1.0 <= v_below <= 13.0
        assert 1.0 <= v_above <= 13.0


class TestPitchValueToMidi:
    """pitch_value_to_midi 함수 테스트"""

    def test_value_1_is_c4(self):
        assert pitch_value_to_midi(1) == 60  # C4

    def test_value_13_is_c5(self):
        assert pitch_value_to_midi(13) == 72  # C5

    def test_intermediate(self):
        assert pitch_value_to_midi(5) == 64  # E4 (미)


class TestSampleBeatGrid:
    """sample_beat_grid 함수 테스트"""

    def test_empty_input(self):
        """빈 입력이면 모든 셀이 쉼표(총 64개가 1개 덩어리로 합쳐짐)"""
        result = sample_beat_grid([], 800, 400)
        # 모든 셀이 쉼표이면 마디 경계마다 1개씩 → 4개의 쉼표
        assert len(result) == 4
        assert all(n.is_rest for n in result)

    def test_all_rest_when_few_points(self):
        """셀당 2점 이하면 쉼표"""
        # 하나의 셀에 1점만 있으면 쉼표 처리
        points = [(10, 200), (20, 200)]
        result = sample_beat_grid(points, 800, 400)
        assert all(n.is_rest for n in result)

    def test_horizontal_line_generates_single_note_per_measure(self):
        """수평선(일정 Y값)이면 마디마다 전체 셀이 동일 음표로 병합"""
        # 각 셀마다 5개 점을 배치 — 64 셀 × 5점 = 320점, 모두 y=200
        points = [(x + 0.5, 200) for x in range(800) if x % 4 == 0]
        # 위 생성은 셀당 여러 점이 들어가도록 충분히 촘촘함
        result = sample_beat_grid(points, 800, 400)
        # 수평선이면 각 마디는 전체(16셀=4박)짜리 1개 음표로 병합됨
        assert len(result) == 4
        for note in result:
            assert not note.is_rest
            assert note.duration == pytest.approx(4.0)
            # 캔버스 중간 y=200이므로 약 7(파) 근처
            assert note.pitch == pitch_value_to_midi(7)

    def test_rest_cells_are_detected(self):
        """특정 X 범위에만 점이 있으면 나머지 셀은 쉼표가 됨"""
        # 캔버스 전반부에만 점 다수 배치
        points = [(x, 200) for x in range(0, 400) for _ in range(3)]
        result = sample_beat_grid(points, 800, 400)
        # 뒷부분에는 쉼표가 존재해야 함
        assert any(n.is_rest for n in result)
        assert any(not n.is_rest for n in result)

    def test_note_durations_multiple_of_16th(self):
        """생성된 음표/쉼표의 duration은 0.25박(16분음표)의 배수"""
        points = [(x, 100 + (x // 50) * 20) for x in range(800)
                  for _ in range(3)]
        result = sample_beat_grid(points, 800, 400)
        for note in result:
            # 0.25의 배수인지 (부동소수점 허용오차)
            cells = note.duration / 0.25
            assert abs(cells - round(cells)) < 1e-6
            assert note.duration > 0

    def test_total_duration_equals_canvas(self):
        """모든 음표/쉼표의 duration 합 = 총 박 수 (마디 수 * beats)"""
        points = [(x, 100 + (x // 50) * 20) for x in range(800)
                  for _ in range(3)]
        result = sample_beat_grid(points, 800, 400, num_measures=4,
                                    time_signature=(4, 4))
        total = sum(n.duration for n in result)
        assert total == pytest.approx(16.0)  # 4마디 × 4박

    def test_measure_indices_valid(self):
        """모든 음표의 measure는 0..num_measures-1 범위"""
        points = [(x, 200) for x in range(800) for _ in range(3)]
        result = sample_beat_grid(points, 800, 400, num_measures=4)
        for n in result:
            assert 0 <= n.measure < 4

    def test_notes_do_not_cross_measure_boundaries(self):
        """음표가 마디 경계를 넘지 않음 (start_beat + duration ≤ 4)"""
        points = [(x, 200) for x in range(800) for _ in range(3)]
        result = sample_beat_grid(points, 800, 400, num_measures=4,
                                    time_signature=(4, 4))
        for n in result:
            assert n.start_beat + n.duration <= 4.0 + 1e-6

    def test_consecutive_same_pitch_merged(self):
        """인접 셀이 같은 정수 음높이면 하나로 병합됨"""
        # 캔버스 절반은 y=100(높은음), 절반은 y=300(낮은음)
        # 각 셀마다 충분한 점 배치
        points = []
        for x in range(800):
            y = 100 if x < 400 else 300
            for _ in range(3):
                points.append((x, y))
        result = sample_beat_grid(points, 800, 400, num_measures=4)
        # 쉼표가 아닌 음표들의 pitch 정수값을 수집
        pitched = [n for n in result if not n.is_rest]
        # 같은 마디 안에서 같은 pitch가 연속되면 병합되어야 함
        # 마디 1,2: 높은 음 (전체 병합); 마디 3,4: 낮은 음 (전체 병합)
        # → 따라서 pitched가 정확히 4개 (마디별 1개)
        assert len(pitched) == 4

    def test_rest_threshold_configurable(self):
        """rest_threshold를 변경하면 판정이 달라짐"""
        # 각 셀에 정확히 3점만 들어가도록 구성 (셀 안의 서로 다른 x 3곳)
        cell_width = 800 / 64
        points = []
        for c in range(64):
            base = c * cell_width
            # 셀 안의 서로 다른 3개 x값 (중복 X 제거 규칙에 걸리지 않도록)
            for offset in (0.2, 0.5, 0.8):
                points.append((base + offset * cell_width, 200))
        # threshold=2면 3점은 쉼표가 아님
        r_default = sample_beat_grid(points, 800, 400)
        assert any(not n.is_rest for n in r_default)
        # threshold=3이면 3점도 쉼표 처리 → 모두 쉼표
        r_strict = sample_beat_grid(points, 800, 400, rest_threshold=3)
        assert all(n.is_rest for n in r_strict)

    def test_duplicate_x_in_cell_keeps_only_first(self):
        """한 셀 안에 같은 x값 점이 여러 개 있으면 가장 먼저 등장한 점만 인식."""
        # 첫 셀(x=0~~12.5) 안에 x=5를 5번 반복: 첫 번째는 y=50(높은음),
        # 이후 4개는 y=350(낮은음). 중복 X가 제거되면 y=50만 남아 쉼표 처리되어야 한다.
        # (rest_threshold=2 기본이므로 점 1개는 쉼표)
        points = [(5.0, 50.0)] + [(5.0, 350.0) for _ in range(4)]
        # 다른 셀에는 점을 많이 넣어 음표가 생기도록 함
        points += [(x + 0.5, 200.0) for x in range(100, 800) if x % 2 == 0]
        result = sample_beat_grid(points, 800, 400)
        # 첫 셀은 점 1개(중복 제거됨)로 쉼표 처리. 따라서 첫 음표/쉼표의 pitch는
        # 낮은음(y=350)의 평균값이 아니어야 한다 — 즉 평균 200 근처와 구분됨.
        # 구체적으로: 첫 음표/쉼표가 is_rest여야 함.
        assert result[0].is_rest

    def test_backward_c_shape_ignored_after_reversal(self):
        """좌→우로 그리다 방향을 바꿔 되돌아오는 점들은 무시되어야 함."""
        # 앞부분: x=0..400, y=100 (높은음) - 정상 진행
        forward = [(float(x), 100.0) for x in range(0, 401) for _ in range(3)]
        # 되돌아오는 부분: x=400..0, y=300 (낮은음) - 되돌아오는 X값이므로 무시되어야 함
        backward = [(float(x), 300.0) for x in range(400, -1, -1) for _ in range(3)]
        points = forward + backward
        result = sample_beat_grid(points, 800, 400, num_measures=4)
        # 앞부분(마디 1~2)에는 높은음(y=100 → 대략 pitch 10)이 있어야 하고
        # 낮은음(y=300 → 대략 pitch 4)은 없어야 한다.
        pitched = [n for n in result if not n.is_rest]
        assert len(pitched) > 0
        # 되돌아오는 y=300의 점이 평균에 섞였다면 pitch가 중간값(7 근처)으로 내려갈 것.
        # 실제로는 y=100만 사용되어 pitch_value_to_midi(10) == 69 근처여야 한다.
        high_pitch_midi = pitch_value_to_midi(10)
        assert any(n.pitch == high_pitch_midi for n in pitched), (
            f"되돌아오는 점이 잘못 포함되어 평균이 왜곡됨. pitches={[n.pitch for n in pitched]}"
        )


class TestBeatGridSummary:
    """beat_grid_summary 함수 테스트"""

    def test_empty(self):
        assert "생성되지 않았" in beat_grid_summary([])

    def test_contains_measure_label(self):
        points = [(x, 200) for x in range(800) for _ in range(3)]
        notes = sample_beat_grid(points, 800, 400)
        text = beat_grid_summary(notes)
        assert "마디 1" in text
        assert "마디 4" in text
