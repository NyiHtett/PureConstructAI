from app.prompts import get_system_prompt
from app.schemas import AnnotationMode


def test_system_prompt_changes_by_annotation_mode() -> None:
    electrical = get_system_prompt(AnnotationMode.electrical_lines)
    studs = get_system_prompt(AnnotationMode.stud_locations)
    flooring = get_system_prompt(AnnotationMode.flooring_pattern)
    notes = get_system_prompt(AnnotationMode.field_notes)

    assert 'annotation_mode must be "electrical_lines"' in electrical
    assert 'annotation_mode must be "stud_locations"' in studs
    assert 'annotation_mode must be "flooring_pattern"' in flooring
    assert 'annotation_mode must be "field_notes"' in notes
    assert "Do not use an items array" not in electrical
    assert "stud_centerlines item" in studs
    assert "floor_layout_lines item" in flooring
    assert "field notes require human review" in notes
    assert '"electrical_lines": []' in electrical
    assert '"outlet_boxes": []' in electrical
    assert '"warning_badges": []' in electrical
