import os
import datetime
import fitz  # PyMuPDF


def analyze_pdf(pdf_path, output_folder, progress_callback=None):
    """Analyze a PDF document and save page elements to a text file.

    Args:
        pdf_path (str): Path to the input PDF document.
        output_folder (str): Folder where the analysis result will be saved.
        progress_callback (callable, optional): Function that accepts an int
            indicating progress percentage. Called after each page is processed.

    Notes:
        Images found in the PDF are extracted to the output folder with file
        names in the form ``<input>_page<page>_img<number>.<ext>`` where
        ``<ext>`` is the image type.
    """
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Open the document
    doc = fitz.open(pdf_path)
    total_pages = doc.page_count

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
        result_file.write(f"Creation Time: {creation_time}\n\n")

        # Iterate over pages
        for page_index in range(total_pages):
            page = doc.load_page(page_index)
            result_file.write(f"=== Page {page_index + 1} ===\n")

            # Extract text blocks and images as simple elements
            page_dict = page.get_text("dict")
            blocks = page_dict.get("blocks", [])

            # Counter for naming extracted images on this page
            image_number = 0
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
                    image_number += 1
                    bbox = block.get("bbox")
                    xref = block.get("xref")
                    if xref:
                        # Extract the image bytes and determine extension
                        img_info = doc.extract_image(xref)
                        ext = img_info.get("ext", "png")

                        # Build a filename that includes page and image numbers
                        img_name = (
                            f"{base_name}_page{page_index + 1}_img{image_number}.{ext}"
                        )
                        img_path = os.path.join(output_folder, img_name)

                        # Save image to disk
                        with open(img_path, "wb") as img_file:
                            img_file.write(img_info.get("image", b""))

                        result_file.write(f"IMAGE {bbox} -> {img_path}\n")
                    else:
                        result_file.write(f"IMAGE {bbox}\n")

            result_file.write("\n")

            # Update progress
            if progress_callback:
                progress = int((page_index + 1) * 100 / total_pages)
                progress_callback(progress)

    if progress_callback:
        progress_callback(100)

    return result_path
