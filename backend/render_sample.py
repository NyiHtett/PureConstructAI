from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.renderers.opencv_renderer import render_annotation
from app.schemas import AnnotationSpec


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a construction annotation sample.")
    parser.add_argument("--image", required=True, help="Input JPG path.")
    parser.add_argument("--spec", required=True, help="Annotation spec JSON path.")
    parser.add_argument("--out", required=True, help="Output JPG path.")
    args = parser.parse_args()

    spec_data = json.loads(Path(args.spec).read_text())
    spec = AnnotationSpec.model_validate(spec_data)
    output_path = render_annotation(args.image, spec, args.out)
    print(output_path)


if __name__ == "__main__":
    main()
