from __future__ import annotations

from app.mock_specs import build_mock_annotation_spec
from app.schemas import AnnotationMode, CalibrationPayload
from app.snapper import snap_annotation_spec


def _calibration() -> CalibrationPayload:
    return CalibrationPayload.model_validate(
        {
            "image_width": 1000,
            "image_height": 700,
            "wall_corners_norm": [
                {"x": 0.10, "y": 0.10},
                {"x": 0.90, "y": 0.10},
                {"x": 0.90, "y": 0.86},
                {"x": 0.10, "y": 0.86},
            ],
            "stud_centerlines_norm": [
                {
                    "id": "stud-a",
                    "top": {"x": 0.24, "y": 0.12},
                    "bottom": {"x": 0.24, "y": 0.84},
                },
                {
                    "id": "stud-b",
                    "top": {"x": 0.48, "y": 0.12},
                    "bottom": {"x": 0.48, "y": 0.84},
                },
            ],
            "floor_plane_norm": {
                "corners": [
                    {"x": 0.12, "y": 0.68},
                    {"x": 0.88, "y": 0.68},
                    {"x": 0.96, "y": 0.96},
                    {"x": 0.04, "y": 0.96},
                ]
            },
        }
    )


def test_missing_calibration_does_not_crash() -> None:
    spec = build_mock_annotation_spec(AnnotationMode.electrical_lines)

    snapped = snap_annotation_spec(spec, None, AnnotationMode.electrical_lines)

    assert snapped.annotation_mode == AnnotationMode.electrical_lines
    assert snapped.warnings


def test_stud_centerlines_are_used_when_provided() -> None:
    spec = build_mock_annotation_spec(AnnotationMode.stud_locations)

    snapped = snap_annotation_spec(spec, _calibration(), AnnotationMode.stud_locations)

    assert len(snapped.stud_centerlines) == 2
    assert [stud.label for stud in snapped.stud_centerlines] == ["S1", "S2"]
    assert snapped.stud_centerlines[0].top.x == 0.24


def test_electrical_boxes_remain_inside_image_bounds() -> None:
    spec = build_mock_annotation_spec(AnnotationMode.electrical_lines)

    snapped = snap_annotation_spec(spec, _calibration(), AnnotationMode.electrical_lines)

    for box in snapped.outlet_boxes:
        assert 0.0 <= box.center.x <= 1.0
        assert 0.0 <= box.center.y <= 1.0


def test_flooring_mode_warns_when_floor_plane_missing() -> None:
    calibration = _calibration()
    calibration.floor_plane_norm = None
    spec = build_mock_annotation_spec(AnnotationMode.flooring_pattern)

    snapped = snap_annotation_spec(spec, calibration, AnnotationMode.flooring_pattern)

    assert any("No floor plane provided" in warning for warning in snapped.warnings)
