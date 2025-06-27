# coding: utf-8
"""Utilities to render a JSON layout pattern as a PDF for preview."""

from __future__ import annotations

import os
import json
import fitz  # PyMuPDF


def mm_to_pt(mm: float) -> float:
    """Convert millimeters to PDF points."""
    return mm * 72 / 25.4


def render_pattern_pdf(pattern_path: str, output_folder: str) -> str:
    """Create a PDF visualizing the blocks defined in ``pattern_path``.

    The JSON file must define ``page_size_mm`` as ``[width, height]`` and a
    ``blocks`` list. Each block entry should have ``blockid``, ``x_mm``,
    ``y_mm``, ``width_mm``, ``height_mm`` and optional ``lines`` (list of text
    strings). Blocks are drawn with a 1px black border and filled with varying
    gray shades.

    Args:
        pattern_path: Path to the JSON pattern file.
        output_folder: Directory where the PDF preview will be saved.

    Returns:
        The full path to the generated PDF file.
    """
    if not os.path.isfile(pattern_path):
        raise FileNotFoundError(pattern_path)

    with open(pattern_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    if not isinstance(data, dict):
        raise ValueError("Pattern file must contain a JSON object")

    page_size = data.get("page_size_mm", [210, 297])
    if (
        not isinstance(page_size, (list, tuple))
        or len(page_size) != 2
        or not all(isinstance(x, (int, float)) for x in page_size)
    ):
        page_size = [210, 297]

    blocks = data.get("blocks", [])
    if not isinstance(blocks, list):
        blocks = []

    os.makedirs(output_folder, exist_ok=True)
    doc = fitz.open()
    page = doc.new_page(width=mm_to_pt(page_size[0]), height=mm_to_pt(page_size[1]))

    for idx, block in enumerate(blocks):
        try:
            x = mm_to_pt(float(block.get("x_mm", 0)))
            y = mm_to_pt(float(block.get("y_mm", 0)))
            w = mm_to_pt(float(block.get("width_mm", 10)))
            h = mm_to_pt(float(block.get("height_mm", 10)))
        except Exception:
            continue
        rect = fitz.Rect(x, y, x + w, y + h)

        gray = 0.9 - (idx % 5) * 0.1
        page.draw_rect(rect, color=(0, 0, 0), fill=(gray, gray, gray), width=1)

        lines = block.get("lines", [])
        if isinstance(lines, list) and lines:
            text = "\n".join(str(t) for t in lines)
            page.insert_textbox(
                rect,
                text,
                fontsize=10,
                fontname="helv",
                align=0,
            )

    output_name = f"{os.path.splitext(os.path.basename(pattern_path))[0]}.pdf"
    output_path = os.path.join(output_folder, output_name)
    doc.save(output_path)
    doc.close()
    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: checkPattern.py PATTERN.json OUTPUT_DIR")
        sys.exit(1)

    print(render_pattern_pdf(sys.argv[1], sys.argv[2]))
