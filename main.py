"""Main GUI application for analyzing PDF documents."""

import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import datetime

import analyzePDF


def bytes_to_human(size):
    """Convert a byte value to a human readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


class PDFAnalyzerGUI:
    """Simple Tkinter GUI for choosing a PDF and analyzing it."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PDF Analyzer")

        # Tkinter variables for entries and labels
        self.pdf_path = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.file_info = tk.StringVar()

        self._build_widgets()

    def _build_widgets(self) -> None:
        """Construct all Tkinter widgets for the interface."""
        # Input PDF selection
        tk.Label(self.root, text="Input PDF:").grid(row=0, column=0, sticky="w")
        tk.Entry(self.root, textvariable=self.pdf_path, width=50).grid(row=0, column=1)
        tk.Button(self.root, text="Browse", command=self.browse_pdf).grid(row=0, column=2)

        # Output folder selection
        tk.Label(self.root, text="Output Folder:").grid(row=1, column=0, sticky="w")
        tk.Entry(self.root, textvariable=self.output_folder, width=50).grid(row=1, column=1)
        tk.Button(self.root, text="Select", command=self.browse_folder).grid(row=1, column=2)

        # File info label
        tk.Label(self.root, textvariable=self.file_info, justify="left").grid(row=2, column=0, columnspan=3, sticky="w")

        # Progress bar widget
        self.progress = ttk.Progressbar(self.root, length=400)
        self.progress.grid(row=3, column=0, columnspan=3, pady=10)

        # Start analysis button
        tk.Button(self.root, text="Analyze", command=self.start_analysis).grid(row=4, column=0, columnspan=3)

    def browse_pdf(self) -> None:
        """Prompt the user to select a PDF file."""
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.pdf_path.set(path)
            self.show_file_info()

    def browse_folder(self) -> None:
        """Prompt the user to select an output folder."""
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)

    def show_file_info(self) -> None:
        """Display path, size and creation time of the chosen PDF."""
        path = self.pdf_path.get()
        if path and os.path.isfile(path):
            stats = os.stat(path)
            size = bytes_to_human(stats.st_size)
            ctime = datetime.datetime.fromtimestamp(stats.st_ctime)
            info = f"Path: {path}\nSize: {size}\nCreated: {ctime}"
            self.file_info.set(info)
        else:
            self.file_info.set("")

    def start_analysis(self) -> None:
        """Launch PDF analysis in a background thread."""
        pdf = self.pdf_path.get()
        output = self.output_folder.get()
        if not pdf or not os.path.isfile(pdf):
            messagebox.showerror("Error", "Please select a PDF file.")
            return
        if not output:
            messagebox.showerror("Error", "Please select an output folder.")
            return

        # Reset progress bar and run analysis
        self.progress['value'] = 0
        thread = threading.Thread(target=self.run_analysis, args=(pdf, output))
        thread.start()

    def update_progress(self, value: int) -> None:
        """Update the progress bar based on percentage value."""
        self.progress['value'] = value
        self.root.update_idletasks()

    def run_analysis(self, pdf: str, output: str) -> None:
        """Invoke the analysis module and show a completion dialog."""
        try:
            result = analyzePDF.analyze_pdf(pdf, output, self.update_progress)
            messagebox.showinfo("Done", f"Analysis completed.\nResults: {result}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))


def main() -> None:
    """Entry point for running the GUI as a script."""
    root = tk.Tk()
    PDFAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
