"""Pillow overlay rendering and localized box labels."""

from __future__ import annotations

from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from ui.locale import Strings, is_known_activity
from utils.paths import default_overlay_font

FONT_HEIGHT_MAIN = 14
FONT_HEIGHT_DETAIL = 12
FONT_HEIGHT_PICKUP = 18

_font_cache: dict[int, ImageFont.FreeTypeFont] = {}


def _get_font(font_size: int) -> ImageFont.FreeTypeFont:
    if font_size not in _font_cache:
        font_path = default_overlay_font()
        if not font_path.is_file():
            raise FileNotFoundError(f"overlay font not found: {font_path}")
        _font_cache[font_size] = ImageFont.truetype(str(font_path), font_size)
    return _font_cache[font_size]


def _bgr_to_rgb(color: Tuple[int, int, int]) -> Tuple[int, int, int]:
    return (color[2], color[1], color[0])


def _draw_on_context(
    draw: ImageDraw.ImageDraw,
    text: str,
    org: Tuple[int, int],
    color: Tuple[int, int, int],
    font_height: int,
    thickness: int,
) -> None:
    if not text:
        return
    font = _get_font(font_height)
    x, y = org
    bbox = draw.textbbox((0, 0), text, font=font)
    text_height = bbox[3] - bbox[1]
    top_left = (x, y - text_height)
    fill = _bgr_to_rgb(color)
    stroke = max(1, thickness // 2) if thickness > 1 else 0
    draw.text(
        top_left,
        text,
        font=font,
        fill=fill,
        stroke_width=stroke,
        stroke_fill=fill,
    )


class FrameTextOverlay:
    """Batch multiple text draws with one BGR/RGB conversion per frame."""

    def __init__(self, frame: np.ndarray) -> None:
        self._frame = frame
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self._pil = Image.fromarray(img_rgb)
        self._draw = ImageDraw.Draw(self._pil)

    def draw(
        self,
        text: str,
        org: Tuple[int, int],
        color: Tuple[int, int, int],
        font_height: int = FONT_HEIGHT_MAIN,
        thickness: int = 2,
    ) -> None:
        _draw_on_context(self._draw, text, org, color, font_height, thickness)

    def apply(self) -> None:
        self._frame[:] = cv2.cvtColor(np.array(self._pil), cv2.COLOR_RGB2BGR)


def draw_text(
    frame: np.ndarray,
    text: str,
    org: Tuple[int, int],
    color: Tuple[int, int, int],
    font_height: int = FONT_HEIGHT_MAIN,
    thickness: int = 2,
) -> None:
    """Draw UTF-8 text on a BGR frame using the bundled Noto font."""
    overlay = FrameTextOverlay(frame)
    overlay.draw(text, org, color, font_height=font_height, thickness=thickness)
    overlay.apply()


class OverlayLabels:
    """Build localized strings for video box overlays."""

    def __init__(self, locale: str = "en") -> None:
        self.S = Strings(locale)

    def _translate_dynamic(self, text: str) -> str:
        if self.S.locale != "ko" or not text or not text.strip():
            return text
        from postprocessing.translate_tts import translate_cached

        try:
            translated, _ = translate_cached(text, target_lang="Korean")
            return translated
        except Exception:
            return text

    def _activity_text(self, activity: str) -> str:
        if not activity:
            return activity
        if is_known_activity(activity):
            return self.S.activity_label(activity)
        return self._translate_dynamic(activity)

    def person_label(self, track_id: int, description: str = "") -> str:
        if description:
            body = self._translate_dynamic(description)
        else:
            body = self.S.t("overlay.person", id=track_id)
        return f"#{track_id} {body}"[:80]

    def activity_line(self, activity: str) -> str:
        return self._activity_text(activity)[:70]

    def holding_line(self, items: List[Dict]) -> str:
        prefix = self.S.t("overlay.holding")
        parts = [
            f"{prefix}: {item['count']} x {self._translate_dynamic(item['name'])}"
            for item in items
        ]
        return ", ".join(parts)[:70]

    def pickup_line(self, items: List[Dict]) -> str:
        prefix = self.S.t("overlay.pickup")
        parts = [
            f"{item['count']} x {self._translate_dynamic(item['name'])}"
            for item in items
        ]
        return f"{prefix}: {', '.join(parts)}"[:80]
