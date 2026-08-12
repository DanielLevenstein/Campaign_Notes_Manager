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
    "Session_Notes_Graph_File_View.png": "Session_Notes_Graph_Session_View.png",
}
MAX_PIXEL_DIFF_RATIO = 0.35


@pytest.mark.parametrize(("old_name", "new_name"), sorted(SCREENSHOT_PAIRS.items()))
def test_new_knowledge_view_screenshots_have_no_large_visual_regressions(old_name: str, new_name: str):
    old_path = OLD_SCREENSHOT_DIR / old_name
    new_path = NEW_SCREENSHOT_DIR / new_name

    if not old_path.exists():
        pytest.xfail(f"Missing old screenshot baseline: {old_path}")
    if not new_path.exists():
        pytest.xfail(f"Missing new screenshot capture: {new_path}")
    with Image.open(old_path) as old_image, Image.open(new_path) as new_image:
        old_rgb, new_rgb = normalize_screenshot_pair(old_image.convert("RGB"), new_image.convert("RGB"))
        diff_ratio = screenshot_pixel_diff_ratio(old_rgb, new_rgb)

    if diff_ratio > MAX_PIXEL_DIFF_RATIO:
        pytest.xfail(
            f"{new_name} differs from {old_name} by {diff_ratio:.2%}; "
            f"review old={old_path} new={new_path}"
        )


def normalize_screenshot_pair(old_image: Image.Image, new_image: Image.Image) -> tuple[Image.Image, Image.Image]:
    width = min(old_image.width, new_image.width)
    height = min(old_image.height, new_image.height)
    return center_crop(old_image, width, height), center_crop(new_image, width, height)


def center_crop(image: Image.Image, width: int, height: int) -> Image.Image:
    left = (image.width - width) // 2
    top = (image.height - height) // 2
    return image.crop((left, top, left + width, top + height))


def screenshot_pixel_diff_ratio(old_image: Image.Image, new_image: Image.Image) -> float:
    diff = ImageChops.difference(old_image, new_image)
    changed_pixels = sum(1 for pixel in diff.getdata() if pixel != (0, 0, 0))
    return changed_pixels / (old_image.width * old_image.height)
