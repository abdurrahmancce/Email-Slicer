import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re
import os
from datetime import datetime

#  THEME  (dark navy / electric-cyan palette)
TH = {
    "bg":          "#0d1117",   # near-black background
    "surface":     "#161b22",   # card / panel background
    "surface2":    "#1c2330",   # slightly lighter panel
    "border":      "#30363d",   # subtle borders
    "cyan":        "#58e6d9",   # primary accent
    "cyan_dim":    "#2d8f87",   # muted accent
    "cyan_dark":   "#1a5c58",   # hover fills
    "green":       "#3fb950",   # success
    "yellow":      "#e3b341",   # warning
    "red":         "#f85149",   # error / danger
    "blue":        "#79c0ff",   # info
    "text":        "#e6edf3",   # primary text
    "text_dim":    "#8b949e",   # secondary text
    "text_muted":  "#484f58",   # muted / placeholder
    "white":       "#ffffff",
    "font_head":   ("Courier", 15, "bold"),
    "font_title":  ("Courier", 12, "bold"),
    "font_body":   ("Courier", 10),
    "font_small":  ("Courier", 9),
    "font_mono":   ("Courier", 11, "bold"),
    "font_huge":   ("Courier", 22, "bold"),
}

#  DOMAIN DATA
TEMPORARY_DOMAINS = {
    "mailinator.com","guerrillamail.com","temp-mail.org","throwam.com",
    "yopmail.com","dispostable.com","maildrop.cc","sharklasers.com",
    "guerrillamailblock.com","grr.la","guerrillamail.info","spam4.me",
    "trashmail.com","trashmail.me","trashmail.net","discard.email",
    "fakeinbox.com","mailnull.com","spamgourmet.com","spamgourmet.net",
    "tempinbox.com","tempmail.com","tempmail.net","tempr.email",
    "10minutemail.com","33mail.com","airmail.cc",
}

POPULAR_DOMAINS = {
    "gmail.com":      "Google Mail",
    "yahoo.com":      "Yahoo Mail",
    "outlook.com":    "Microsoft Outlook",
    "hotmail.com":    "Microsoft Hotmail",
    "icloud.com":     "Apple iCloud",
    "protonmail.com": "ProtonMail (Encrypted)",
    "aol.com":        "AOL Mail",
    "live.com":       "Microsoft Live",
    "msn.com":        "Microsoft MSN",
    "me.com":         "Apple Mail",
    "mac.com":        "Apple Mail",
}

EXTENSION_INFO = {
    ".com": "Commercial",    ".org": "Organization",
    ".net": "Network",       ".edu": "Educational",
    ".gov": "Government",    ".mil": "Military",
    ".int": "International", ".io":  "Tech / Startup",
    ".co":  "Company",       ".info":"Informational",
    ".biz": "Business",      ".app": "Application",
    ".dev": "Developer",     ".ai":  "AI / Tech",
    ".tv":  "Television",    ".me":  "Personal",
    ".us":  "United States", ".uk":  "United Kingdom",
    ".ca":  "Canada",        ".au":  "Australia",
    ".de":  "Germany",       ".fr":  "France",
    ".jp":  "Japan",         ".in":  "India",
    ".bd":  "Bangladesh",
}

#  CORE LOGIC
def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def slice_email(email: str) -> dict:
    email = email.strip().lower()
    at_index = email.index("@")
    username = email[:at_index]
    domain_full = email[at_index + 1:]
    dot_parts = domain_full.split(".")
    if len(dot_parts) >= 3:
        domain_name = ".".join(dot_parts[:-2])
        extension   = "." + ".".join(dot_parts[-2:])
    elif len(dot_parts) == 2:
        domain_name = dot_parts[0]
        extension   = "." + dot_parts[1]
    else:
        domain_name = domain_full
        extension   = ""
    return {
        "original":    email,
        "username":    username,
        "domain_full": domain_full,
        "domain_name": domain_name,
        "extension":   extension,
        "is_temp":     domain_full in TEMPORARY_DOMAINS,
        "provider":    POPULAR_DOMAINS.get(domain_full, "Unknown / Custom"),
        "ext_type":    EXTENSION_INFO.get(extension, "Unknown"),
    }


#  REUSABLE WIDGET HELPERS
def make_frame(parent, bg=None, **kw):
    return tk.Frame(parent, bg=bg or TH["surface"], **kw)


def make_label(parent, text, font=None, fg=None, bg=None, **kw):
    return tk.Label(
        parent, text=text,
        font=font or TH["font_body"],
        fg=fg or TH["text"],
        bg=bg or TH["surface"],
        **kw
    )


def card(parent, padx=16, pady=12):
    """Bordered card frame."""
    outer = tk.Frame(parent, bg=TH["border"], padx=1, pady=1)
    inner = tk.Frame(outer, bg=TH["surface2"], padx=padx, pady=pady)
    inner.pack(fill="both", expand=True)
    return outer, inner


def accent_button(parent, text, command, width=18, danger=False):
    color  = TH["red"]   if danger else TH["cyan"]
    hover  = "#c0392b"   if danger else TH["cyan_dark"]
    fg     = TH["white"] if danger else TH["bg"]
    btn = tk.Button(
        parent, text=text, command=command,
        font=TH["font_body"],
        fg=fg, bg=color,
        activeforeground=fg, activebackground=hover,
        relief="flat", cursor="hand2", width=width,
        padx=10, pady=6,
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=hover))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def ghost_button(parent, text, command, width=16):
    btn = tk.Button(
        parent, text=text, command=command,
        font=TH["font_small"],
        fg=TH["text_dim"], bg=TH["surface"],
        activeforeground=TH["cyan"], activebackground=TH["surface"],
        relief="flat", cursor="hand2", width=width,
        padx=8, pady=4,
        highlightthickness=1, highlightbackground=TH["border"],
    )
    btn.bind("<Enter>", lambda e: btn.config(fg=TH["cyan"], highlightbackground=TH["cyan_dim"]))
    btn.bind("<Leave>", lambda e: btn.config(fg=TH["text_dim"], highlightbackground=TH["border"]))
    return btn


#  RESULT CARD  (reusable animated reveal)
class ResultCard(tk.Frame):
    def __init__(self, parent, result: dict, **kw):
        super().__init__(parent, bg=TH["surface2"], **kw)
        self._result = result
        self._build()

    def _build(self):
        r = self._result
        is_temp = r["is_temp"]

        # ── Header bar
        hdr_bg = TH["red"] if is_temp else TH["cyan_dark"]
        hdr = tk.Frame(self, bg=hdr_bg, padx=14, pady=8)
        hdr.pack(fill="x")

        icon  = "⚠  DISPOSABLE" if is_temp else "✔  VALID"
        hdr_c = TH["yellow"] if is_temp else TH["cyan"]
        tk.Label(hdr, text=icon, font=TH["font_title"],
                 fg=hdr_c, bg=hdr_bg).pack(side="left")
        tk.Label(hdr, text=r["original"], font=TH["font_body"],
                 fg=TH["text_dim"], bg=hdr_bg).pack(side="right")

        # ── Body rows
        body = tk.Frame(self, bg=TH["surface2"], padx=14, pady=10)
        body.pack(fill="both", expand=True)

        rows = [
            ("👤  Username",      r["username"],    TH["green"]),
            ("🌐  Full Domain",   r["domain_full"], TH["blue"]),
            ("🏷   Domain Name",  r["domain_name"], TH["cyan"]),
            ("🔖  Extension",     r["extension"],   TH["cyan"]),
            ("📮  Provider",      r["provider"],    TH["yellow"]),
            ("📁  Ext. Type",     r["ext_type"],    TH["text_dim"]),
        ]

        for label, value, color in rows:
            row_f = tk.Frame(body, bg=TH["surface2"])
            row_f.pack(fill="x", pady=2)
            tk.Label(row_f, text=f"{label:<22}", font=TH["font_small"],
                     fg=TH["text_dim"], bg=TH["surface2"]).pack(side="left")
            tk.Label(row_f, text="→", font=TH["font_small"],
                     fg=TH["border"], bg=TH["surface2"]).pack(side="left", padx=4)
            tk.Label(row_f, text=value, font=("Courier", 10, "bold"),
                     fg=color, bg=TH["surface2"]).pack(side="left")

        # ── Bottom border accent
        accent_h = TH["red"] if is_temp else TH["cyan_dim"]
        tk.Frame(self, bg=accent_h, height=2).pack(fill="x", side="bottom")


#  ANIMATED FLASH  (border flash on entry)
def flash_widget(widget, color=None, original=None, steps=6, delay=60):
    color    = color    or TH["cyan"]
    original = original or TH["border"]
    colors   = [color, original] * (steps // 2)

    def step(i=0):
        if i < len(colors):
            try:
                widget.config(highlightbackground=colors[i])
                widget.after(delay, lambda: step(i + 1))
            except Exception:
                pass
    step()


#  NOTIFICATION BAR
class NotifBar(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=TH["bg"], height=28, **kw)
        self._lbl = tk.Label(self, text="", font=TH["font_small"],
                             fg=TH["text_dim"], bg=TH["bg"])
        self._lbl.pack(side="left", padx=12)
        self._job = None

    def show(self, msg, color=None, duration=3500):
        if self._job:
            self.after_cancel(self._job)
        self._lbl.config(text=f"  {msg}", fg=color or TH["cyan"])
        self._job = self.after(duration, self.clear)

    def clear(self):
        self._lbl.config(text="")


#  MAIN APPLICATION WINDOW
class EmailSlicerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("✉  Email Slicer & Analyzer")
        self.geometry("820x700")
        self.minsize(760, 600)
        self.configure(bg=TH["bg"])
        self.resizable(True, True)

        # session stats
        self._stats = {"total": 0, "valid": 0, "invalid": 0, "temp": 0}
        self._history = []   # list of result dicts

        self._build_ui()
        self._center_window()

    def _center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    # ── Build all UI
    def _build_ui(self):
        self._build_header()
        self._build_notif()
        self._build_tabs()
        self._build_footer()

    # ── Header
    def _build_header(self):
        hdr = tk.Frame(self, bg=TH["surface"], pady=0)
        hdr.pack(fill="x")

        # Top accent line
        tk.Frame(hdr, bg=TH["cyan"], height=3).pack(fill="x")

        inner = tk.Frame(hdr, bg=TH["surface"], padx=20, pady=12)
        inner.pack(fill="x")

        left = tk.Frame(inner, bg=TH["surface"])
        left.pack(side="left")

        tk.Label(left, text="✉  Email Slicer", font=TH["font_head"],
                 fg=TH["cyan"], bg=TH["surface"]).pack(side="left")
        tk.Label(left, text="  &  Analyzer", font=("Courier", 14),
                 fg=TH["text_dim"], bg=TH["surface"]).pack(side="left")

        right = tk.Frame(inner, bg=TH["surface"])
        right.pack(side="right")
        tk.Label(right, text="v2.0  GUI Edition", font=TH["font_small"],
                 fg=TH["text_muted"], bg=TH["surface"]).pack()

        tk.Frame(hdr, bg=TH["border"], height=1).pack(fill="x")

    # ── Notification bar
    def _build_notif(self):
        self._notif = NotifBar(self)
        self._notif.pack(fill="x")

    # ── Tabs
    def _build_tabs(self):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TNotebook",
                        background=TH["bg"], borderwidth=0,
                        tabmargins=[0, 0, 0, 0])
        style.configure("TNotebook.Tab",
                        background=TH["surface"], foreground=TH["text_dim"],
                        font=TH["font_body"], padding=[18, 8],
                        focuscolor=TH["bg"])
        style.map("TNotebook.Tab",
                  background=[("selected", TH["surface2"])],
                  foreground=[("selected", TH["cyan"])],
                  expand=[("selected", [0, 0, 0, 0])])

        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=0, pady=0)

        self._tab_single = tk.Frame(self._nb, bg=TH["bg"])
        self._tab_bulk   = tk.Frame(self._nb, bg=TH["bg"])
        self._tab_hist   = tk.Frame(self._nb, bg=TH["bg"])
        self._tab_stats  = tk.Frame(self._nb, bg=TH["bg"])

        self._nb.add(self._tab_single, text="  🔍  Single  ")
        self._nb.add(self._tab_bulk,   text="  📂  Bulk    ")
        self._nb.add(self._tab_hist,   text="  📋  History ")
        self._nb.add(self._tab_stats,  text="  📊  Stats   ")

        self._build_single_tab()
        self._build_bulk_tab()
        self._build_history_tab()
        self._build_stats_tab()

    # ── SINGLE TAB
    def _build_single_tab(self):
        p = tk.Frame(self._tab_single, bg=TH["bg"], padx=24, pady=20)
        p.pack(fill="both", expand=True)

        # Input card
        o, c = card(p)
        o.pack(fill="x", pady=(0, 12))

        tk.Label(c, text="Enter an email address to analyze",
                 font=TH["font_title"], fg=TH["text"], bg=TH["surface2"]).pack(anchor="w")
        tk.Label(c, text="Extracts username, domain, extension, provider, and more.",
                 font=TH["font_small"], fg=TH["text_dim"], bg=TH["surface2"]).pack(anchor="w", pady=(2, 10))

        entry_frame = tk.Frame(c, bg=TH["surface2"])
        entry_frame.pack(fill="x")

        self._single_var = tk.StringVar()
        self._single_entry = tk.Entry(
            entry_frame,
            textvariable=self._single_var,
            font=TH["font_mono"],
            fg=TH["text"], bg=TH["bg"],
            insertbackground=TH["cyan"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=TH["border"],
            highlightcolor=TH["cyan"],
        )
        self._single_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))
        self._single_entry.bind("<Return>", lambda e: self._analyze_single())
        self._single_entry.bind("<FocusIn>", lambda e: self._single_entry.config(highlightbackground=TH["cyan"]))
        self._single_entry.bind("<FocusOut>", lambda e: self._single_entry.config(highlightbackground=TH["border"]))

        accent_button(entry_frame, "  Analyze  ▶", self._analyze_single, width=14).pack(side="left")

        # Paste hint
        tk.Label(c, text="Press Enter or click Analyze",
                 font=TH["font_small"], fg=TH["text_muted"], bg=TH["surface2"]).pack(anchor="w", pady=(6, 0))

        # Result area — scrollable
        result_container = tk.Frame(p, bg=TH["bg"])
        result_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(result_container, bg=TH["bg"], highlightthickness=0)
        scroll = tk.Scrollbar(result_container, orient="vertical",
                              command=canvas.yview, bg=TH["surface"])
        canvas.configure(yscrollcommand=scroll.set)

        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._single_result_frame = tk.Frame(canvas, bg=TH["bg"])
        canvas_win = canvas.create_window((0, 0), window=self._single_result_frame, anchor="nw")

        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_win, width=canvas.winfo_width())
        self._single_result_frame.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_win, width=e.width))

        # Mouse-wheel scroll
        def _mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _mousewheel)

        self._single_result_frame._canvas = canvas

    def _analyze_single(self):
        raw = self._single_var.get().strip()
        if not raw:
            self._notif.show("⚠  Please enter an email address.", TH["yellow"])
            flash_widget(self._single_entry, TH["yellow"])
            return

        self._stats["total"] += 1

        if not validate_email(raw):
            self._stats["invalid"] += 1
            self._update_stats_tab()
            self._notif.show(f"✘  '{raw}' — invalid email format.", TH["red"])
            flash_widget(self._single_entry, TH["red"])
            self._show_single_error(raw)
            return

        result = slice_email(raw)
        self._stats["valid"] += 1
        if result["is_temp"]:
            self._stats["temp"] += 1
        self._history.append(result)
        self._update_stats_tab()
        self._refresh_history_tab()

        # Clear old result
        for w in self._single_result_frame.winfo_children():
            w.destroy()

        # Animate reveal
        card_widget = ResultCard(self._single_result_frame, result,
                                 highlightthickness=1,
                                 highlightbackground=TH["cyan"])
        card_widget.pack(fill="x", padx=0, pady=(8, 0))

        save_row = tk.Frame(self._single_result_frame, bg=TH["bg"])
        save_row.pack(fill="x", pady=8)
        ghost_button(save_row, "💾  Save to File", lambda: self._save_results([result]), width=18).pack(side="left")
        ghost_button(save_row, "🗑  Clear", self._clear_single, width=12).pack(side="left", padx=8)

        self._single_result_frame._canvas.yview_moveto(0)
        flash_widget(card_widget,
                     TH["yellow"] if result["is_temp"] else TH["cyan"],
                     TH["cyan"] if not result["is_temp"] else TH["red"])

        msg = (f"⚠  Disposable email detected: {raw}"
               if result["is_temp"] else
               f"✔  Analyzed: {raw}")
        self._notif.show(msg, TH["yellow"] if result["is_temp"] else TH["green"])

    def _show_single_error(self, raw):
        for w in self._single_result_frame.winfo_children():
            w.destroy()
        err = tk.Frame(self._single_result_frame, bg=TH["surface2"],
                       highlightthickness=1, highlightbackground=TH["red"],
                       padx=14, pady=12)
        err.pack(fill="x", pady=(8, 0))
        tk.Label(err, text="✘  Invalid Email Address",
                 font=TH["font_title"], fg=TH["red"], bg=TH["surface2"]).pack(anchor="w")
        tk.Label(err, text=f'  "{raw}" does not match a valid email pattern.',
                 font=TH["font_body"], fg=TH["text_dim"], bg=TH["surface2"]).pack(anchor="w", pady=4)
        tk.Label(err, text="  Expected format:  username@domain.extension",
                 font=TH["font_small"], fg=TH["text_muted"], bg=TH["surface2"]).pack(anchor="w")

    def _clear_single(self):
        self._single_var.set("")
        for w in self._single_result_frame.winfo_children():
            w.destroy()
        self._single_entry.focus_set()

    # ── BULK TAB
    def _build_bulk_tab(self):
        p = tk.Frame(self._tab_bulk, bg=TH["bg"], padx=24, pady=20)
        p.pack(fill="both", expand=True)

        # Input card
        o, c = card(p)
        o.pack(fill="x", pady=(0, 12))

        top = tk.Frame(c, bg=TH["surface2"])
        top.pack(fill="x")
        tk.Label(top, text="Bulk Email Processor",
                 font=TH["font_title"], fg=TH["text"], bg=TH["surface2"]).pack(side="left")
        tk.Label(top, text="  One email per line",
                 font=TH["font_small"], fg=TH["text_muted"], bg=TH["surface2"]).pack(side="left", pady=(4, 0))

        ghost_button(top, "📂  Load from .txt", self._load_bulk_file, width=18).pack(side="right")

        text_frame = tk.Frame(c, bg=TH["surface2"], pady=8)
        text_frame.pack(fill="x")

        self._bulk_text = tk.Text(
            text_frame,
            height=6, wrap="none",
            font=TH["font_body"],
            fg=TH["text"], bg=TH["bg"],
            insertbackground=TH["cyan"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=TH["border"],
            highlightcolor=TH["cyan"],
            selectbackground=TH["cyan_dark"],
        )
        bulk_scroll_y = tk.Scrollbar(text_frame, orient="vertical",
                                     command=self._bulk_text.yview)
        self._bulk_text.configure(yscrollcommand=bulk_scroll_y.set)
        bulk_scroll_y.pack(side="right", fill="y")
        self._bulk_text.pack(fill="x", ipady=4)
        self._bulk_text.bind("<FocusIn>",  lambda e: self._bulk_text.config(highlightbackground=TH["cyan"]))
        self._bulk_text.bind("<FocusOut>", lambda e: self._bulk_text.config(highlightbackground=TH["border"]))

        btn_row = tk.Frame(c, bg=TH["surface2"])
        btn_row.pack(fill="x", pady=(8, 0))
        accent_button(btn_row, "  Process All  ▶", self._analyze_bulk, width=16).pack(side="left")
        ghost_button(btn_row, "🗑  Clear All", self._clear_bulk, width=12).pack(side="left", padx=8)

        # Results area
        result_container = tk.Frame(p, bg=TH["bg"])
        result_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(result_container, bg=TH["bg"], highlightthickness=0)
        sc = tk.Scrollbar(result_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sc.set)
        sc.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._bulk_result_frame = tk.Frame(canvas, bg=TH["bg"])
        cwin = canvas.create_window((0, 0), window=self._bulk_result_frame, anchor="nw")

        def _conf(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(cwin, width=canvas.winfo_width())
        self._bulk_result_frame.bind("<Configure>", _conf)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cwin, width=e.width))

        self._bulk_result_frame._canvas = canvas

    def _load_bulk_file(self):
        path = filedialog.askopenfilename(
            title="Load email list",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self._bulk_text.delete("1.0", "end")
            self._bulk_text.insert("1.0", content)
            self._notif.show(f"✔  Loaded: {os.path.basename(path)}", TH["green"])
        except Exception as ex:
            self._notif.show(f"✘  Could not read file: {ex}", TH["red"])

    def _analyze_bulk(self):
        raw_text = self._bulk_text.get("1.0", "end").strip()
        if not raw_text:
            self._notif.show("⚠  Please enter at least one email.", TH["yellow"])
            return

        emails = [line.strip() for line in raw_text.splitlines() if line.strip()]

        for w in self._bulk_result_frame.winfo_children():
            w.destroy()

        valid_results = []
        invalid_list  = []
        temp_count    = 0

        for email in emails:
            self._stats["total"] += 1
            if not validate_email(email):
                self._stats["invalid"] += 1
                invalid_list.append(email)
            else:
                r = slice_email(email)
                self._stats["valid"] += 1
                if r["is_temp"]:
                    self._stats["temp"] += 1
                    temp_count += 1
                valid_results.append(r)
                self._history.append(r)

        self._update_stats_tab()
        self._refresh_history_tab()

        # ── Summary bar
        summary = tk.Frame(self._bulk_result_frame, bg=TH["surface2"],
                           padx=14, pady=10,
                           highlightthickness=1, highlightbackground=TH["cyan_dim"])
        summary.pack(fill="x", pady=(0, 10))
        tk.Label(summary, text="📊  Bulk Summary", font=TH["font_title"],
                 fg=TH["cyan"], bg=TH["surface2"]).pack(anchor="w")
        tk.Frame(summary, bg=TH["border"], height=1).pack(fill="x", pady=6)

        cols = tk.Frame(summary, bg=TH["surface2"])
        cols.pack(fill="x")
        for label, val, color in [
            ("Total",   len(emails),       TH["text"]),
            ("Valid",   len(valid_results), TH["green"]),
            ("Invalid", len(invalid_list),  TH["red"]),
            ("Temp",    temp_count,         TH["yellow"]),
        ]:
            cell = tk.Frame(cols, bg=TH["surface"], padx=14, pady=8)
            cell.pack(side="left", padx=(0, 8), pady=2)
            tk.Label(cell, text=str(val), font=TH["font_huge"],
                     fg=color, bg=TH["surface"]).pack()
            tk.Label(cell, text=label, font=TH["font_small"],
                     fg=TH["text_muted"], bg=TH["surface"]).pack()

        if valid_results:
            btn_row = tk.Frame(summary, bg=TH["surface2"])
            btn_row.pack(anchor="e", pady=(6, 0))
            ghost_button(btn_row, "💾  Save All to File",
                         lambda: self._save_results(valid_results), width=20).pack(side="right")

        # ── Invalid list
        if invalid_list:
            bad = tk.Frame(self._bulk_result_frame, bg=TH["surface2"],
                           padx=14, pady=10,
                           highlightthickness=1, highlightbackground=TH["red"])
            bad.pack(fill="x", pady=(0, 10))
            tk.Label(bad, text="✘  Invalid Emails", font=TH["font_title"],
                     fg=TH["red"], bg=TH["surface2"]).pack(anchor="w")
            for inv in invalid_list:
                tk.Label(bad, text=f"   • {inv}", font=TH["font_small"],
                         fg=TH["text_dim"], bg=TH["surface2"]).pack(anchor="w")

        # ── Valid result cards
        for i, res in enumerate(valid_results):
            rc = ResultCard(self._bulk_result_frame, res)
            rc.pack(fill="x", pady=(0, 8))
            rc.after(i * 80, lambda w=rc: w.configure(highlightthickness=0))

        self._notif.show(
            f"✔  Processed {len(emails)} emails — {len(valid_results)} valid, {len(invalid_list)} invalid",
            TH["green"]
        )

    def _clear_bulk(self):
        self._bulk_text.delete("1.0", "end")
        for w in self._bulk_result_frame.winfo_children():
            w.destroy()

    # ── HISTORY TAB
    def _build_history_tab(self):
        p = tk.Frame(self._tab_hist, bg=TH["bg"], padx=24, pady=20)
        p.pack(fill="both", expand=True)

        top = tk.Frame(p, bg=TH["bg"])
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="📋  Analysis History", font=TH["font_title"],
                 fg=TH["text"], bg=TH["bg"]).pack(side="left")

        btn_row = tk.Frame(top, bg=TH["bg"])
        btn_row.pack(side="right")
        ghost_button(btn_row, "💾  Export All", self._export_history, width=14).pack(side="left", padx=(0, 6))
        ghost_button(btn_row, "🗑  Clear", self._clear_history, width=10).pack(side="left")

        # Treeview table
        cols = ("Email", "Username", "Domain", "Extension", "Provider", "Temp?")
        style = ttk.Style()
        style.configure("History.Treeview",
                        background=TH["surface2"],
                        fieldbackground=TH["surface2"],
                        foreground=TH["text"],
                        font=TH["font_small"],
                        rowheight=26,
                        borderwidth=0)
        style.configure("History.Treeview.Heading",
                        background=TH["surface"],
                        foreground=TH["cyan"],
                        font=TH["font_small"],
                        relief="flat")
        style.map("History.Treeview",
                  background=[("selected", TH["cyan_dark"])],
                  foreground=[("selected", TH["white"])])

        tree_frame = tk.Frame(p, bg=TH["bg"])
        tree_frame.pack(fill="both", expand=True)

        self._hist_tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                       style="History.Treeview", selectmode="browse")
        widths = [200, 120, 150, 90, 160, 60]
        for col, w in zip(cols, widths):
            self._hist_tree.heading(col, text=col)
            self._hist_tree.column(col, width=w, minwidth=60, anchor="w")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",   command=self._hist_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self._hist_tree.xview)
        self._hist_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self._hist_tree.pack(fill="both", expand=True)

        # Alternate row colors
        self._hist_tree.tag_configure("even", background=TH["surface"])
        self._hist_tree.tag_configure("odd",  background=TH["surface2"])
        self._hist_tree.tag_configure("temp", foreground=TH["yellow"])

        # Status bar
        self._hist_status = tk.Label(p, text="No records yet.", font=TH["font_small"],
                                     fg=TH["text_muted"], bg=TH["bg"])
        self._hist_status.pack(anchor="w", pady=(6, 0))

    def _refresh_history_tab(self):
        for item in self._hist_tree.get_children():
            self._hist_tree.delete(item)
        for i, r in enumerate(self._history):
            tag = ("temp",) if r["is_temp"] else (("even" if i % 2 == 0 else "odd"),)
            self._hist_tree.insert("", "end", values=(
                r["original"], r["username"], r["domain_full"],
                r["extension"], r["provider"],
                "⚠ Yes" if r["is_temp"] else "No"
            ), tags=tag)
        total = len(self._history)
        self._hist_status.config(
            text=f"  {total} record{'s' if total != 1 else ''} total" if total else "No records yet."
        )

    def _export_history(self):
        if not self._history:
            self._notif.show("⚠  No history to export.", TH["yellow"])
            return
        self._save_results(self._history, prompt=True)

    def _clear_history(self):
        if not self._history:
            return
        if messagebox.askyesno("Clear History", "Clear all history records?"):
            self._history.clear()
            self._refresh_history_tab()
            self._notif.show("🗑  History cleared.", TH["text_dim"])

    # ── STATS TAB
    def _build_stats_tab(self):
        p = tk.Frame(self._tab_stats, bg=TH["bg"], padx=24, pady=20)
        p.pack(fill="both", expand=True)

        tk.Label(p, text="📊  Session Statistics", font=TH["font_head"],
                 fg=TH["cyan"], bg=TH["bg"]).pack(anchor="w", pady=(0, 16))

        # Stat cards grid
        grid = tk.Frame(p, bg=TH["bg"])
        grid.pack(fill="x")

        self._stat_vars = {}
        stat_defs = [
            ("total",   "Total Analyzed",     TH["text"],   "📋"),
            ("valid",   "Valid Emails",        TH["green"],  "✔ "),
            ("invalid", "Invalid Emails",      TH["red"],    "✘ "),
            ("temp",    "Disposable Detected", TH["yellow"], "⚠ "),
        ]

        for col_i, (key, label, color, icon) in enumerate(stat_defs):
            cell = tk.Frame(grid, bg=TH["surface2"], padx=20, pady=16,
                            highlightthickness=1, highlightbackground=TH["border"])
            cell.grid(row=0, column=col_i, padx=(0, 12), pady=(0, 12), sticky="nsew")
            grid.columnconfigure(col_i, weight=1)

            val_var = tk.StringVar(value="0")
            self._stat_vars[key] = val_var
            tk.Label(cell, textvariable=val_var, font=TH["font_huge"],
                     fg=color, bg=TH["surface2"]).pack()
            tk.Label(cell, text=f"{icon} {label}", font=TH["font_small"],
                     fg=TH["text_dim"], bg=TH["surface2"]).pack()

        # Valid rate
        o, c = card(p)
        o.pack(fill="x", pady=(4, 16))
        self._valid_rate_var = tk.StringVar(value="N/A")
        self._valid_rate_bar_var = tk.DoubleVar(value=0)

        tk.Label(c, text="Valid Rate", font=TH["font_title"],
                 fg=TH["text"], bg=TH["surface2"]).pack(anchor="w")

        bar_frame = tk.Frame(c, bg=TH["surface2"], pady=6)
        bar_frame.pack(fill="x")

        self._rate_canvas = tk.Canvas(bar_frame, bg=TH["bg"], height=20,
                                      highlightthickness=0)
        self._rate_canvas.pack(fill="x", pady=4)
        tk.Label(bar_frame, textvariable=self._valid_rate_var,
                 font=TH["font_mono"], fg=TH["cyan"], bg=TH["surface2"]).pack(anchor="e")

        # Reset button
        ghost_button(p, "🔄  Reset Statistics", self._reset_stats, width=20).pack(anchor="w")

    def _update_stats_tab(self):
        s = self._stats
        for key, var in self._stat_vars.items():
            var.set(str(s[key]))

        pct = (s["valid"] / s["total"] * 100) if s["total"] > 0 else 0
        self._valid_rate_var.set(f"{pct:.1f}%")

        # Animate progress bar
        self._animate_bar(pct)

    def _animate_bar(self, target_pct, current=None):
        if current is None:
            current = 0.0
        step = (target_pct - current)
        if abs(step) < 0.5:
            current = target_pct
        else:
            current += step * 0.18

        try:
            w = self._rate_canvas.winfo_width()
            h = self._rate_canvas.winfo_height()
            self._rate_canvas.delete("all")
            # Background
            self._rate_canvas.create_rectangle(0, 0, w, h, fill=TH["surface"], outline="")
            # Fill
            fill_w = int(w * current / 100)
            if fill_w > 0:
                self._rate_canvas.create_rectangle(0, 0, fill_w, h, fill=TH["cyan_dim"], outline="")
                # Bright cap
                cap = min(fill_w, 4)
                self._rate_canvas.create_rectangle(fill_w - cap, 0, fill_w, h, fill=TH["cyan"], outline="")
        except Exception:
            pass

        if abs(current - target_pct) > 0.5:
            self.after(30, lambda: self._animate_bar(target_pct, current))

    def _reset_stats(self):
        if messagebox.askyesno("Reset Stats", "Reset all session statistics?"):
            self._stats = {"total": 0, "valid": 0, "invalid": 0, "temp": 0}
            self._update_stats_tab()
            self._notif.show("🔄  Statistics reset.", TH["text_dim"])

    # ── SAVE TO FILE
    def _save_results(self, results: list, prompt=False):
        if prompt:
            path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile="email_results.txt",
                title="Save Results",
            )
            if not path:
                return
        else:
            path = os.path.join(os.path.expanduser("~"), "email_results.txt")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Exported at: {timestamp}\n")
                f.write(f"{'='*50}\n")
                for r in results:
                    f.write(f"\nOriginal    : {r['original']}\n")
                    f.write(f"Username    : {r['username']}\n")
                    f.write(f"Domain      : {r['domain_full']}\n")
                    f.write(f"Domain Name : {r['domain_name']}\n")
                    f.write(f"Extension   : {r['extension']}\n")
                    f.write(f"Provider    : {r['provider']}\n")
                    f.write(f"Ext. Type   : {r['ext_type']}\n")
                    f.write(f"Temporary   : {'YES' if r['is_temp'] else 'No'}\n")
                    f.write(f"{'-'*30}\n")
            self._notif.show(f"💾  Saved {len(results)} record(s) → {os.path.basename(path)}", TH["green"])
        except Exception as ex:
            self._notif.show(f"✘  Save failed: {ex}", TH["red"])

    # ── FOOTER
    def _build_footer(self):
        footer = tk.Frame(self, bg=TH["surface"], pady=4)
        footer.pack(fill="x", side="bottom")
        tk.Frame(footer, bg=TH["border"], height=1).pack(fill="x")
        inner = tk.Frame(footer, bg=TH["surface"])
        inner.pack(fill="x", padx=16, pady=4)
        tk.Label(inner, text="Email Slicer & Analyzer  ·  GUI Edition  ·  Python + Tkinter",
                 font=TH["font_small"], fg=TH["text_muted"], bg=TH["surface"]).pack(side="left")
        tk.Label(inner, text="Beginner-friendly  ·  Open Source",
                 font=TH["font_small"], fg=TH["text_muted"], bg=TH["surface"]).pack(side="right")


#  ENTRY POINT
if __name__ == "__main__":
    app = EmailSlicerApp()
    app.mainloop()