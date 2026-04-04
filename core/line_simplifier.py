"""
line_simplifier.py — 곡선 → 직선 변환 모듈

Ramer-Douglas-Peucker(RDP) 알고리즘을 사용하여
사용자가 그린 원시 곡선 좌표를 단순화된 직선 세그먼트로 변환합니다.
"""

import math


def _perpendicular_distance(point: tuple[float, float],
                            line_start: tuple[float, float],
                            line_end: tuple[float, float]) -> float:
    """
    한 점에서 직선(line_start → line_end)까지의 수직 거리를 계산합니다.

    Args:
        point: 거리를 측정할 점 (x, y)
        line_start: 직선의 시작점 (x, y)
        line_end: 직선의 끝점 (x, y)

    Returns:
        수직 거리 (float)
    """
    x0, y0 = point
    x1, y1 = line_start
    x2, y2 = line_end

    # 시작점과 끝점이 동일한 경우 → 점까지의 유클리드 거리
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x0 - x1, y0 - y1)

    # 수직 거리 공식: |cross product| / |line length|
    numerator = abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1)
    denominator = math.hypot(dx, dy)
    return numerator / denominator


def simplify_line(points: list[tuple[float, float]],
                  epsilon: float) -> list[tuple[float, float]]:
    """
    Ramer-Douglas-Peucker 알고리즘으로 곡선 좌표를 단순화합니다.

    Args:
        points: 원시 좌표 리스트 [(x1, y1), (x2, y2), ...]
                X는 단조 증가해야 합니다.
        epsilon: 단순화 허용 오차 (클수록 더 단순화됨)

    Returns:
        단순화된 핵심 포인트 좌표 리스트
    """
    # 점이 2개 이하이면 더 단순화할 수 없음
    if len(points) <= 2:
        return list(points)

    # 모든 점에서 첫 점-끝 점 직선까지의 최대 수직 거리를 찾음
    max_distance = 0.0
    max_index = 0
    start = points[0]
    end = points[-1]

    for i in range(1, len(points) - 1):
        distance = _perpendicular_distance(points[i], start, end)
        if distance > max_distance:
            max_distance = distance
            max_index = i

    # 최대 거리가 epsilon보다 크면 재귀적으로 분할
    if max_distance > epsilon:
        # 왼쪽 부분과 오른쪽 부분을 각각 단순화
        left = simplify_line(points[:max_index + 1], epsilon)
        right = simplify_line(points[max_index:], epsilon)
        # 중복되는 분할점을 제거하고 합침
        return left[:-1] + right
    else:
        # 중간 점들이 모두 허용 오차 이내 → 시작점과 끝점만 유지
        return [start, end]


def enforce_left_to_right(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """
    좌표 리스트에서 X좌표가 단조 증가하도록 필터링합니다.
    X가 이전 포인트보다 작거나 같은 입력은 제거합니다.

    Args:
        points: 원시 좌표 리스트

    Returns:
        X좌표가 단조 증가하는 좌표 리스트
    """
    if not points:
        return []

    result = [points[0]]
    for i in range(1, len(points)):
        x, y = points[i]
        prev_x = result[-1][0]
        if x > prev_x:
            result.append((x, y))
        # X가 감소하거나 같으면 해당 포인트를 무시 (역방향 제거)

    return result
