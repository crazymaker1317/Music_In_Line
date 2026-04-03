"""Unit tests for app.py coordinate extraction and UI callback."""

import numpy as np
import pytest

from app import extract_coordinates_from_image, generate_music


class TestExtractCoordinatesFromImage:
    def test_none_input(self):
        assert extract_coordinates_from_image(None) == []

    def test_blank_white_image(self):
        img = np.ones((256, 512, 3), dtype=np.uint8) * 255
        assert extract_coordinates_from_image(img) == []

    def test_single_pixel_drawn(self):
        img = np.ones((256, 512, 3), dtype=np.uint8) * 255
        img[100, 200, :] = 0  # draw a black pixel
        coords = extract_coordinates_from_image(img)
        assert len(coords) == 1
        assert coords[0] == pytest.approx((200.0, 100.0))

    def test_horizontal_line(self):
        img = np.ones((256, 512, 3), dtype=np.uint8) * 255
        img[128, 50:200, :] = 0  # horizontal line at y=128
        coords = extract_coordinates_from_image(img)
        assert len(coords) >= 2
        # All y-values should be ~128
        for _, y in coords:
            assert y == pytest.approx(128.0, abs=1)

    def test_rgba_image(self):
        img = np.zeros((256, 512, 4), dtype=np.uint8)  # transparent
        # Draw with alpha
        img[100, 200:210, 3] = 255  # opaque stroke
        img[100, 200:210, :3] = 0
        coords = extract_coordinates_from_image(img)
        assert len(coords) >= 1

    def test_subsampling(self):
        img = np.ones((256, 512, 3), dtype=np.uint8) * 255
        img[128, :, :] = 0  # Full horizontal line across the image
        coords = extract_coordinates_from_image(img)
        assert len(coords) <= 64  # subsampled


class TestGenerateMusic:
    def test_none_input(self):
        audio, midi, summary = generate_music(None, "Rule-based")
        assert audio is None
        assert midi is None
        assert "Drawing Error" in summary

    def test_blank_canvas(self):
        img = np.ones((256, 512, 3), dtype=np.uint8) * 255
        data = {"composite": img}
        audio, midi, summary = generate_music(data, "Rule-based")
        assert audio is None
        assert "Drawing Error" in summary

    def test_valid_drawing(self):
        img = np.ones((256, 512, 3), dtype=np.uint8) * 255
        # Draw a diagonal line
        for i in range(200):
            x = int(50 + i * 2)
            y = int(200 - i * 0.8)
            if 0 <= y < 256 and 0 <= x < 512:
                img[y, x, :] = 0
        data = {"composite": img}
        audio, midi, summary = generate_music(data, "Rule-based")
        assert audio is not None
        assert midi is not None
        assert "Note:" in summary

    def test_dict_with_ndarray_image(self):
        img = np.ones((256, 512, 3), dtype=np.uint8) * 255
        for i in range(100):
            img[128, 50 + i, :] = 0
        audio, midi, summary = generate_music(img, "Rule-based")
        assert audio is not None
