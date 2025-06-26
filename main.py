"""Main GUI application for analyzing PDF documents."""

import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import datetime
import json

import createPDFA6

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
        self.suffix = tk.StringVar()
        self.pattern_path = tk.StringVar()
        self.file_info = tk.StringVar()

        self._load_settings()

        self._build_widgets()

        # Save parameters whenever they change
        self.pdf_path.trace_add("write", lambda *_: self._save_settings())
        self.output_folder.trace_add("write", lambda *_: self._save_settings())
        self.suffix.trace_add("write", lambda *_: self._save_settings())
        self.pattern_path.trace_add("write", lambda *_: self._save_settings())
        self.show_file_info()

    SETTINGS_FILE = "last_params.json"

    def _load_settings(self) -> None:
        """Load saved parameters if available."""
        if os.path.isfile(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception:
                data = {}
            self.pdf_path.set(data.get("pdf_path", ""))
            self.output_folder.set(data.get("output_folder", ""))
            self.suffix.set(data.get("suffix", "_new"))
            self.pattern_path.set(data.get("pattern_path", ""))
        else:
            self.suffix.set("_new")
            self.pattern_path.set("")

    def _save_settings(self) -> None:
        """Persist current parameters to disk."""
        data = {
            "pdf_path": self.pdf_path.get(),
            "output_folder": self.output_folder.get(),
            "suffix": self.suffix.get(),
            "pattern_path": self.pattern_path.get(),

        }
        try:
            with open(self.SETTINGS_FILE, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
        except Exception:
            pass

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

        # Suffix field
        tk.Label(self.root, text="Suffix:").grid(row=2, column=0, sticky="w")
        tk.Entry(self.root, textvariable=self.suffix, width=20).grid(row=2, column=1, sticky="w")

        # Pattern JSON selection
        tk.Label(self.root, text="Pattern JSON:").grid(row=3, column=0, sticky="w")
        tk.Entry(self.root, textvariable=self.pattern_path, width=50).grid(row=3, column=1)
        tk.Button(self.root, text="Browse", command=self.browse_pattern).grid(row=3, column=2)

        # File info label
        tk.Label(self.root, textvariable=self.file_info, justify="left").grid(row=4, column=0, columnspan=3, sticky="w")

        # Progress bar widget
        self.progress = ttk.Progressbar(self.root, length=400)
        self.progress.grid(row=5, column=0, columnspan=3, pady=10)

        # Start analysis button
        tk.Button(self.root, text="Analyze", command=self.start_analysis).grid(row=6, column=0, columnspan=3)

        # Transform button
        tk.Button(self.root, text="Transform", command=self.start_transform).grid(row=7, column=0, columnspan=3)

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

    def browse_pattern(self) -> None:
        """Prompt the user to select a JSON pattern file."""
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            self.pattern_path.set(path)

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

    def start_transform(self) -> None:
        """Create a new PDF with the chosen suffix and logo."""
        pdf = self.pdf_path.get()
        output = self.output_folder.get()
        suffix = self.suffix.get() or "_new"
        if not pdf or not os.path.isfile(pdf):
            messagebox.showerror("Error", "Please select a PDF file.")
            return
        if not output:
            messagebox.showerror("Error", "Please select an output folder.")
            return

        pattern = self.pattern_path.get() or None
        try:
            result = createPDFA6.create_pdf(pdf, output, suffix, pattern_path=pattern)

            messagebox.showinfo("Done", f"Created PDF: {result}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

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
