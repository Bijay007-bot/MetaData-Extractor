import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import datetime

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

BG_DARK    = "#0d1117"
BG_PANEL   = "#161b22"
BG_CARD    = "#1c2128"
ACCENT     = "#58a6ff"
ACCENT2    = "#3fb950"
WARNING    = "#f0883e"
DANGER     = "#ff7b72"
TEXT_PRI   = "#e6edf3"
TEXT_SEC   = "#8b949e"
BORDER     = "#30363d"
HEADER_BG  = "#21262d"

FONT_MONO  = ("Courier New", 10)
FONT_BODY  = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_SUB   = ("Segoe UI", 9)
FONT_TAG   = ("Segoe UI", 9, "bold")

def _convert_to_degrees(value):
    try:
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)
    except Exception:
        return None


def extract_gps(gps_info: dict):
    try:
        lat_raw  = gps_info.get(2)
        lat_ref  = gps_info.get(1, "N")
        lon_raw  = gps_info.get(4)
        lon_ref  = gps_info.get(3, "E")
        if lat_raw and lon_raw:
            lat = _convert_to_degrees(lat_raw)
            lon = _convert_to_degrees(lon_raw)
            if lat_ref != "N":
                lat = -lat
            if lon_ref != "E":
                lon = -lon
            return lat, lon
    except Exception:
        pass
    return None, None


SENSITIVE_KEYS = {
    "gpslatitude", "gpslongitude", "gpsinfo",
    "author", "creator", "producer", "make", "model",
    "software", "datetime", "datetimeoriginal", "datetimedigitized",
    "serialnumber", "lensmake", "lensmodel",
}

def classify(key: str) -> str:
    k = key.lower().replace(" ", "")
    if any(s in k for s in ["gps", "location", "author", "serial"]):
        return "sensitive"
    if any(s in k for s in ["date", "time", "software", "make", "model", "creator", "producer"]):
        return "warning"
    return "normal"


def extract_image_metadata(path: str) -> list[dict]:
    if not PIL_AVAILABLE:
        return [{"key": "Error", "value": "Pillow not installed. Run: pip install Pillow", "category": "sensitive"}]

    rows = []
    try:
        img = Image.open(path)

        rows.append({"key": "File Name",  "value": os.path.basename(path),               "category": "normal"})
        rows.append({"key": "File Size",  "value": f"{os.path.getsize(path):,} bytes",    "category": "normal"})
        rows.append({"key": "Format",     "value": img.format or "Unknown",               "category": "normal"})
        rows.append({"key": "Mode",       "value": img.mode,                              "category": "normal"})
        rows.append({"key": "Dimensions", "value": f"{img.width} × {img.height} px",      "category": "normal"})

        exif_data = img._getexif() if hasattr(img, "_getexif") else None
        if exif_data:
            gps_info = {}
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, str(tag_id))
                if tag == "GPSInfo":
                    for gps_id, gps_val in value.items():
                        gps_tag = GPSTAGS.get(gps_id, str(gps_id))
                        gps_info[gps_id] = gps_val
                        rows.append({"key": f"GPS · {gps_tag}", "value": str(gps_val), "category": "sensitive"})
                elif isinstance(value, bytes):
                    rows.append({"key": tag, "value": f"<binary {len(value)} bytes>", "category": "normal"})
                else:
                    rows.append({"key": tag, "value": str(value), "category": classify(tag)})

            lat, lon = extract_gps(gps_info)
            if lat is not None:
                rows.append({"key": "📍 GPS Decimal", "value": f"{lat:.6f}, {lon:.6f}", "category": "sensitive"})
                rows.append({"key": "🗺  Maps Link",   "value": f"https://maps.google.com/?q={lat},{lon}", "category": "sensitive"})
        else:
            rows.append({"key": "EXIF Data", "value": "No EXIF metadata found in this image.", "category": "normal"})

    except Exception as e:
        rows.append({"key": "Error", "value": str(e), "category": "sensitive"})

    return rows


def extract_pdf_metadata(path: str) -> list[dict]:
    if not PDF_AVAILABLE:
        return [{"key": "Error", "value": "PyPDF2 not installed. Run: pip install PyPDF2", "category": "sensitive"}]

    rows = []
    try:
        rows.append({"key": "File Name", "value": os.path.basename(path),            "category": "normal"})
        rows.append({"key": "File Size", "value": f"{os.path.getsize(path):,} bytes", "category": "normal"})

        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            rows.append({"key": "Pages",     "value": str(len(reader.pages)), "category": "normal"})
            rows.append({"key": "Encrypted", "value": str(reader.is_encrypted), "category": "warning"})

            meta = reader.metadata
            if meta:
                for key, value in meta.items():
                    clean_key = key.lstrip("/")
                    rows.append({"key": clean_key, "value": str(value), "category": classify(clean_key)})
            else:
                rows.append({"key": "PDF Metadata", "value": "No metadata found.", "category": "normal"})

    except Exception as e:
        rows.append({"key": "Error", "value": str(e), "category": "sensitive"})

    return rows


class MetadataExtractorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Digital Forensics — Metadata Extractor")
        self.root.geometry("860x680")
        self.root.minsize(700, 500)
        self.root.configure(bg=BG_DARK)

        self._build_styles()
        self._build_ui()

    def _build_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Dark.TFrame",       background=BG_DARK)
        style.configure("Panel.TFrame",      background=BG_PANEL)
        style.configure("Card.TFrame",       background=BG_CARD)

        style.configure("Title.TLabel",      background=BG_DARK,  foreground=ACCENT,   font=FONT_TITLE)
        style.configure("Sub.TLabel",        background=BG_DARK,  foreground=TEXT_SEC, font=FONT_SUB)
        style.configure("Body.TLabel",       background=BG_PANEL, foreground=TEXT_PRI, font=FONT_BODY)
        style.configure("Status.TLabel",     background=BG_DARK,  foreground=TEXT_SEC, font=FONT_SUB)

        style.configure("Meta.Treeview",
                         background=BG_CARD, foreground=TEXT_PRI,
                         fieldbackground=BG_CARD, rowheight=24,
                         font=FONT_BODY, borderwidth=0)
        style.configure("Meta.Treeview.Heading",
                         background=HEADER_BG, foreground=ACCENT,
                         font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Meta.Treeview",
                  background=[("selected", "#264f78")],
                  foreground=[("selected", TEXT_PRI)])

        style.configure("Accent.TButton",
                         background=ACCENT, foreground="#000000",
                         font=("Segoe UI", 10, "bold"),
                         padding=(12, 6), relief="flat", borderwidth=0)
        style.map("Accent.TButton",
                  background=[("active", "#79c0ff")])

        style.configure("Ghost.TButton",
                         background=BG_PANEL, foreground=TEXT_PRI,
                         font=FONT_BODY, padding=(10, 5), relief="flat")
        style.map("Ghost.TButton",
                  background=[("active", HEADER_BG)])

    def _build_ui(self):
        header = ttk.Frame(self.root, style="Dark.TFrame", padding=(24, 18, 24, 10))
        header.pack(fill="x")

        left_head = ttk.Frame(header, style="Dark.TFrame")
        left_head.pack(side="left", fill="y")

        ttk.Label(left_head, text="🔍  Metadata Extractor", style="Title.TLabel").pack(anchor="w")
        ttk.Label(left_head, text="Digital Forensics Tool · Cybersecurity Project",
                  style="Sub.TLabel").pack(anchor="w", pady=(2, 0))

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=0)

        pick_frame = ttk.Frame(self.root, style="Panel.TFrame", padding=(24, 16))
        pick_frame.pack(fill="x")

        row1 = ttk.Frame(pick_frame, style="Panel.TFrame")
        row1.pack(fill="x")

        self.path_var = tk.StringVar(value="No file selected")
        path_lbl = tk.Label(row1, textvariable=self.path_var,
                            bg=BG_CARD, fg=TEXT_SEC, font=FONT_BODY,
                            anchor="w", padx=12, pady=8,
                            relief="flat", cursor="hand2")
        path_lbl.pack(side="left", fill="x", expand=True, ipady=2)

        ttk.Button(row1, text="  Browse File  ", style="Accent.TButton",
                   command=self._browse).pack(side="left", padx=(10, 0))

        row2 = ttk.Frame(pick_frame, style="Panel.TFrame")
        row2.pack(fill="x", pady=(8, 0))

        self._make_tag_pill(row2, "  📷 JPG / PNG / TIFF  ", ACCENT)
        self._make_tag_pill(row2, "  📄 PDF  ", ACCENT2)
        self._make_tag_pill(row2, "  ⚠ May reveal location & device info  ", WARNING)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        legend = ttk.Frame(self.root, style="Dark.TFrame", padding=(24, 8, 24, 4))
        legend.pack(fill="x")
        self._make_tag_pill(legend, " 🔴 Sensitive ",  DANGER,   bg=BG_DARK)
        self._make_tag_pill(legend, " 🟠 Noteworthy ", WARNING,  bg=BG_DARK)
        self._make_tag_pill(legend, " ⚪ Normal ",      TEXT_SEC, bg=BG_DARK)
        tk.Label(legend, text="← colour coding", bg=BG_DARK,
                 fg=TEXT_SEC, font=FONT_SUB).pack(side="left", padx=6)

        tree_frame = ttk.Frame(self.root, style="Dark.TFrame", padding=(24, 6, 24, 0))
        tree_frame.pack(fill="both", expand=True)

        cols = ("Field", "Value")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                  style="Meta.Treeview", selectmode="browse")
        self.tree.heading("Field", text="Metadata Field")
        self.tree.heading("Value", text="Extracted Value")
        self.tree.column("Field", width=220, minwidth=160, stretch=False)
        self.tree.column("Value", width=560, minwidth=300, stretch=True)

        self.tree.tag_configure("sensitive", foreground=DANGER)
        self.tree.tag_configure("warning",   foreground=WARNING)
        self.tree.tag_configure("normal",    foreground=TEXT_PRI)
        self.tree.tag_configure("odd",       background="#171c22")
        self.tree.tag_configure("even",      background=BG_CARD)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self._copy_value)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")
        footer = ttk.Frame(self.root, style="Dark.TFrame", padding=(24, 6))
        footer.pack(fill="x")

        self.status_var = tk.StringVar(value="Ready · Browse a file to extract its metadata")
        ttk.Label(footer, textvariable=self.status_var, style="Status.TLabel").pack(side="left")

        ttk.Button(footer, text="Export .txt", style="Ghost.TButton",
                   command=self._export).pack(side="right")
        ttk.Button(footer, text="Clear", style="Ghost.TButton",
                   command=self._clear).pack(side="right", padx=(0, 6))

        self.empty_lbl = tk.Label(self.root, text="Drop an image or PDF above to reveal hidden metadata",
                                   bg=BG_DARK, fg=TEXT_SEC, font=("Segoe UI", 11))
        self.empty_lbl.place(relx=0.5, rely=0.62, anchor="center")

        self._current_rows: list[dict] = []
        self._current_file: str = ""

    def _make_tag_pill(self, parent, text, color, bg=BG_PANEL):
        lbl = tk.Label(parent, text=text, bg=bg, fg=color, font=FONT_TAG,
                        padx=4, pady=2)
        lbl.pack(side="left", padx=(0, 6))

    def _browse(self):
        filetypes = [
            ("Supported files", "*.jpg *.jpeg *.png *.tiff *.tif *.bmp *.gif *.pdf"),
            ("Images",          "*.jpg *.jpeg *.png *.tiff *.tif *.bmp *.gif"),
            ("PDF files",       "*.pdf"),
            ("All files",       "*.*"),
        ]
        path = filedialog.askopenfilename(title="Select a file", filetypes=filetypes)
        if not path:
            return
        self._analyse(path)

    def _analyse(self, path: str):
        self._current_file = path
        ext = os.path.splitext(path)[1].lower()

        if ext == ".pdf":
            rows = extract_pdf_metadata(path)
        elif ext in (".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".gif", ".webp"):
            rows = extract_image_metadata(path)
        else:
            messagebox.showwarning("Unsupported", f"File type '{ext}' is not supported.\nSupported: JPG, PNG, TIFF, BMP, GIF, PDF")
            return

        self._current_rows = rows
        self._populate(rows, path)

    def _populate(self, rows: list[dict], path: str):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.empty_lbl.place_forget()

        sensitive_count = sum(1 for r in rows if r["category"] == "sensitive")
        warning_count   = sum(1 for r in rows if r["category"] == "warning")

        for i, row in enumerate(rows):
            stripe = "odd" if i % 2 else "even"
            tags   = (row["category"], stripe)
            self.tree.insert("", "end", values=(row["key"], row["value"]), tags=tags)

        fname = os.path.basename(path)
        self.path_var.set(f"  {path}")
        self.status_var.set(
            f"{fname}  ·  {len(rows)} fields extracted  "
            f"·  🔴 {sensitive_count} sensitive  ·  🟠 {warning_count} noteworthy"
            f"  ·  Double-click a row to copy its value"
        )

    def _copy_value(self, event):
        item = self.tree.focus()
        if not item:
            return
        value = self.tree.item(item, "values")[1]
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.status_var.set(f"✅  Copied: {value[:80]}{'…' if len(value) > 80 else ''}")

    def _clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.path_var.set("No file selected")
        self.status_var.set("Ready · Browse a file to extract its metadata")
        self._current_rows = []
        self._current_file = ""
        self.empty_lbl.place(relx=0.5, rely=0.62, anchor="center")

    def _export(self):
        if not self._current_rows:
            messagebox.showinfo("Nothing to export", "Extract metadata from a file first.")
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")],
            initialfile="metadata_report.txt",
            title="Save Metadata Report",
        )
        if not save_path:
            return
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write("  DIGITAL FORENSICS — METADATA EXTRACTOR REPORT\n")
                f.write(f"  Generated : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"  Source    : {self._current_file}\n")
                f.write("=" * 60 + "\n\n")
                for row in self._current_rows:
                    tag = "⚠ " if row["category"] == "warning" else ("🔴 " if row["category"] == "sensitive" else "   ")
                    f.write(f"{tag}{row['key']:<30} {row['value']}\n")
                f.write("\n" + "=" * 60 + "\n")
                f.write("  End of Report\n")
            self.status_var.set(f"✅  Report saved → {save_path}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app  = MetadataExtractorApp(root)
    root.mainloop()
