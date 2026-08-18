"""T-NEW-117 regression tests for image palette extraction."""

from PIL import Image

from pyffice.images.palettes import PyfficeColorPalette


def test_extract_palette_counts_and_orders_exact_rgb_colors(tmp_path):
    image_path = tmp_path / "tiny-palette.png"
    image = Image.new("RGB", (2, 2))
    image.putdata(
        [
            (255, 0, 0),
            (255, 0, 0),
            (0, 0, 255),
            (0, 255, 0),
        ]
    )
    image.save(image_path)

    palette = PyfficeColorPalette.__new__(PyfficeColorPalette).extract_palette(image_path)

    assert palette == {
        "colors": [
            {"hex": "#ff0000", "count": 2, "percent": 50.0},
            {"hex": "#0000ff", "count": 1, "percent": 25.0},
            {"hex": "#00ff00", "count": 1, "percent": 25.0},
        ]
    }
