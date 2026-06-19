from __future__ import annotations

from pathlib import Path
from typing import Mapping, Tuple

import cv2
import numpy as np

from app.schemas import (
    AnnotationSpec,
    ArrowItem,
    ElectricalLineItem,
    FloorLayoutLineItem,
    LabelItem,
    NormalizedPoint,
    OutletBoxItem,
    StudCenterlineItem,
    WarningBadgeItem,
)


Color = Tuple[int, int, int]

COLORS: Mapping[str, Color] = {
    "red": (35, 35, 235),
    "green": (50, 210, 80),
    "cyan": (230, 220, 40),
    "yellow": (40, 220, 245),
    "orange": (35, 150, 245),
    "white": (245, 245, 245),
    "black": (20, 20, 20),
}


def _color(name: str, fallback: Color) -> Color:
    return COLORS.get(name.lower(), fallback)


def norm_to_px(point: NormalizedPoint, width: int, height: int) -> tuple[int, int]:
    x = min(max(point.x, 0.0), 1.0)
    y = min(max(point.y, 0.0), 1.0)
    return round(x * (width - 1)), round(y * (height - 1))


def _polyline_points(points: list[NormalizedPoint], width: int, height: int) -> np.ndarray:
    return np.array([norm_to_px(point, width, height) for point in points], dtype=np.int32)


def _draw_text_with_background(
    image: np.ndarray,
    text: str,
    origin: tuple[int, int],
    background: Color,
    foreground: Color = COLORS["white"],
    scale: float = 0.62,
    thickness: int = 2,
) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size, baseline = cv2.getTextSize(text, font, scale, thickness)
    x, y = origin
    pad_x = 9
    pad_y = 7
    max_x = image.shape[1] - text_size[0] - (pad_x * 2) - 1
    max_y = image.shape[0] - baseline - pad_y - 1
    x = min(max(x, 0), max(max_x, 0))
    y = min(max(y, text_size[1] + pad_y), max(max_y, text_size[1] + pad_y))
    top_left = (x, y - text_size[1] - pad_y)
    bottom_right = (x + text_size[0] + (pad_x * 2), y + baseline + pad_y)
    cv2.rectangle(image, top_left, bottom_right, background, thickness=-1)
    cv2.rectangle(image, top_left, bottom_right, COLORS["black"], thickness=1)
    cv2.putText(image, text, (x + pad_x, y), font, scale, foreground, thickness, cv2.LINE_AA)


def draw_electrical_line(image: np.ndarray, item: ElectricalLineItem) -> None:
    height, width = image.shape[:2]
    points = _polyline_points(item.points, width, height)
    overlay = image.copy()
    cv2.polylines(
        overlay,
        [points],
        isClosed=False,
        color=_color(item.color, COLORS["red"]),
        thickness=item.thickness,
        lineType=cv2.LINE_AA,
    )
    cv2.addWeighted(overlay, 0.82, image, 0.18, 0.0, dst=image)
    for point in points:
        cv2.circle(image, tuple(point), max(4, item.thickness), _color(item.color, COLORS["red"]), -1, cv2.LINE_AA)


def draw_outlet_box(image: np.ndarray, item: OutletBoxItem) -> None:
    height, width = image.shape[:2]
    cx, cy = norm_to_px(item.center, width, height)
    half_w = max(5, round(item.width * width / 2))
    half_h = max(5, round(item.height * height / 2))
    top_left = (max(cx - half_w, 0), max(cy - half_h, 0))
    bottom_right = (min(cx + half_w, width - 1), min(cy + half_h, height - 1))
    overlay = image.copy()
    cv2.rectangle(overlay, top_left, bottom_right, (245, 245, 245), thickness=-1)
    cv2.addWeighted(overlay, 0.28, image, 0.72, 0.0, dst=image)
    cv2.rectangle(image, top_left, bottom_right, COLORS["red"], thickness=3, lineType=cv2.LINE_AA)
    cv2.circle(image, (cx, cy), max(4, min(half_w, half_h) // 4), COLORS["black"], -1, cv2.LINE_AA)
    if item.label:
        _draw_text_with_background(image, item.label, (top_left[0], top_left[1] - 8), COLORS["red"], scale=0.48)


def draw_stud_centerline(image: np.ndarray, item: StudCenterlineItem) -> None:
    height, width = image.shape[:2]
    top = norm_to_px(item.top, width, height)
    bottom = norm_to_px(item.bottom, width, height)
    color = _color(item.color, COLORS["green"])
    cv2.line(image, top, bottom, color, item.thickness, cv2.LINE_AA)
    cv2.circle(image, top, item.thickness + 3, color, -1, cv2.LINE_AA)
    cv2.circle(image, bottom, item.thickness + 3, color, -1, cv2.LINE_AA)
    if item.label:
        _draw_text_with_background(image, item.label, (top[0] + 8, top[1] + 22), color, scale=0.5)


def draw_floor_layout_line(image: np.ndarray, item: FloorLayoutLineItem) -> None:
    height, width = image.shape[:2]
    points = _polyline_points(item.points, width, height)
    overlay = image.copy()
    cv2.polylines(
        overlay,
        [points],
        isClosed=False,
        color=_color(item.color, COLORS["cyan"]),
        thickness=item.thickness,
        lineType=cv2.LINE_AA,
    )
    cv2.addWeighted(overlay, 0.72, image, 0.28, 0.0, dst=image)


def draw_label(image: np.ndarray, item: LabelItem) -> None:
    height, width = image.shape[:2]
    anchor = norm_to_px(item.anchor, width, height)
    _draw_text_with_background(image, item.text, anchor, COLORS["black"])


def draw_warning_badge(image: np.ndarray, item: WarningBadgeItem) -> None:
    height, width = image.shape[:2]
    anchor = norm_to_px(item.anchor, width, height)
    text = f"WARNING: {item.text}"
    _draw_text_with_background(image, text, anchor, COLORS["orange"], COLORS["black"], scale=0.58)


def draw_arrow(image: np.ndarray, item: ArrowItem) -> None:
    height, width = image.shape[:2]
    start = norm_to_px(item.start, width, height)
    end = norm_to_px(item.end, width, height)
    color = _color(item.color, COLORS["yellow"])
    cv2.arrowedLine(image, start, end, color, item.thickness, cv2.LINE_AA, tipLength=0.12)
    if item.label:
        _draw_text_with_background(image, item.label, (end[0] + 8, end[1] - 8), color, COLORS["black"], scale=0.5)


def render_annotation(input_image_path: str, spec: AnnotationSpec | dict, output_image_path: str) -> str:
    parsed_spec = spec if isinstance(spec, AnnotationSpec) else AnnotationSpec.model_validate(spec)
    image = cv2.imread(input_image_path, cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not read input image: {input_image_path}")

    for item in parsed_spec.floor_layout_lines:
        draw_floor_layout_line(image, item)
    for item in parsed_spec.stud_centerlines:
        draw_stud_centerline(image, item)
    for item in parsed_spec.electrical_lines:
        draw_electrical_line(image, item)
    for item in parsed_spec.outlet_boxes:
        draw_outlet_box(image, item)
    for item in parsed_spec.labels:
        draw_label(image, item)
    for item in parsed_spec.warning_badges:
        draw_warning_badge(image, item)
    for item in parsed_spec.arrows:
        draw_arrow(image, item)

    output_path = Path(output_image_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), image):
        raise OSError(f"Could not write rendered image: {output_image_path}")
    return str(output_path)
