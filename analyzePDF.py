import os
import datetime
import fitz  # PyMuPDF


def analyze_pdf(pdf_path, output_folder):

    """Analyze a PDF document and save page elements to a text file.

    Args:
        pdf_path (str): Path to the input PDF document.
        output_folder (str): Folder where the analysis result will be saved.

    Notes:
        Metadata written to the result file includes the PDF's resolution and
        page size in millimeters. Image blocks are recorded but no longer
        extracted or saved as separate files.
    """
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Open the document
    doc = fitz.open(pdf_path)
    total_pages = doc.page_count

    # Determine resolution and page size using the first page
    if total_pages:
        first_page = doc.load_page(0)
        pix = first_page.get_pixmap()
        xres = pix.xres
        yres = pix.yres
        rect = first_page.rect
        width_mm = rect.width * 25.4 / 72
        height_mm = rect.height * 25.4 / 72
    else:
        xres = yres = 0
        width_mm = height_mm = 0

    # Construct result file path
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    result_path = os.path.join(output_folder, f"{base_name}.txt")

    # Gather file information
    file_stats = os.stat(pdf_path)
    file_size = file_stats.st_size
    creation_time = datetime.datetime.fromtimestamp(file_stats.st_ctime)

    with open(result_path, "w", encoding="utf-8") as result_file:
        # Write metadata
        result_file.write(f"PDF Path: {pdf_path}\n")
        result_file.write(f"Size (bytes): {file_size}\n")
        result_file.write(f"Creation Time: {creation_time}\n")
        result_file.write(f"Resolution: {xres:.0f}x{yres:.0f} DPI\n")
        result_file.write(
            f"Page Size: {width_mm:.2f}mm x {height_mm:.2f}mm\n\n"
        )

        # Iterate over pages
        for page_index in range(total_pages):
            page = doc.load_page(page_index)
            result_file.write(f"=== Page {page_index + 1} ===\n")

            # Extract text and image blocks as simple elements
            page_dict = page.get_text("dict")
            blocks = page_dict.get("blocks", [])
            for block in blocks:
                block_type = block.get("type")
                if block_type == 0:  # text block
                    bbox = block.get("bbox")
                    result_file.write(f"TEXT BLOCK {bbox}\n")
                    # Extract font characteristics from spans
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            font = span.get("font")
                            size = span.get("size")
                            text = span.get("text", "").strip()
                            result_file.write(
                                f"  Font: {font}, Size: {size} -> {text}\n"
                            )
                elif block_type == 1:  # image
                    bbox = block.get("bbox")
                    result_file.write(f"IMAGE {bbox}\n")
            result_file.write("\n")

    return result_path
