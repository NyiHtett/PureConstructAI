from __future__ import annotations

from app.schemas import AnnotationMode, AnnotationSpec


def build_mock_annotation_spec(annotation_mode: AnnotationMode) -> AnnotationSpec:
    if annotation_mode == AnnotationMode.electrical_lines:
        return AnnotationSpec.model_validate(
            {
                "annotation_mode": annotation_mode,
                "electrical_lines": [
                    {
                        "points": [
                            {"x": 0.14, "y": 0.62},
                            {"x": 0.30, "y": 0.49},
                            {"x": 0.50, "y": 0.45},
                            {"x": 0.70, "y": 0.49},
                            {"x": 0.86, "y": 0.62},
                        ],
                        "color": "red",
                        "thickness": 6,
                    }
                ],
                "outlet_boxes": [
                    {"center": {"x": 0.18, "y": 0.67}, "label": "O1"},
                    {"center": {"x": 0.38, "y": 0.59}, "label": "O2"},
                    {"center": {"x": 0.62, "y": 0.59}, "label": "O3"},
                    {"center": {"x": 0.82, "y": 0.67}, "label": "O4"},
                ],
                "labels": [{"anchor": {"x": 0.34, "y": 0.38}, "text": "PROPOSED CABLE ROUTE"}],
                "warning_badges": [
                    {"anchor": {"x": 0.30, "y": 0.09}, "text": "VERIFY BEFORE INSTALLATION"}
                ],
                "warnings": ["Field reference only. Verify before installation."],
            }
        )

    if annotation_mode == AnnotationMode.stud_locations:
        return AnnotationSpec.model_validate(
            {
                "annotation_mode": annotation_mode,
                "stud_centerlines": [
                    {
                        "top": {"x": 0.22, "y": 0.12},
                        "bottom": {"x": 0.22, "y": 0.84},
                        "label": "S1",
                    },
                    {
                        "top": {"x": 0.38, "y": 0.12},
                        "bottom": {"x": 0.38, "y": 0.84},
                        "label": "S2",
                    },
                    {
                        "top": {"x": 0.54, "y": 0.12},
                        "bottom": {"x": 0.54, "y": 0.84},
                        "label": "S3",
                    },
                    {
                        "top": {"x": 0.70, "y": 0.12},
                        "bottom": {"x": 0.70, "y": 0.84},
                        "label": "S4",
                    },
                ],
                "labels": [{"anchor": {"x": 0.18, "y": 0.08}, "text": "STUD CENTERLINES"}],
                "warnings": ["Stud markings are approximate until calibrated."],
            }
        )

    if annotation_mode == AnnotationMode.flooring_pattern:
        return AnnotationSpec.model_validate(
            {
                "annotation_mode": annotation_mode,
                "floor_layout_lines": [
                    {"points": [{"x": 0.08, "y": 0.78}, {"x": 0.92, "y": 0.72}]},
                    {"points": [{"x": 0.10, "y": 0.86}, {"x": 0.94, "y": 0.79}]},
                    {"points": [{"x": 0.12, "y": 0.94}, {"x": 0.96, "y": 0.86}]},
                    {"points": [{"x": 0.24, "y": 0.70}, {"x": 0.18, "y": 0.98}]},
                    {"points": [{"x": 0.46, "y": 0.69}, {"x": 0.44, "y": 0.98}]},
                    {"points": [{"x": 0.68, "y": 0.68}, {"x": 0.72, "y": 0.98}]},
                ],
                "labels": [{"anchor": {"x": 0.12, "y": 0.70}, "text": "FLOOR LAYOUT REFERENCE"}],
                "warnings": ["Confirm floor plane and material direction before layout."],
            }
        )

    return AnnotationSpec.model_validate(
        {
            "annotation_mode": annotation_mode,
            "arrows": [
                {
                    "start": {"x": 0.24, "y": 0.24},
                    "end": {"x": 0.36, "y": 0.42},
                    "label": "CHECK BLOCKING",
                },
                {
                    "start": {"x": 0.74, "y": 0.22},
                    "end": {"x": 0.64, "y": 0.48},
                    "label": "PHOTO DETAIL NEEDED",
                },
            ],
            "warning_badges": [
                {"anchor": {"x": 0.11, "y": 0.09}, "text": "FIELD NOTE"},
                {"anchor": {"x": 0.50, "y": 0.09}, "text": "DO NOT TREAT AS CODE COMPLIANCE"},
            ],
            "warnings": ["Field notes are for review and coordination only."],
        }
    )
