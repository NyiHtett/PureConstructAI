from __future__ import annotations

import json
from typing import Optional

from app.schemas import AnnotationMode, CalibrationPayload


BASE_SYSTEM_PROMPT = """You are Field Annotation Planner, a construction-photo annotation assistant.

Your job is not to edit, regenerate, or photorealistically modify the image.
Your job is to return JSON that directly validates against the backend AnnotationSpec Pydantic model.

Return only one valid JSON object.
Do not return Markdown.
Do not wrap the JSON in code fences.
Do not return HTML, CSS, SVG, or prose outside the JSON.
Do not claim the image has been modified.
Do not certify code compliance.
Do not say the proposed work is approved.
Do not invent hidden conditions that are not visible.

Use normalized coordinates between 0 and 1.
Coordinate system: x=0 left, x=1 right, y=0 top, y=1 bottom.

The renderer controls all visual styling. Do not include style fields.
Do not include version, id, type, confidence, metadata, color, thickness, width, height, line_width, line_style, font_size, opacity, stroke, or fill.

Use exactly this top-level JSON shape for every annotation mode:
{
  "annotation_mode": "electrical_lines",
  "electrical_lines": [],
  "outlet_boxes": [],
  "stud_centerlines": [],
  "floor_layout_lines": [],
  "labels": [],
  "warning_badges": [],
  "arrows": [],
  "warnings": []
}

Allowed annotation_mode values:
- electrical_lines
- stud_locations
- flooring_pattern
- field_notes

Allowed object shapes:

electrical_lines item:
{
  "points": [
    { "x": number, "y": number }
  ]
}

outlet_boxes item:
{
  "center": { "x": number, "y": number },
  "label": string
}

stud_centerlines item:
{
  "top": { "x": number, "y": number },
  "bottom": { "x": number, "y": number },
  "label": string
}

floor_layout_lines item:
{
  "points": [
    { "x": number, "y": number }
  ]
}

labels item:
{
  "anchor": { "x": number, "y": number },
  "text": string
}

warning_badges item:
{
  "anchor": { "x": number, "y": number },
  "text": string
}

arrows item:
{
  "start": { "x": number, "y": number },
  "end": { "x": number, "y": number },
  "label": string
}

All arrays must be present. Use empty arrays when no items of that type are needed.
All point objects must include only x and y.
warnings must be an array of strings."""


ELECTRICAL_LINES_SYSTEM_PROMPT = BASE_SYSTEM_PROMPT + """

For this request, annotation_mode must be "electrical_lines".

Electrical rules:
- Use the visible framed wall area.
- Keep proposed cable routes and outlet boxes inside the visible work area.
- Place outlet_boxes first, then route electrical_lines through the outlet_box centers from left to right.
- Include one proposed cable route in electrical_lines that uses the same center coordinates as the outlet_boxes when outlet_boxes are present.
- Do not place the cable route on the wall midpoint unless the outlet_box centers are also on that midpoint.
- Include four outlet_boxes labeled E-1, E-2, E-3, and E-4 when reasonable.
- If calibration stud centerlines are provided, prefer outlet_box centers that align with those visible or calibrated stud centerlines.
- Include a label saying PROPOSED CABLE ROUTE.
- Include a warning_badge saying VERIFY BEFORE INSTALLATION.
- Include a warning saying this is field markup only and not code approval."""


STUD_LOCATIONS_SYSTEM_PROMPT = BASE_SYSTEM_PROMPT + """

For this request, annotation_mode must be "stud_locations".

Stud rules:
- Mark visible or calibration-provided stud centerlines in stud_centerlines.
- If calibration stud centerlines are provided, treat them as the primary spatial reference.
- Do not infer hidden studs unless there is strong visual evidence.
- Use labels such as S-1, S-2, S-3.
- Do not claim exact measurements unless measurement data is provided.
- Include a warning_badge if stud locations are estimated.
- Include a warning saying field markup must be verified before layout or installation work."""


FLOORING_PATTERN_SYSTEM_PROMPT = BASE_SYSTEM_PROMPT + """

For this request, annotation_mode must be "flooring_pattern".

Flooring rules:
- Show proposed flooring layout direction, starter line, or grid using floor_layout_lines.
- If floor plane corners are provided in calibration geometry, use them as the primary spatial reference.
- Keep layout lines inside the visible floor plane or provided floor plane geometry.
- Use labels such as STARTER LINE, FLOORING DIRECTION, VERIFY LAYOUT, or FIELD VERIFY.
- Do not claim exact dimensions unless measurement data is provided.
- Do not claim the layout is approved.
- Include a warning_badge if the floor plane is estimated.
- Include a warning saying field layout must be verified before installation."""


FIELD_NOTES_SYSTEM_PROMPT = BASE_SYSTEM_PROMPT + """

For this request, annotation_mode must be "field_notes".

Field note rules:
- Add worker-facing notes only where useful.
- Prefer short labels such as VERIFY, NEEDS REVIEW, TAKE CLOSE-UP PHOTO, HOLD POINT, CHECK ALIGNMENT, or FIELD VERIFY.
- Use arrows to point from labels to specific visible areas.
- Use floor_layout_lines only for area outlines if a region clearly needs attention.
- Do not invent defects that are not visible.
- Do not claim something failed inspection.
- Do not claim work is approved or code-compliant.
- If uncertainty is high, use NEEDS REVIEW or TAKE CLOSE-UP PHOTO instead of making a specific claim.
- Include a warning saying field notes require human review."""


SYSTEM_PROMPTS = {
    AnnotationMode.electrical_lines.value: ELECTRICAL_LINES_SYSTEM_PROMPT,
    AnnotationMode.stud_locations.value: STUD_LOCATIONS_SYSTEM_PROMPT,
    AnnotationMode.flooring_pattern.value: FLOORING_PATTERN_SYSTEM_PROMPT,
    AnnotationMode.field_notes.value: FIELD_NOTES_SYSTEM_PROMPT,
}


def get_system_prompt(annotation_mode: AnnotationMode) -> str:
    return SYSTEM_PROMPTS[annotation_mode.value]


def build_user_prompt(
    annotation_mode: AnnotationMode,
    image_width: int,
    image_height: int,
    calibration: Optional[CalibrationPayload],
    notes: Optional[str],
) -> str:
    calibration_json = json.dumps(calibration.model_dump(mode="json"), indent=2) if calibration else "null"
    return f"""Create a field-ready annotation plan for the attached construction photo.

Annotation mode:
{annotation_mode.value}

Image dimensions:
{image_width} x {image_height}

Task:
{_task_for_mode(annotation_mode)}

Return JSON that directly validates against AnnotationSpec.
Do not use an items array.
Do not include version, id, type, confidence, style, or metadata fields.

Additional notes:
{notes or ""}

Calibration geometry:
{calibration_json}

Return only one valid JSON object."""


def _task_for_mode(annotation_mode: AnnotationMode) -> str:
    if annotation_mode == AnnotationMode.electrical_lines:
        return "Show a proposed electrical rough-in layout on the visible framed wall."
    if annotation_mode == AnnotationMode.stud_locations:
        return "Mark visible or calibration-provided stud centerlines for field reference."
    if annotation_mode == AnnotationMode.flooring_pattern:
        return "Show a proposed flooring layout direction, starter line, or grid on the visible floor plane."
    return "Add concise field notes, hold points, arrows, and warnings for visible areas needing human review."
