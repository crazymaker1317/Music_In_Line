"""
test_extract_points.py — _extract_points_from_image 함수 테스트

특히 복잡한 그림(좌우 반전 C 모양 등)에서 점이 겹칠 때,
기존 획을 따라가는 연속성 기반 클러스터 선택이 정상 동작하는지 검증합니다.
"""

import numpy as np
from app import _extract_points_from_image


def _make_rgb_canvas(height=400, width=800):
    """흰 배경의 RGB 캔버스를 생성."""
    return np.full((height, width, 3), 255, dtype=np.uint8)


def test_empty_image_returns_empty():
    img = _make_rgb_canvas()
    assert _extract_points_from_image(img) == []


def test_horizontal_line_follows_y():
    """두께 있는 수평선 → 각 X에서 대략 중심 Y가 추출되어야 함."""
    img = _make_rgb_canvas()
    # y=200 주변 두께 5px (198..202) 검은색 수평선
    img[198:203, 100:700, :] = 0
    points = _extract_points_from_image(img)
    assert len(points) > 100
    for x, y in points:
        assert 100 <= x < 700
        # 단일 클러스터 평균 → 약 200
        assert 198 <= y <= 202


def test_reversed_c_shape_tracks_forward_stroke():
    """
    좌우 반전 C 모양: 위쪽 획(y=100)과 아래쪽 획(y=300)이 동일한 X 범위에서 겹침.
    단순 평균이면 중앙값(~200)이 나오지만, 연속성 기반 선택으로 위쪽 획을 따라야 함.
    """
    img = _make_rgb_canvas()
    # 위쪽 획: y=98..102, x=100..500 (왼쪽에서 오른쪽으로 그림)
    img[98:103, 100:501, :] = 0
    # 아래쪽 획: y=298..302, x=100..500 (되돌아오는 부분)
    img[298:303, 100:501, :] = 0
    # 오른쪽 끝(x=500 근처)에서 두 획이 수직선으로 이어짐 (커브 부분 생략)
    img[100:301, 498:503, :] = 0

    points = _extract_points_from_image(img)
    assert len(points) > 0

    # X 범위 [110, 480] 구간(좌우 끝의 연결부 제외)에서 Y는 위쪽 획(~100)
    # 이어야 하며, 평균값 ~200이면 안 된다.
    interior = [(x, y) for x, y in points if 110 <= x <= 480]
    assert len(interior) > 100
    for x, y in interior:
        # 위쪽 획을 따라가야 함 → y는 98..102 사이 (± 클러스터 평균 허용)
        assert y < 150, (
            f"x={x}에서 y={y}: 두 획의 중간값이 나왔다 — "
            f"연속성 기반 클러스터 선택이 동작하지 않음"
        )
