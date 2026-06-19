from __future__ import annotations

import json
import math
from typing import Optional

from pydantic import ValidationError

from app.schemas import CalibrationPayload, FloorLayoutLineItem, NormalizedPoint, StudCenterline


def parse_calibration_json(calibration_json: Optional[str]) -> Optional[CalibrationPayload]:
    if not calibration_json:
        return None
    try:
        data = json.loads(calibration_json)
        if not data:
            return None
        return CalibrationPayload.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"Invalid calibration_json: {exc}") from exc


def norm_to_px(point: NormalizedPoint, width: int, height: int) -> tuple[int, int]:
    return round(point.x * (width - 1)), round(point.y * (height - 1))


def px_to_norm(x: int, y: int, width: int, height: int) -> NormalizedPoint:
    return NormalizedPoint(
        x=min(max(x / max(width - 1, 1), 0.0), 1.0),
        y=min(max(y / max(height - 1, 1), 0.0), 1.0),
    )


def point_inside_wall_polygon(point: NormalizedPoint, wall_corners: list[NormalizedPoint]) -> bool:
    if len(wall_corners) < 3:
        return True
    inside = False
    j = len(wall_corners) - 1
    for i, corner in enumerate(wall_corners):
        previous = wall_corners[j]
        intersects = (corner.y > point.y) != (previous.y > point.y)
        if intersects:
            x_at_y = (previous.x - corner.x) * (point.y - corner.y) / (previous.y - corner.y) + corner.x
            if point.x < x_at_y:
                inside = not inside
        j = i
    return inside


def _distance_to_segment(point: NormalizedPoint, start: NormalizedPoint, end: NormalizedPoint) -> float:
    dx = end.x - start.x
    dy = end.y - start.y
    if dx == 0 and dy == 0:
        return math.hypot(point.x - start.x, point.y - start.y)
    t = ((point.x - start.x) * dx + (point.y - start.y) * dy) / (dx * dx + dy * dy)
    t = min(max(t, 0.0), 1.0)
    projected_x = start.x + t * dx
    projected_y = start.y + t * dy
    return math.hypot(point.x - projected_x, point.y - projected_y)


def interpolate_along_stud_centerline(stud: StudCenterline, y: float) -> NormalizedPoint:
    top = stud.top
    bottom = stud.bottom
    if bottom.y == top.y:
        return NormalizedPoint(x=top.x, y=min(max(y, 0.0), 1.0))
    t = (y - top.y) / (bottom.y - top.y)
    t = min(max(t, 0.0), 1.0)
    return NormalizedPoint(x=top.x + ((bottom.x - top.x) * t), y=top.y + ((bottom.y - top.y) * t))


def nearest_stud_centerline(point: NormalizedPoint, studs: list[StudCenterline]) -> Optional[StudCenterline]:
    if not studs:
        return None
    return min(studs, key=lambda stud: _distance_to_segment(point, stud.top, stud.bottom))


def wall_midline_path(wall_corners: list[NormalizedPoint]) -> list[NormalizedPoint]:
    if len(wall_corners) != 4:
        return [NormalizedPoint(x=0.15, y=0.52), NormalizedPoint(x=0.85, y=0.52)]
    top_left, top_right, bottom_right, bottom_left = wall_corners
    left_mid = NormalizedPoint(x=(top_left.x + bottom_left.x) / 2, y=(top_left.y + bottom_left.y) / 2)
    right_mid = NormalizedPoint(x=(top_right.x + bottom_right.x) / 2, y=(top_right.y + bottom_right.y) / 2)
    return [left_mid, right_mid]


def floor_plane_grid_lines(corners: list[NormalizedPoint], count: int = 6) -> list[FloorLayoutLineItem]:
    if len(corners) != 4:
        return []
    front_left, front_right, back_right, back_left = corners
    lines: list[FloorLayoutLineItem] = []
    for index in range(1, count):
        t = index / count
        left = NormalizedPoint(
            x=front_left.x + ((back_left.x - front_left.x) * t),
            y=front_left.y + ((back_left.y - front_left.y) * t),
        )
        right = NormalizedPoint(
            x=front_right.x + ((back_right.x - front_right.x) * t),
            y=front_right.y + ((back_right.y - front_right.y) * t),
        )
        lines.append(FloorLayoutLineItem(points=[left, right], color="cyan", thickness=3))
    for index in range(1, 4):
        t = index / 4
        front = NormalizedPoint(
            x=front_left.x + ((front_right.x - front_left.x) * t),
            y=front_left.y + ((front_right.y - front_left.y) * t),
        )
        back = NormalizedPoint(
            x=back_left.x + ((back_right.x - back_left.x) * t),
            y=back_left.y + ((back_right.y - back_left.y) * t),
        )
        lines.append(FloorLayoutLineItem(points=[front, back], color="cyan", thickness=3))
    return lines
