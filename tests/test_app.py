"""Tests for the app pipeline."""

import numpy as np
import pytest

from app import generate_music


class TestGenerateMusic:
    def _make_image_dict(self, img):
        return {"composite": img}

    def test_none_input(self):
        fig, wav, midi, status = generate_music(None, "기본 모드")
        assert fig is None
        assert "그림을 그려주세요" in status

    def test_blank_image(self):
        img = np.full((256, 512), 255, dtype=np.uint8)
        fig, wav, midi, status = generate_music(self._make_image_dict(img), "기본 모드")
        assert fig is None
        assert "2개 이상" in status

    def test_short_line_warning(self):
        img = np.full((256, 512), 255, dtype=np.uint8)
        img[128, 10:13] = 0  # only 3 pixels
        _, _, _, status = generate_music(self._make_image_dict(img), "기본 모드")
        assert "짧습니다" in status

    def test_valid_line(self):
        img = np.full((256, 512), 255, dtype=np.uint8)
        # Draw a zigzag line
        for x in range(0, 512, 1):
            y = int(128 + 50 * np.sin(x / 20.0))
            img[y, x] = 0
        fig, wav, midi, status = generate_music(self._make_image_dict(img), "기본 모드")
        assert fig is not None
        assert wav is not None
        assert midi is not None
        assert "생성되었습니다" in status

    def test_smoothing_mode(self):
        img = np.full((256, 512), 255, dtype=np.uint8)
        for x in range(0, 512, 1):
            y = int(128 + 50 * np.sin(x / 20.0))
            img[y, x] = 0
        fig, wav, midi, status = generate_music(
            self._make_image_dict(img), "스무딩 적용"
        )
        assert fig is not None
        assert "생성되었습니다" in status
