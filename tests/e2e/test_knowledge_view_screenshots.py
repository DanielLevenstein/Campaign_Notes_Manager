from pathlib import Path

import pytest
from PIL import Image, ImageChops


ROOT_DIR = Path(__file__).resolve().parents[2]
OLD_SCREENSHOT_DIR = ROOT_DIR / "tests" / "screenshots" / "knowledge_views"
NEW_SCREENSHOT_DIR = ROOT_DIR / "tests" / "fixtures" / "screenshots" / "knowledge_views"
SCREENSHOT_PAIRS = {
    "Characters_Graph_Party_View.png": "Characters_Graph_Party_View.png",
    "Characters_Graph_Single_Character.png": "Characters_Graph_Single_Character.png",
    "Places_Graph_File_View.png": "Places_Graph_Location_View.png",
    "Session_Notes_Graph_File_View.png": "Session_Notes_Graph_Location_View.png",
    "Session_Notes_Graph_Directory_File_View.png": "Session_Notes_Graph_Directory_File_View.png",
}
MAX_PIXEL_DIFF_RATIO = 0.35


@pytest.mark.parametrize(("old_name", "new_name"), sorted(SCREENSHOT_PAIRS.items()))
def test_new_knowledge_view_screenshots_have_no_large_visual_regressions(old_name: str, new_name: str):
    old_path = OLD_SCREENSHOT_DIR / old_name
    new_path = NEW_SCREENSHOT_DIR / new_name

    assert old_path.exists(), f"Missing old screenshot baseline: {old_path}"
    assert new_path.exists(), f"Missing new screenshot capture: {new_path}"
    with Image.open(old_path) as old_image, Image.open(new_path) as new_image:
        assert old_image.size == new_image.size
        diff_ratio = screenshot_pixel_diff_ratio(old_image.convert("RGB"), new_image.convert("RGB"))

    assert diff_ratio <= MAX_PIXEL_DIFF_RATIO, (
        f"{new_name} differs from {old_name} by {diff_ratio:.2%}; "
        f"review old={old_path} new={new_path}"
    )


def screenshot_pixel_diff_ratio(old_image: Image.Image, new_image: Image.Image) -> float:
    diff = ImageChops.difference(old_image, new_image)
    changed_pixels = sum(1 for pixel in diff.getdata() if pixel != (0, 0, 0))
    return changed_pixels / (old_image.width * old_image.height)
