from __future__ import annotations

from copy import deepcopy

from app.geometry import (
    floor_plane_grid_lines,
    interpolate_along_stud_centerline,
    nearest_stud_centerline,
    point_inside_wall_polygon,
)
from app.schemas import (
    AnnotationMode,
    AnnotationSpec,
    ElectricalLineItem,
    CalibrationPayload,
    LabelItem,
    NormalizedPoint,
    StudCenterlineItem,
    WarningBadgeItem,
)


def _clamp_point(point: NormalizedPoint) -> NormalizedPoint:
    return NormalizedPoint(x=min(max(point.x, 0.0), 1.0), y=min(max(point.y, 0.0), 1.0), label=point.label)


def _clamp_spec(spec: AnnotationSpec) -> AnnotationSpec:
    for line in spec.electrical_lines:
        line.points = [_clamp_point(point) for point in line.points]
    for box in spec.outlet_boxes:
        box.center = _clamp_point(box.center)
    for stud in spec.stud_centerlines:
        stud.top = _clamp_point(stud.top)
        stud.bottom = _clamp_point(stud.bottom)
    for line in spec.floor_layout_lines:
        line.points = [_clamp_point(point) for point in line.points]
    for label in spec.labels:
        label.anchor = _clamp_point(label.anchor)
    for badge in spec.warning_badges:
        badge.anchor = _clamp_point(badge.anchor)
    for arrow in spec.arrows:
        arrow.start = _clamp_point(arrow.start)
        arrow.end = _clamp_point(arrow.end)
    return spec


def _distance_squared(start: NormalizedPoint, end: NormalizedPoint) -> float:
    return ((start.x - end.x) ** 2) + ((start.y - end.y) ** 2)


def _nearest_point_on_segment(
    point: NormalizedPoint,
    start: NormalizedPoint,
    end: NormalizedPoint,
) -> NormalizedPoint:
    dx = end.x - start.x
    dy = end.y - start.y
    if dx == 0 and dy == 0:
        return NormalizedPoint(x=start.x, y=start.y, label=point.label)

    t = ((point.x - start.x) * dx + (point.y - start.y) * dy) / ((dx * dx) + (dy * dy))
    t = min(max(t, 0.0), 1.0)
    return NormalizedPoint(x=start.x + (t * dx), y=start.y + (t * dy), label=point.label)


def _constrain_point_to_wall(point: NormalizedPoint, wall_corners: list[NormalizedPoint]) -> NormalizedPoint:
    if len(wall_corners) < 3 or point_inside_wall_polygon(point, wall_corners):
        return point

    wall_edges = list(zip(wall_corners, wall_corners[1:] + wall_corners[:1]))
    return min(
        (_nearest_point_on_segment(point, start, end) for start, end in wall_edges),
        key=lambda candidate: _distance_squared(point, candidate),
    )


def _route_through_outlet_centers(spec: AnnotationSpec) -> None:
    if len(spec.outlet_boxes) < 2:
        return

    route_points = [box.center for box in sorted(spec.outlet_boxes, key=lambda box: box.center.x)]
    if spec.electrical_lines:
        spec.electrical_lines[0].points = route_points
    else:
        spec.electrical_lines.append(ElectricalLineItem(points=route_points))


def snap_annotation_spec(
    spec: AnnotationSpec,
    calibration: CalibrationPayload | None,
    annotation_mode: AnnotationMode,
) -> AnnotationSpec:
    snapped = deepcopy(spec)
    snapped.annotation_mode = annotation_mode

    if annotation_mode == AnnotationMode.electrical_lines:
        _snap_electrical(snapped, calibration)
    elif annotation_mode == AnnotationMode.stud_locations:
        _snap_studs(snapped, calibration)
    elif annotation_mode == AnnotationMode.flooring_pattern:
        _snap_flooring(snapped, calibration)
    elif annotation_mode == AnnotationMode.field_notes:
        _clamp_spec(snapped)

    return _clamp_spec(snapped)


def _snap_electrical(spec: AnnotationSpec, calibration: CalibrationPayload | None) -> None:
    if not calibration or len(calibration.wall_corners_norm) != 4:
        warning = "No wall corners provided; electrical route is approximate."
        if warning not in spec.warnings:
            spec.warnings.append(warning)
        spec.warning_badges.append(
            WarningBadgeItem(anchor=NormalizedPoint(x=0.08, y=0.91), text="WALL GEOMETRY NOT CALIBRATED")
        )
        _route_through_outlet_centers(spec)
        return

    for line in spec.electrical_lines:
        line.points = [_constrain_point_to_wall(point, calibration.wall_corners_norm) for point in line.points]

    for box in spec.outlet_boxes:
        nearest = nearest_stud_centerline(box.center, calibration.stud_centerlines_norm)
        if nearest:
            box.center = interpolate_along_stud_centerline(nearest, box.center.y)
        if not point_inside_wall_polygon(box.center, calibration.wall_corners_norm):
            box.center = _constrain_point_to_wall(box.center, calibration.wall_corners_norm)

    _route_through_outlet_centers(spec)


def _snap_studs(spec: AnnotationSpec, calibration: CalibrationPayload | None) -> None:
    if not calibration or not calibration.stud_centerlines_norm:
        warning = "No stud centerlines provided; stud locations are approximate."
        if warning not in spec.warnings:
            spec.warnings.append(warning)
        return

    spec.stud_centerlines = []
    for index, stud in enumerate(calibration.stud_centerlines_norm, start=1):
        spec.stud_centerlines.append(
            StudCenterlineItem(top=stud.top, bottom=stud.bottom, label=f"S{index}", color="green", thickness=3)
        )
    spec.labels.append(LabelItem(anchor=NormalizedPoint(x=0.08, y=0.08), text="CALIBRATED STUD CENTERLINES"))


def _snap_flooring(spec: AnnotationSpec, calibration: CalibrationPayload | None) -> None:
    corners = []
    if calibration and calibration.floor_plane_norm:
        corners = calibration.floor_plane_norm.corners
    if len(corners) != 4:
        warning = "No floor plane provided; flooring layout is approximate."
        if warning not in spec.warnings:
            spec.warnings.append(warning)
        spec.warning_badges.append(
            WarningBadgeItem(anchor=NormalizedPoint(x=0.08, y=0.90), text="FLOOR PLANE NOT CALIBRATED")
        )
        return

    spec.floor_layout_lines = floor_plane_grid_lines(corners)
    spec.labels.append(LabelItem(anchor=corners[0], text="CALIBRATED FLOOR LAYOUT"))
