"""
test_line_simplifier.py — 곡선 → 직선 변환 모듈 테스트
"""

import pytest
from core.line_simplifier import simplify_line, enforce_left_to_right


class TestSimplifyLine:
    """simplify_line 함수 테스트"""

    def test_empty_input(self):
        """빈 입력 처리"""
        assert simplify_line([], 5.0) == []

    def test_single_point(self):
        """점 하나만 입력"""
        result = simplify_line([(100, 200)], 5.0)
        assert result == [(100, 200)]

    def test_two_points(self):
        """점 두 개 입력 — 더 단순화할 수 없음"""
        points = [(0, 0), (100, 100)]
        result = simplify_line(points, 5.0)
        assert result == [(0, 0), (100, 100)]

    def test_straight_line(self):
        """이미 직선인 입력 — 시작점과 끝점만 남아야 함"""
        points = [(0, 0), (25, 25), (50, 50), (75, 75), (100, 100)]
        result = simplify_line(points, 1.0)
        assert len(result) == 2
        assert result[0] == (0, 0)
        assert result[-1] == (100, 100)

    def test_zigzag_line(self):
        """지그재그 곡선 — 꺾이는 점이 보존되어야 함"""
        points = [(0, 0), (50, 100), (100, 0), (150, 100), (200, 0)]
        result = simplify_line(points, 1.0)
        # 지그재그의 꺾이는 점들이 유지되어야 함
        assert len(result) >= 3

    def test_complex_curve(self):
        """복잡한 곡선 — epsilon이 클수록 더 단순화됨"""
        # 사인파와 유사한 곡선 생성
        import math
        points = [(x, 100 + 50 * math.sin(x / 20)) for x in range(0, 201, 5)]

        result_small_eps = simplify_line(points, 1.0)
        result_large_eps = simplify_line(points, 20.0)

        # 큰 epsilon일수록 더 적은 점으로 단순화
        assert len(result_large_eps) < len(result_small_eps)
        # 시작점과 끝점은 항상 보존
        assert result_small_eps[0] == points[0]
        assert result_small_eps[-1] == points[-1]

    def test_epsilon_zero(self):
        """epsilon=0이면 모든 점이 유지됨"""
        points = [(0, 0), (10, 5), (20, 0)]
        result = simplify_line(points, 0.0)
        assert len(result) == len(points)


class TestEnforceLeftToRight:
    """enforce_left_to_right 함수 테스트"""

    def test_empty_input(self):
        """빈 입력"""
        assert enforce_left_to_right([]) == []

    def test_already_increasing(self):
        """이미 X가 단조 증가하는 경우"""
        points = [(0, 10), (50, 20), (100, 30)]
        result = enforce_left_to_right(points)
        assert result == points

    def test_backward_movement(self):
        """X가 감소하는 포인트 처리 — 역방향 포인트가 제거됨"""
        points = [(0, 10), (50, 20), (30, 30), (80, 40)]
        result = enforce_left_to_right(points)
        # (30, 30)은 역방향이므로 제거되어야 함
        assert len(result) == 3
        assert result == [(0, 10), (50, 20), (80, 40)]

    def test_single_point(self):
        """포인트 하나"""
        result = enforce_left_to_right([(42, 99)])
        assert result == [(42, 99)]
