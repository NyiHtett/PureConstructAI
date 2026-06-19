from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from app.model_clients import MockModelClient, ModelClientError, get_model_client, parse_annotation_spec_json
from app.schemas import AnnotationMode


def _write_image(path: Path) -> None:
    image = np.full((300, 420, 3), (185, 180, 172), dtype=np.uint8)
    assert cv2.imwrite(str(path), image)


def test_mock_provider_works(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    image_path = tmp_path / "wall.jpg"
    _write_image(image_path)
    monkeypatch.setenv("MODEL_PROVIDER", "mock")

    client = get_model_client()
    spec = client.generate_annotation_spec(str(image_path), AnnotationMode.electrical_lines, None, None)

    assert isinstance(client, MockModelClient)
    assert spec.annotation_mode == AnnotationMode.electrical_lines
    assert spec.electrical_lines


def test_invalid_model_json_is_rejected() -> None:
    with pytest.raises(ModelClientError):
        parse_annotation_spec_json("not json")

    with pytest.raises(ModelClientError):
        parse_annotation_spec_json('{"annotation_mode": "electrical_lines", "outlet_boxes": "bad"}')


def test_model_coordinate_arrays_are_normalized() -> None:
    spec = parse_annotation_spec_json(
        """
        {
          "annotation_mode": "stud_locations",
          "stud_centerlines": [[0.08, 0.22, 0.08, 0.68]],
          "floor_layout_lines": [[0.08, 0.68, 0.92, 0.68]],
          "electrical_lines": [[[0.1, 0.4], [0.5, 0.4], [0.9, 0.5]]],
          "outlet_boxes": [[0.25, 0.62]]
        }
        """
    )

    assert spec.stud_centerlines[0].top.x == 0.08
    assert spec.floor_layout_lines[0].points[1].x == 0.92
    assert spec.electrical_lines[0].points[2].y == 0.5
    assert spec.outlet_boxes[0].center.x == 0.25


def test_items_based_semantic_plan_is_converted() -> None:
    spec = parse_annotation_spec_json(
        """
        {
          "version": "1.0",
          "annotation_mode": "electrical_lines",
          "image_width": 984,
          "image_height": 595,
          "items": [
            {
              "id": "route_1",
              "type": "electrical_line",
              "points": [{"x": 0.1, "y": 0.5}, {"x": 0.8, "y": 0.5}],
              "label": "PROPOSED CABLE ROUTE",
              "confidence": 0.8
            },
            {
              "id": "box_1",
              "type": "outlet_box",
              "center": {"x": 0.25, "y": 0.62},
              "label": "E-1",
              "confidence": 0.9
            },
            {
              "id": "warning_1",
              "type": "warning_badge",
              "anchor": {"x": 0.2, "y": 0.1},
              "text": "VERIFY BEFORE INSTALLATION",
              "confidence": 1.0
            }
          ],
          "warnings": ["Field markup only. Verify layout before installation. This is not code approval."]
        }
        """
    )

    assert spec.electrical_lines[0].points[1].x == 0.8
    assert spec.outlet_boxes[0].label == "E-1"
    assert spec.warning_badges[0].text == "VERIFY BEFORE INSTALLATION"
    assert spec.labels[0].text == "PROPOSED CABLE ROUTE"


def test_low_confidence_spec_has_warning_badge(tmp_path: Path) -> None:
    image_path = tmp_path / "wall.jpg"
    _write_image(image_path)

    spec = MockModelClient().generate_annotation_spec(
        str(image_path),
        AnnotationMode.field_notes,
        None,
        "low confidence: photo is blurry",
    )

    assert any("Low confidence" in warning for warning in spec.warnings)
    assert any("LOW CONFIDENCE" in badge.text for badge in spec.warning_badges)
