import os

import json
import tempfile
import fitz  # PyMuPDF
import barcode
from barcode.writer import ImageWriter
import segno


def mm_to_pt(mm: float) -> float:
    """Convert millimeters to PDF points."""
    return mm * 72 / 25.4

def _code128_image(data: str) -> str:
    """Create a Code128 barcode image and return its file path."""
    code = barcode.get("code128", data, writer=ImageWriter())
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    code.write(temp)
    temp.close()
    return temp.name


def _datamatrix_image(data: str) -> str:
    """Create a DataMatrix barcode image and return its file path."""
    dm = segno.helpers.make_data_matrix(data)
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    dm.save(temp.name, scale=3)
    return temp.name


from typing import Optional


def create_pdf(
    pdf_path: str,
    output_folder: str,
    suffix: str = "_new",
    logo_path: str = "logo.png",
    pattern_path: Optional[str] = None,
) -> str:
    """Create a new PDF with optional logo and codes defined by a JSON pattern.

    The PDF dimensions default to 210x297 mm (A4). The output file name is the
    base name of ``pdf_path`` with ``suffix`` appended. If ``pattern_path`` is
    supplied, it should point to a JSON file containing layout information. The
    JSON may contain the fields ``page_size_mm`` (``[width, height]``),
    ``logoimg`` (with keys ``path``, ``x_mm``, ``y_mm``, ``width_mm`` and
    ``height_mm``), ``barcodes`` (list of objects with ``data``, ``x_mm``,
    ``y_mm``), and ``qrcodes`` (list of objects with ``data``, ``x_mm``,
    ``y_mm``). Barcodes are generated in Code128 format and qrcodes in
    DataMatrix format.

    Args:
        pdf_path: Path to the input PDF. Only the name is used for the output.
        output_folder: Directory to place the new PDF.
        suffix: Suffix for the output PDF name.
        logo_path: Default path to a logo image.
        pattern_path: Optional JSON pattern describing items to place.

    Returns:
        The full path to the generated PDF file.
    """

    os.makedirs(output_folder, exist_ok=True)

    pattern = {}
    if pattern_path and os.path.isfile(pattern_path):
        try:
            with open(pattern_path, "r", encoding="utf-8") as fh:
                pattern = json.load(fh)
        except Exception:
            pattern = {}

    # Determine page size
    page_width_mm, page_height_mm = 210, 297
    if isinstance(pattern.get("page_size_mm"), list) and len(pattern["page_size_mm"]) == 2:
        page_width_mm, page_height_mm = pattern["page_size_mm"]

    width = mm_to_pt(page_width_mm)
    height = mm_to_pt(page_height_mm)

    doc = fitz.open()
    page = doc.new_page(width=width, height=height)

    # Logo placement
    logo = pattern.get("logoimg", {})
    logo_file = logo.get("path", logo_path)
    if os.path.isfile(logo_file):
        pix = fitz.Pixmap(logo_file)
        w = mm_to_pt(logo.get("width_mm", pix.width))
        h = mm_to_pt(logo.get("height_mm", pix.height))
        x = mm_to_pt(logo.get("x_mm", 0))
        y = mm_to_pt(logo.get("y_mm", 0))
        rect = fitz.Rect(x, y, x + w, y + h)
        page.insert_image(rect, filename=logo_file)

    # Insert barcodes
    for bc in pattern.get("barcodes", []):
        data = str(bc.get("data", ""))
        if not data:
            continue
        img_path = _code128_image(data)
        try:
            w = mm_to_pt(bc.get("width_mm", 40))
            h = mm_to_pt(bc.get("height_mm", 20))
            x = mm_to_pt(bc.get("x_mm", 0))
            y = mm_to_pt(bc.get("y_mm", 0))
            rect = fitz.Rect(x, y, x + w, y + h)
            page.insert_image(rect, filename=img_path)
        finally:
            os.unlink(img_path)

    # Insert QR/DataMatrix codes
    for qr in pattern.get("qrcodes", []):
        data = str(qr.get("data", ""))
        if not data:
            continue
        img_path = _datamatrix_image(data)
        try:
            size = mm_to_pt(qr.get("size_mm", 30))
            x = mm_to_pt(qr.get("x_mm", 0))
            y = mm_to_pt(qr.get("y_mm", 0))
            rect = fitz.Rect(x, y, x + size, y + size)
            page.insert_image(rect, filename=img_path)
        finally:
            os.unlink(img_path)

    output_name = f"{os.path.splitext(os.path.basename(pdf_path))[0]}{suffix}.pdf"
    output_path = os.path.join(output_folder, output_name)

    doc.save(output_path)
    doc.close()
    return output_path
