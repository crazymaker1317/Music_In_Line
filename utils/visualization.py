"""
visualization.py — 선 변환 결과 시각화 모듈

원본 곡선과 단순화된 직선 데이터를 matplotlib으로 시각화합니다.
"""

import matplotlib
matplotlib.use('Agg')  # GUI 없는 환경에서도 동작하도록 백엔드 설정
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np


def plot_line_comparison(original_points, simplified_points,
                         canvas_width=800, canvas_height=400,
                         num_measures=4):
    """
    원본 곡선과 단순화된 직선을 겹쳐서 비교 시각화합니다.

    Args:
        original_points: 원본 좌표 리스트 [(x1, y1), ...]
        simplified_points: 단순화된 좌표 리스트 [(x1, y1), ...]
        canvas_width: 캔버스 가로 크기
        canvas_height: 캔버스 세로 크기
        num_measures: 마디 수 (가이드라인 표시용)

    Returns:
        matplotlib Figure 객체
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 5))

    # 원본 곡선 그리기
    if original_points:
        orig_x = [p[0] for p in original_points]
        orig_y = [p[1] for p in original_points]
        ax.plot(orig_x, orig_y, 'b-', alpha=0.3, linewidth=1,
                label='원본 곡선')

    # 단순화된 직선 그리기
    if simplified_points:
        simp_x = [p[0] for p in simplified_points]
        simp_y = [p[1] for p in simplified_points]
        ax.plot(simp_x, simp_y, 'r-o', linewidth=2, markersize=6,
                label='단순화된 직선')

    # 마디 구분선 그리기
    measure_width = canvas_width / num_measures
    for i in range(num_measures + 1):
        x = i * measure_width
        ax.axvline(x=x, color='gray', linestyle='--', alpha=0.5)
        if i < num_measures:
            ax.text(x + measure_width / 2, canvas_height * 0.02,
                    f'마디 {i + 1}', ha='center', fontsize=9, color='gray')

    # 축 설정
    ax.set_xlim(0, canvas_width)
    ax.set_ylim(0, canvas_height)
    ax.invert_yaxis()  # Y축 반전 (캔버스 좌표계: 위=0)
    ax.set_xlabel('시간 (X축)')
    ax.set_ylabel('음높이 (Y축) - 위: 높은 음, 아래: 낮은 음')
    ax.set_title('선 변환 결과')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.2)

    plt.tight_layout()
    return fig
