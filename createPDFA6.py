import os
import fitz  # PyMuPDF


def mm_to_pt(mm: float) -> float:
    """Convert millimeters to PDF points."""
    return mm * 72 / 25.4


def create_pdf(pdf_path: str, output_folder: str, suffix: str = "_new", logo_path: str = "logo.png") -> str:
    """Create a new PDF with a logo in the top-left corner.

    The PDF dimensions are fixed at 210x297 mm. The output file name is the
    base name of ``pdf_path`` with ``suffix`` appended.

    Args:
        pdf_path: Path to the input PDF. Only the name is used for the output.
        output_folder: Directory to place the new PDF.
        suffix: Suffix for the output PDF name.
        logo_path: Path to a PNG logo image.

    Returns:
        The full path to the generated PDF file.
    """

    os.makedirs(output_folder, exist_ok=True)

    # Calculate A4 page size in points
    width = mm_to_pt(210)
    height = mm_to_pt(297)

    doc = fitz.open()
    page = doc.new_page(width=width, height=height)

    if os.path.isfile(logo_path):
        pix = fitz.Pixmap(logo_path)
        rect = fitz.Rect(0, 0, pix.width, pix.height)
        page.insert_image(rect, filename=logo_path)

    output_name = f"{os.path.splitext(os.path.basename(pdf_path))[0]}{suffix}.pdf"
    output_path = os.path.join(output_folder, output_name)

    doc.save(output_path)
    doc.close()
    return output_path
