from __future__ import annotations

from copy import deepcopy

from app.geometry import (
    floor_plane_grid_lines,
    interpolate_along_stud_centerline,
    nearest_stud_centerline,
    point_inside_wall_polygon,
    wall_midline_path,
)
from app.schemas import (
    AnnotationMode,
    AnnotationSpec,
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
        return

    wall_path = wall_midline_path(calibration.wall_corners_norm)
    if spec.electrical_lines:
        spec.electrical_lines[0].points = wall_path

    for box in spec.outlet_boxes:
        nearest = nearest_stud_centerline(box.center, calibration.stud_centerlines_norm)
        if nearest:
            box.center = interpolate_along_stud_centerline(nearest, box.center.y)
        if not point_inside_wall_polygon(box.center, calibration.wall_corners_norm):
            box.center = NormalizedPoint(
                x=min(max(box.center.x, min(corner.x for corner in calibration.wall_corners_norm)), max(corner.x for corner in calibration.wall_corners_norm)),
                y=min(max(box.center.y, min(corner.y for corner in calibration.wall_corners_norm)), max(corner.y for corner in calibration.wall_corners_norm)),
            )


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
