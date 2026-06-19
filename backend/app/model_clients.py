from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Optional, Protocol

import cv2
import httpx

from app.mock_specs import build_mock_annotation_spec
from app.prompts import SYSTEM_PROMPT, build_user_prompt
from app.schemas import AnnotationMode, AnnotationSpec, CalibrationPayload, WarningBadgeItem, NormalizedPoint


class ModelClientError(Exception):
    pass


def load_local_env() -> None:
    for env_path in (Path(".env"), Path("backend/.env")):
        if not env_path.exists():
            continue
        for line in env_path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()


class ModelClient(Protocol):
    def generate_annotation_spec(
        self,
        image_path: str,
        annotation_mode: AnnotationMode,
        calibration: Optional[CalibrationPayload],
        notes: Optional[str],
    ) -> AnnotationSpec:
        ...


class MockModelClient:
    def generate_annotation_spec(
        self,
        image_path: str,
        annotation_mode: AnnotationMode,
        calibration: Optional[CalibrationPayload],
        notes: Optional[str],
    ) -> AnnotationSpec:
        spec = build_mock_annotation_spec(annotation_mode)
        if notes and "low confidence" in notes.lower():
            warning = "Low confidence model output; verify all markings in the field."
            spec.warnings.append(warning)
            spec.warning_badges.append(
                WarningBadgeItem(anchor=NormalizedPoint(x=0.08, y=0.82), text="LOW CONFIDENCE - VERIFY")
            )
        return spec


class OpenInferModelClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        url: str = "https://platform.openinfer.io/v1/responses",
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENINFER_API_KEY")
        self.model = model or os.getenv("OPENINFER_MODEL", "@oi/beta")
        self.url = url
        self.timeout = timeout

    def generate_annotation_spec(
        self,
        image_path: str,
        annotation_mode: AnnotationMode,
        calibration: Optional[CalibrationPayload],
        notes: Optional[str],
    ) -> AnnotationSpec:
        if not self.api_key or self.api_key == "replace-with-hackathon-key":
            raise ModelClientError("OPENINFER_API_KEY is not configured")

        image = cv2.imread(image_path)
        if image is None:
            raise ModelClientError(f"Could not read image for model request: {image_path}")
        height, width = image.shape[:2]

        request_body = {
            "model": self.model,
            "stream": True,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": build_user_prompt(annotation_mode, width, height, calibration, notes),
                        },
                        {"type": "input_image", "image_url": _image_data_url(image_path)},
                    ],
                },
            ],
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream(
                    "POST",
                    self.url,
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json=request_body,
                ) as response:
                    request_id = response.headers.get("x-request-id")
                    if response.status_code >= 400:
                        body = response.read().decode("utf-8", errors="replace")
                        raise ModelClientError(
                            f"OpenInfer request failed: status={response.status_code} request_id={request_id} body={body}"
                        )
                    output_text = _read_sse_text(response)
        except httpx.HTTPError as exc:
            raise ModelClientError(f"OpenInfer request failed: {exc}") from exc

        return parse_annotation_spec_json(output_text)


class OpenAIModelClient:
    def generate_annotation_spec(
        self,
        image_path: str,
        annotation_mode: AnnotationMode,
        calibration: Optional[CalibrationPayload],
        notes: Optional[str],
    ) -> AnnotationSpec:
        raise ModelClientError("OpenAIModelClient is a placeholder and is not implemented yet")


def get_model_client(provider: Optional[str] = None) -> ModelClient:
    selected = get_model_provider_name(provider)
    if selected == "mock":
        return MockModelClient()
    if selected in {"openinfer", "open_infer"}:
        return OpenInferModelClient()
    if selected == "openai":
        return OpenAIModelClient()
    raise ModelClientError(f"Unsupported MODEL_PROVIDER: {selected}")


def get_model_provider_name(provider: Optional[str] = None) -> str:
    return (provider or os.getenv("MODEL_PROVIDER", "mock")).lower()


def parse_annotation_spec_json(output_text: str) -> AnnotationSpec:
    trimmed = output_text.strip()
    json_start = trimmed.find("{")
    json_end = trimmed.rfind("}")
    if json_start == -1 or json_end == -1 or json_end < json_start:
        raise ModelClientError("Model did not return a JSON object")
    try:
        parsed = json.loads(trimmed[json_start : json_end + 1])
        parsed = _normalize_model_spec(parsed)
        return AnnotationSpec.model_validate(parsed)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ModelClientError(f"Model returned invalid AnnotationSpec JSON: {exc}") from exc


def _normalize_model_spec(parsed: object) -> object:
    if not isinstance(parsed, dict):
        return parsed

    if isinstance(parsed.get("items"), list):
        return _semantic_plan_to_annotation_spec(parsed)

    normalized = dict(parsed)
    normalized["stud_centerlines"] = [
        _normalize_stud_centerline(item) for item in normalized.get("stud_centerlines", [])
    ]
    normalized["floor_layout_lines"] = [
        _normalize_polyline_item(item) for item in normalized.get("floor_layout_lines", [])
    ]
    normalized["electrical_lines"] = [
        _normalize_polyline_item(item) for item in normalized.get("electrical_lines", [])
    ]
    normalized["outlet_boxes"] = [
        _normalize_outlet_box(item) for item in normalized.get("outlet_boxes", [])
    ]
    return normalized


def _semantic_plan_to_annotation_spec(parsed: dict) -> dict:
    normalized: dict = {
        "annotation_mode": parsed.get("annotation_mode", "electrical_lines"),
        "electrical_lines": [],
        "outlet_boxes": [],
        "stud_centerlines": [],
        "floor_layout_lines": [],
        "labels": [],
        "warning_badges": [],
        "arrows": [],
        "warnings": parsed.get("warnings", []),
    }
    for item in parsed.get("items", []):
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type == "electrical_line":
            normalized["electrical_lines"].append({"points": item.get("points", [])})
            if item.get("label"):
                points = item.get("points") or []
                anchor = points[len(points) // 2] if points else {"x": 0.15, "y": 0.15}
                normalized["labels"].append({"anchor": anchor, "text": item["label"]})
        elif item_type == "outlet_box":
            normalized["outlet_boxes"].append({"center": item.get("center"), "label": item.get("label")})
        elif item_type == "label":
            normalized["labels"].append({"anchor": item.get("anchor"), "text": item.get("text", "")})
        elif item_type == "warning_badge":
            normalized["warning_badges"].append({"anchor": item.get("anchor"), "text": item.get("text", "")})
        elif item_type == "arrow":
            normalized["arrows"].append(
                {"start": item.get("start"), "end": item.get("end"), "label": item.get("label")}
            )
        elif item_type == "area_highlight":
            normalized["floor_layout_lines"].append({"points": item.get("points", [])})
    return normalized


def _normalize_stud_centerline(item: object) -> object:
    if isinstance(item, list) and len(item) == 4:
        x1, y1, x2, y2 = item
        return {"top": {"x": x1, "y": y1}, "bottom": {"x": x2, "y": y2}}
    return item


def _normalize_polyline_item(item: object) -> object:
    if isinstance(item, list):
        if len(item) == 4 and all(isinstance(value, (int, float)) for value in item):
            x1, y1, x2, y2 = item
            return {"points": [{"x": x1, "y": y1}, {"x": x2, "y": y2}]}
        if all(isinstance(point, list) and len(point) >= 2 for point in item):
            return {"points": [{"x": point[0], "y": point[1]} for point in item]}
    return item


def _normalize_outlet_box(item: object) -> object:
    if isinstance(item, list) and len(item) >= 2:
        return {"center": {"x": item[0], "y": item[1]}}
    return item


def _image_data_url(image_path: str) -> str:
    suffix = Path(image_path).suffix.lower()
    media_type = "image/png" if suffix == ".png" else "image/jpeg"
    encoded = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def _read_sse_text(response: httpx.Response) -> str:
    text = ""
    buffer = ""
    for chunk in response.iter_text():
        buffer += chunk
        events = buffer.split("\n\n")
        buffer = events.pop() or ""
        for event in events:
            for line in event.splitlines():
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if not payload or payload == "[DONE]":
                    continue
                try:
                    parsed = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                if parsed.get("type") == "response.output_text.delta" and isinstance(parsed.get("delta"), str):
                    text += parsed["delta"]
                elif isinstance(parsed.get("delta"), str):
                    text += parsed["delta"]
    return text
