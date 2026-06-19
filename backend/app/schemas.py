from __future__ import annotations

from enum import Enum
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class NormalizedPoint(BaseModel):
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    label: Optional[str] = None


class AnnotationMode(str, Enum):
    electrical_lines = "electrical_lines"
    stud_locations = "stud_locations"
    flooring_pattern = "flooring_pattern"
    field_notes = "field_notes"


class JobStatus(str, Enum):
    draft = "draft"
    rendered = "rendered"
    approved_for_field_reference = "approved_for_field_reference"
    rejected = "rejected"
    needs_closer_photo = "needs_closer_photo"


class ReviewEventType(str, Enum):
    approved = "approved"
    rejected = "rejected"
    needs_closer_photo = "needs_closer_photo"


class ElectricalLineItem(BaseModel):
    points: List[NormalizedPoint] = Field(min_length=2)
    color: str = "red"
    thickness: int = Field(default=5, ge=1, le=40)


class OutletBoxItem(BaseModel):
    center: NormalizedPoint
    width: float = Field(default=0.055, gt=0.0, le=1.0)
    height: float = Field(default=0.075, gt=0.0, le=1.0)
    label: Optional[str] = None


class StudCenterlineItem(BaseModel):
    top: NormalizedPoint
    bottom: NormalizedPoint
    label: Optional[str] = None
    color: str = "green"
    thickness: int = Field(default=3, ge=1, le=20)


class FloorLayoutLineItem(BaseModel):
    points: List[NormalizedPoint] = Field(min_length=2)
    color: str = "cyan"
    thickness: int = Field(default=3, ge=1, le=20)


class LabelItem(BaseModel):
    anchor: NormalizedPoint
    text: str = Field(min_length=1, max_length=120)


class WarningBadgeItem(BaseModel):
    anchor: NormalizedPoint
    text: str = Field(min_length=1, max_length=160)


class ArrowItem(BaseModel):
    start: NormalizedPoint
    end: NormalizedPoint
    label: Optional[str] = None
    color: str = "yellow"
    thickness: int = Field(default=4, ge=1, le=20)


class AnnotationSpec(BaseModel):
    annotation_mode: AnnotationMode = AnnotationMode.electrical_lines
    electrical_lines: List[ElectricalLineItem] = Field(default_factory=list)
    outlet_boxes: List[OutletBoxItem] = Field(default_factory=list)
    stud_centerlines: List[StudCenterlineItem] = Field(default_factory=list)
    floor_layout_lines: List[FloorLayoutLineItem] = Field(default_factory=list)
    labels: List[LabelItem] = Field(default_factory=list)
    warning_badges: List[WarningBadgeItem] = Field(default_factory=list)
    arrows: List[ArrowItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    @field_validator("annotation_mode")
    @classmethod
    def annotation_mode_must_not_be_blank(cls, value: AnnotationMode) -> AnnotationMode:
        return value


class AnnotationResponse(BaseModel):
    job_id: str
    annotation_mode: AnnotationMode
    annotated_image_url: str
    spec: AnnotationSpec
    warnings: List[str] = Field(default_factory=list)


class StudCenterline(BaseModel):
    id: Optional[str] = None
    top: NormalizedPoint
    bottom: NormalizedPoint


class FloorPlane(BaseModel):
    corners: List[NormalizedPoint] = Field(default_factory=list, max_length=4)


class CalibrationPayload(BaseModel):
    image_width: Optional[int] = Field(default=None, gt=0)
    image_height: Optional[int] = Field(default=None, gt=0)
    wall_corners_norm: List[NormalizedPoint] = Field(default_factory=list, max_length=4)
    stud_centerlines_norm: List[StudCenterline] = Field(default_factory=list)
    floor_plane_norm: Optional[FloorPlane] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReviewRequest(BaseModel):
    event_type: ReviewEventType
    reviewer_id: str = "local-reviewer"
    notes: Optional[str] = None


class ReviewResponse(BaseModel):
    job_id: str
    status: JobStatus
    event_type: ReviewEventType


class ApprovedFieldReferenceSummary(BaseModel):
    id: str
    job_id: str
    annotation_mode: AnnotationMode
    project_id: Optional[str] = None
    wall_id: Optional[str] = None
    reviewer_id: Optional[str] = None
    notes: Optional[str] = None
    approved_at: str
    image_url: str
