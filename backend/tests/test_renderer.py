from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from app.renderers.opencv_renderer import render_annotation
from app.schemas import AnnotationSpec


def _write_input_image(path: Path, width: int = 960, height: int = 640) -> None:
    image = np.full((height, width, 3), (188, 183, 174), dtype=np.uint8)
    cv2.rectangle(image, (70, 55), (890, 560), (202, 198, 189), -1)
    for x in range(130, 890, 115):
        cv2.line(image, (x, 70), (x, 545), (155, 150, 142), 2, cv2.LINE_AA)
    cv2.rectangle(image, (0, 560), (width - 1, height - 1), (120, 118, 112), -1)
    assert cv2.imwrite(str(path), image)


def test_renderer_creates_output_and_preserves_dimensions(tmp_path: Path) -> None:
    input_path = tmp_path / "wall.jpg"
    output_path = tmp_path / "rendered.jpg"
    _write_input_image(input_path)
    spec_data = json.loads(Path("backend/sample_data/sample_annotation_spec.json").read_text())

    result = render_annotation(str(input_path), spec_data, str(output_path))

    assert result == str(output_path)
    assert output_path.exists()
    input_image = cv2.imread(str(input_path))
    output_image = cv2.imread(str(output_path))
    assert output_image.shape == input_image.shape


def test_renderer_handles_each_supported_item_type(tmp_path: Path) -> None:
    input_path = tmp_path / "wall.jpg"
    output_path = tmp_path / "all_items.jpg"
    _write_input_image(input_path)
    spec = AnnotationSpec.model_validate(
        {
            "annotation_mode": "field_notes",
            "electrical_lines": [
                {
                    "points": [
                        {"x": 0.12, "y": 0.40},
                        {"x": 0.50, "y": 0.33},
                        {"x": 0.88, "y": 0.40},
                    ]
                }
            ],
            "outlet_boxes": [{"center": {"x": 0.25, "y": 0.62}, "label": "O1"}],
            "stud_centerlines": [
                {
                    "top": {"x": 0.40, "y": 0.15},
                    "bottom": {"x": 0.40, "y": 0.86},
                    "label": "S1",
                }
            ],
            "floor_layout_lines": [
                {
                    "points": [
                        {"x": 0.10, "y": 0.88},
                        {"x": 0.90, "y": 0.78},
                    ]
                }
            ],
            "labels": [{"anchor": {"x": 0.34, "y": 0.22}, "text": "TEST LABEL"}],
            "warning_badges": [
                {"anchor": {"x": 0.12, "y": 0.08}, "text": "VERIFY BEFORE INSTALLATION"}
            ],
        }
    )

    render_annotation(str(input_path), spec, str(output_path))

    assert output_path.exists()
    assert cv2.imread(str(output_path)) is not None
