import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from io import BytesIO
from pypdf import PdfReader, PdfWriter

class PDFMergerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Merger")
        self.geometry("560x420")
        self.files = []  # list[Path]

        # Listbox
        frame = tk.Frame(self); frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.lb = tk.Listbox(frame, selectmode=tk.EXTENDED)
        self.lb.pack(side="left", fill="both", expand=True)
        sb = tk.Scrollbar(frame, command=self.lb.yview); sb.pack(side="right", fill="y")
        self.lb.config(yscrollcommand=sb.set)

        # Buttons
        btns = tk.Frame(self); btns.pack(fill="x", padx=10, pady=(0,10))
        tk.Button(btns, text="Add PDFs", command=self.add_files).pack(side="left", padx=3)
        tk.Button(btns, text="Remove", command=self.remove_selected).pack(side="left", padx=3)
        tk.Button(btns, text="Clear", command=self.clear_all).pack(side="left", padx=3)
        tk.Button(btns, text="Move ↑", command=lambda: self.move(-1)).pack(side="left", padx=3)
        tk.Button(btns, text="Move ↓", command=lambda: self.move(+1)).pack(side="left", padx=3)

        # Merge row
        merge_row = tk.Frame(self); merge_row.pack(fill="x", padx=10, pady=(0,10))
        tk.Label(merge_row, text="Output:").pack(side="left")
        self.out_name = tk.Entry(merge_row, width=30)
        self.out_name.insert(0, "merged.pdf")
        self.out_name.pack(side="left", padx=6)
        tk.Button(merge_row, text="Merge", command=self.merge).pack(side="right")

        self.status = tk.Label(self, anchor="w", fg="#666")
        self.status.pack(fill="x", padx=10, pady=(0,10))
        self.update_status()

    def update_status(self, text=None):
        if text is None:
            total_mb = sum(p.stat().st_size for p in self.files) / 1024 / 1024 if self.files else 0
            text = f"{len(self.files)} file(s) • {total_mb:.2f} MB"
        self.status.config(text=text)

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF files", "*.pdf")]
        )
        for p in paths:
            pp = Path(p)
            if pp.suffix.lower() == ".pdf":
                self.files.append(pp)
                self.lb.insert("end", pp.name)
        self.update_status()

    def remove_selected(self):
        sel = list(self.lb.curselection())
        if not sel: return
        for idx in reversed(sel):
            self.lb.delete(idx)
            del self.files[idx]
        self.update_status()

    def clear_all(self):
        self.lb.delete(0, "end")
        self.files.clear()
        self.update_status()

    def move(self, direction):
        sel = list(self.lb.curselection())
        if not sel: return
        # For stable move, process in order depending on direction
        indices = sel if direction < 0 else reversed(sel)
        for i in indices:
            j = i + direction
            if 0 <= j < self.lb.size():
                # swap in listbox
                txt_i = self.lb.get(i)
                txt_j = self.lb.get(j)
                self.lb.delete(j); self.lb.insert(j, txt_i)
                self.lb.delete(i); self.lb.insert(i, txt_j)
                # swap in files
                self.files[i], self.files[j] = self.files[j], self.files[i]
        # Reselect moved items
        self.lb.selection_clear(0, "end")
        for i in [k + direction for k in sel if 0 <= k + direction < self.lb.size()]:
            self.lb.selection_set(i)

    def merge(self):
        if not self.files:
            messagebox.showwarning("PDF Merger", "Add at least one PDF.")
            return
        default_name = self.out_name.get().strip() or "merged.pdf"
        out_path = filedialog.asksaveasfilename(
            title="Save merged PDF as",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF", "*.pdf")]
        )
        if not out_path: return

        writer = PdfWriter()
        skipped = []

        for p in self.files:
            try:
                # Read PDF into memory to avoid "seek of closed file" error
                with open(p, "rb") as f:
                    pdf_bytes = BytesIO(f.read())
                reader = PdfReader(pdf_bytes)
                if reader.is_encrypted:
                    # try blank password (common for lightly protected PDFs)
                    try:
                        reader.decrypt("")
                    except Exception:
                        skipped.append(p.name)
                        continue
                for page in reader.pages:
                    writer.add_page(page)
            except Exception:
                skipped.append(p.name)

        if len(writer.pages) == 0:
            messagebox.showerror("PDF Merger", "No pages were merged.\nEncrypted or invalid PDFs may be the cause.")
            return

        try:
            with open(out_path, "wb") as out_f:
                writer.write(out_f)
            if skipped:
                messagebox.showinfo("PDF Merger", f"Merged successfully, but skipped:\n\n" + "\n".join(skipped))
            else:
                messagebox.showinfo("PDF Merger", "Merged successfully!")
        except Exception as e:
            messagebox.showerror("PDF Merger", f"Failed to write output:\n{e}")

        self.update_status("Done.")

if __name__ == "__main__":
    app = PDFMergerApp()
    app.mainloop()
