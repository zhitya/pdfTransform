# coding: utf-8

"""Utilities to render a JSON layout pattern as a PDF for preview.

This module interprets pattern JSON files describing blocks inside a page
section.  All coordinates and sizes are expected to be in **PDF points**. The
JSON may define one or more sections using the following structure::

    {
        "page_size": [595, 842],
        "sections": [
            {
                "section": 1,
                "image": {
                    "blockid": "logoimg",
                    "position": [8.5, 8.5],
                    "size": [113.39, 70.87]
                },
                "text_blocks": [
                    {
                        "blockid": "barcodeshort",
                        "position": [184.25, 64.23],
                        "size": [255.97, 13.74],
                        "lines": [
                            {"font": "Helvetica", "size_pt": 10, "text": "950240000"}
                        ]
                    }
                ]
            }
        ]
    }

If a single section is provided, it will be repeated three times on the page
so that the output shows three sections stacked vertically.  Each block is
drawn with a 1px black border and a light grey fill.
"""

from __future__ import annotations

import os
import json
import fitz  # PyMuPDF


def to_pt(value: float) -> float:
    """Return ``value`` unchanged as pattern coordinates are already in points."""
    return float(value)


def _draw_text_block(page: fitz.Page, block: dict, y_offset_pt: float, index: int) -> None:
    """Draw a text block defined in the pattern."""
    try:
        x_mm, y_mm = block.get("position", [0, 0])
        w_mm, h_mm = block.get("size", [10, 10])

        x = to_pt(float(x_mm))
        y = to_pt(float(y_mm)) + y_offset_pt
        w = to_pt(float(w_mm))
        h = to_pt(float(h_mm))

    except Exception:
        return

    rect = fitz.Rect(x, y, x + w, y + h)
    gray = 0.9 - (index % 5) * 0.1
    page.draw_rect(rect, color=(0, 0, 0), fill=(gray, gray, gray), width=1)

    lines = block.get("lines", [])
    if isinstance(lines, list) and lines:
        text = "\n".join(str(line.get("text", "")) for line in lines)
        font_size = lines[0].get("size_pt", 10)
        font_name = lines[0].get("font", "helv")
        page.insert_textbox(
            rect,
            text,
            fontsize=float(font_size),
            fontname=str(font_name),
            align=0,
        )


def _draw_image(page: fitz.Page, image: dict, y_offset_pt: float) -> None:
    """Draw an image placeholder or insert an image if a path is provided."""
    try:
        x_mm, y_mm = image.get("position", [0, 0])
        w_mm, h_mm = image.get("size", [10, 10])
        x = to_pt(float(x_mm))
        y = to_pt(float(y_mm)) + y_offset_pt
        w = to_pt(float(w_mm))
        h = to_pt(float(h_mm))

    except Exception:
        return

    rect = fitz.Rect(x, y, x + w, y + h)
    path = image.get("path")
    if path and os.path.isfile(path):
        page.insert_image(rect, filename=path)
    else:
        page.draw_rect(rect, color=(0, 0, 0), fill=(0.85, 0.85, 0.85), width=1)


def render_pattern_pdf(pattern_path: str, output_folder: str) -> str:
    """Create a PDF visualizing the sections defined in ``pattern_path``."""

    if not os.path.isfile(pattern_path):
        raise FileNotFoundError(pattern_path)

    with open(pattern_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)


    page_size = [595, 842]
    if isinstance(data, dict):
        size = None
        if isinstance(data.get("page_size"), list):
            size = data.get("page_size")
        elif isinstance(data.get("page_size_pt"), list):
            size = data.get("page_size_pt")
        elif isinstance(data.get("page_size_mm"), list):
            size = data.get("page_size_mm")
        if isinstance(size, list) and len(size) == 2 and all(isinstance(v, (int, float)) for v in size):

            page_size = size

    sections = []
    if isinstance(data, dict) and isinstance(data.get("sections"), list):
        sections = data["sections"]
    elif isinstance(data, list):
        sections = data
    else:
        sections = [data]

    os.makedirs(output_folder, exist_ok=True)
    doc = fitz.open()

    width_pt = to_pt(page_size[0])
    height_pt = to_pt(page_size[1])

    page = doc.new_page(width=width_pt, height=height_pt)

    section_height = height_pt / 3

    if len(sections) == 1 and sections[0].get("section") is None:
        # Only a single section definition without explicit section number -> repeat 3 times
        src = sections[0]
        for i in range(3):
            y_offset = section_height * i
            img = src.get("image")
            if isinstance(img, dict):
                _draw_image(page, img, y_offset)
            for idx, tb in enumerate(src.get("text_blocks", [])):
                _draw_text_block(page, tb, y_offset, idx)
    else:
        for sec in sections:
            sec_num = int(sec.get("section", 1))
            y_offset = section_height * (sec_num - 1)
            img = sec.get("image")
            if isinstance(img, dict):
                _draw_image(page, img, y_offset)
            for idx, tb in enumerate(sec.get("text_blocks", [])):
                _draw_text_block(page, tb, y_offset, idx)

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
