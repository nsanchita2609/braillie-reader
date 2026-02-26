"""
Braill'ie - Main GUI
=====================
Run AFTER position_server.py is running.

Install:
    pip install pyserial PyMuPDF websockets

Run:
    python braillie_gui.py
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import asyncio
import json

try:
    import websockets
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

try:
    import fitz
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# ─────────────────────────────────────────
# BRAILLE MAP
# ─────────────────────────────────────────
BRAILLE_MAP = {
    'a':0b000001,'b':0b000011,'c':0b001001,'d':0b011001,'e':0b010001,
    'f':0b001011,'g':0b011011,'h':0b010011,'i':0b001010,'j':0b011010,
    'k':0b000101,'l':0b000111,'m':0b001101,'n':0b011101,'o':0b010101,
    'p':0b001111,'q':0b011111,'r':0b010111,'s':0b001110,'t':0b011110,
    'u':0b100101,'v':0b100111,'w':0b011010,'x':0b101101,'y':0b111101,
    'z':0b110101,' ':0b000000,
}

def char_to_braille_bits(ch):
    return BRAILLE_MAP.get(ch.lower(), 0b000000)

# ─────────────────────────────────────────
# PALETTE
# ─────────────────────────────────────────
C = {
    "bg":     "#0B0C10",
    "panel":  "#13151A",
    "card":   "#1A1D24",
    "border": "#2A2D35",
    "accent": "#00D4FF",
    "accent2":"#FF6B35",
    "green":  "#00FF94",
    "red":    "#FF4757",
    "text":   "#E8EAED",
    "muted":  "#6B7280",
}

# ─────────────────────────────────────────
# BRAILLE CELL WIDGET
# ─────────────────────────────────────────
class BrailleDisplay(tk.Canvas):
    def __init__(self, parent, size=80, **kwargs):
        super().__init__(parent, width=size, height=int(size*1.35),
                         bg=C["card"], highlightthickness=0, **kwargs)
        self.size = size
        self._draw(0)

    def set_char(self, ch):
        self._draw(char_to_braille_bits(ch))

    def _draw(self, bits):
        self.delete("all")
        s = self.size
        r = s * 0.11
        positions = [
            (s*0.3, s*0.2), (s*0.7, s*0.2),
            (s*0.3, s*0.52),(s*0.7, s*0.52),
            (s*0.3, s*0.84),(s*0.7, s*0.84),
        ]
        for i, (x, y) in enumerate(positions):
            active = (bits >> i) & 1
            if active:
                self.create_oval(x-r*1.6,y-r*1.6,x+r*1.6,y+r*1.6,
                                 fill="#00334A", outline=C["accent"], width=1.5)
                self.create_oval(x-r,y-r,x+r,y+r, fill=C["accent"], outline="")
            else:
                self.create_oval(x-r,y-r,x+r,y+r, fill=C["border"], outline="")

# ─────────────────────────────────────────
# SCREEN BASE
# ─────────────────────────────────────────
class Screen(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C["bg"])
    def show(self): self.pack(fill="both", expand=True)
    def hide(self): self.pack_forget()

# ─────────────────────────────────────────
# SCREEN 1 — WELCOME
# ─────────────────────────────────────────
class WelcomeScreen(Screen):
    def __init__(self, parent, on_next):
        super().__init__(parent)
        self.on_next = on_next
        self._build()

    def _build(self):
        tk.Frame(self, bg=C["bg"], height=70).pack()
        tk.Label(self, text="✦", font=("Georgia",52), bg=C["bg"], fg=C["accent"]).pack()
        tk.Label(self, text="Braill'ie", font=("Georgia",44,"bold"),
                 bg=C["bg"], fg=C["text"]).pack()
        tk.Label(self, text="YOUR  READING  ASSISTANT",
                 font=("Courier",10), bg=C["bg"], fg=C["muted"]).pack(pady=(2,0))
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", padx=100, pady=28)
        tk.Label(self, text="Converting any PDF into tactile braille,\none character at a time.",
                 font=("Georgia",13,"italic"), bg=C["bg"],
                 fg=C["muted"], justify="center").pack()
        tk.Frame(self, bg=C["bg"], height=40).pack()
        tk.Button(self, text="GET STARTED  →",
                  font=("Courier",13,"bold"),
                  bg=C["accent"], fg=C["bg"],
                  relief="flat", padx=30, pady=12,
                  cursor="hand2", command=self.on_next).pack()
        tk.Frame(self, bg=C["bg"], height=16).pack()
        tk.Label(self, text="Start position_server.py before continuing",
                 font=("Courier",9), bg=C["bg"], fg=C["muted"]).pack()

# ─────────────────────────────────────────
# SCREEN 2 — CALIBRATE
# ─────────────────────────────────────────
class CalibrateScreen(Screen):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=C["panel"], pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="STEP 1  —  CALIBRATE",
                 font=("Courier",11,"bold"), bg=C["panel"], fg=C["accent"]).pack()

        tk.Frame(self, bg=C["bg"], height=24).pack()

        card = tk.Frame(self, bg=C["card"], padx=50, pady=30)
        card.pack(padx=80)
        tk.Label(card, text="⊕", font=("Arial",40), bg=C["card"], fg=C["accent"]).pack()
        tk.Label(card, text="Move Glove to Top-Left Corner of Page",
                 font=("Georgia",15,"bold"), bg=C["card"],
                 fg=C["text"], justify="center").pack(pady=(8,4))
        tk.Label(card,
                 text="This sets the origin point (0,0).\nAll character positions are measured from here.",
                 font=("Courier",10), bg=C["card"], fg=C["muted"],
                 justify="center").pack()

        tk.Frame(self, bg=C["bg"], height=20).pack()

        # Diagram
        d = tk.Canvas(self, width=320, height=150, bg=C["card"], highlightthickness=0)
        d.pack()
        d.create_rectangle(30,20,290,130, outline=C["border"], width=2)
        d.create_oval(20,10,48,38, fill=C["accent2"], outline="")
        d.create_text(34,24, text="✦", fill="white", font=("Arial",9,"bold"))
        d.create_text(56,24, text="← Glove starts here",
                      fill=C["accent"], font=("Courier",9), anchor="w")
        d.create_line(34,38,34,52, fill=C["accent2"], width=2, arrow="last")
        d.create_text(160,80, text="P D F  P A G E",
                      fill=C["border"], font=("Courier",10))

        tk.Frame(self, bg=C["bg"], height=18).pack()
        self.status = tk.Label(self, text="Waiting...",
                                font=("Courier",10), bg=C["bg"], fg=C["muted"])
        self.status.pack()
        tk.Frame(self, bg=C["bg"], height=12).pack()

        self.btn = tk.Button(self, text="✦  CALIBRATE NOW",
                              font=("Courier",13,"bold"),
                              bg=C["accent2"], fg="white",
                              relief="flat", padx=28, pady=12,
                              cursor="hand2", command=self._calibrate)
        self.btn.pack()

    def _calibrate(self):
        self.status.config(text="Sending calibration signal...", fg=C["accent"])
        self.btn.config(state="disabled")
        self.app.ws_send({"cmd": "calibrate"})
        self.after(900, self._done)

    def _done(self):
        self.status.config(text="✔  Origin set! Opening PDF reader...", fg=C["green"])
        self.after(1100, self.app.go_to_pdf)

# ─────────────────────────────────────────
# SCREEN 3 — PDF READER
# ─────────────────────────────────────────
class PDFScreen(Screen):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.pdf_text = ""
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=C["panel"], pady=14)
        hdr.pack(fill="x")
        row = tk.Frame(hdr, bg=C["panel"])
        row.pack()
        tk.Label(row, text="STEP 2  —  OPEN PDF",
                 font=("Courier",11,"bold"), bg=C["panel"], fg=C["accent"]).pack(side="left",padx=20)
        self.ws_lbl = tk.Label(row, text="● WS",
                                font=("Courier",9), bg=C["panel"], fg=C["muted"])
        self.ws_lbl.pack(side="right", padx=20)

        pick = tk.Frame(self, bg=C["card"], padx=20, pady=16)
        pick.pack(fill="x", padx=20, pady=(14,0))
        self.file_lbl = tk.Label(pick, text="No file selected",
                                  font=("Courier",10), bg=C["card"],
                                  fg=C["muted"], anchor="w")
        self.file_lbl.pack(side="left", fill="x", expand=True)
        tk.Button(pick, text="📂  BROWSE PDF",
                  font=("Courier",10,"bold"),
                  bg=C["accent"], fg=C["bg"],
                  relief="flat", padx=14, pady=8,
                  cursor="hand2", command=self._load).pack(side="right")

        prev = tk.Frame(self, bg=C["bg"])
        prev.pack(fill="both", expand=True, padx=20, pady=(8,0))
        tk.Label(prev, text="EXTRACTED TEXT", font=("Courier",8),
                 bg=C["bg"], fg=C["muted"]).pack(anchor="w")

        wrap = tk.Frame(prev, bg=C["border"], padx=1, pady=1)
        wrap.pack(fill="both", expand=True, pady=(4,0))
        self.textbox = tk.Text(wrap, bg=C["panel"], fg=C["text"],
                                font=("Courier",10), relief="flat",
                                wrap="word", padx=12, pady=10,
                                insertbackground=C["accent"])
        sb = tk.Scrollbar(wrap, command=self.textbox.yview,
                           bg=C["border"], troughcolor=C["bg"])
        self.textbox.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.textbox.pack(fill="both", expand=True)

        bot = tk.Frame(self, bg=C["panel"], pady=10)
        bot.pack(fill="x", pady=(6,0))
        self.count_lbl = tk.Label(bot, text="0 chars",
                                   font=("Courier",9), bg=C["panel"], fg=C["muted"])
        self.count_lbl.pack(side="left", padx=20)
        tk.Button(bot, text="START READING  →",
                  font=("Courier",12,"bold"),
                  bg=C["green"], fg=C["bg"],
                  relief="flat", padx=20, pady=10,
                  cursor="hand2", command=self._start).pack(side="right", padx=20)

    def _load(self):
        if not PDF_AVAILABLE:
            messagebox.showwarning("Missing", "pip install PyMuPDF")
            return
        path = filedialog.askopenfilename(filetypes=[("PDF","*.pdf")])
        if not path: return
        try:
            doc = fitz.open(path)
            text = "".join(p.get_text() for p in doc)
            doc.close()
            self.pdf_text = text
            self.textbox.delete("1.0", tk.END)
            self.textbox.insert(tk.END, text)
            fname = path.replace("\\","/").split("/")[-1]
            self.file_lbl.config(text=f"✔  {fname}", fg=C["green"])
            self.count_lbl.config(text=f"{len(text)} chars")
            self.app.ws_send({"cmd":"set_total","total":len(text)})
        except Exception as e:
            messagebox.showerror("PDF Error", str(e))

    def _start(self):
        if not self.pdf_text:
            messagebox.showwarning("No PDF", "Load a PDF first.")
            return
        self.app.pdf_text = self.pdf_text
        self.app.go_to_reading()

    def set_ws(self, ok):
        self.ws_lbl.config(
            text="● WS Connected" if ok else "● WS Disconnected",
            fg=C["green"] if ok else C["red"])

# ─────────────────────────────────────────
# SCREEN 4 — READING
# ─────────────────────────────────────────
class ReadingScreen(Screen):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.text = ""
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=C["panel"], pady=12)
        hdr.pack(fill="x")
        hrow = tk.Frame(hdr, bg=C["panel"])
        hrow.pack()
        tk.Label(hrow, text="STEP 3  —  READING",
                 font=("Courier",11,"bold"), bg=C["panel"], fg=C["accent"]).pack(side="left",padx=20)
        tk.Button(hrow, text="← Back",
                  font=("Courier",9), bg=C["card"], fg=C["muted"],
                  relief="flat", padx=8, pady=4,
                  command=self.app.go_to_pdf).pack(side="right", padx=20)

        main = tk.Frame(self, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=16, pady=10)

        # LEFT panel
        left = tk.Frame(main, bg=C["card"], padx=20, pady=20, width=190)
        left.pack(side="left", fill="y", padx=(0,10))
        left.pack_propagate(False)

        tk.Label(left, text="BRAILLE CELL", font=("Courier",8),
                 bg=C["card"], fg=C["muted"]).pack()
        tk.Frame(left, bg=C["bg"], height=6).pack()
        self.cell = BrailleDisplay(left, size=90)
        self.cell.pack()
        tk.Frame(left, bg=C["bg"], height=10).pack()
        self.char_lbl = tk.Label(left, text="—", font=("Georgia",38,"bold"),
                                  bg=C["card"], fg=C["text"])
        self.char_lbl.pack()
        self.bits_lbl = tk.Label(left, text="000000", font=("Courier",12),
                                  bg=C["card"], fg=C["accent"])
        self.bits_lbl.pack()
        tk.Frame(left, bg=C["border"], height=1).pack(fill="x", pady=10)
        self.pos_lbl  = tk.Label(left, text="pos: 0",    font=("Courier",9), bg=C["card"], fg=C["muted"])
        self.hex_lbl  = tk.Label(left, text="byte: 0x00",font=("Courier",9), bg=C["card"], fg=C["muted"])
        self.pos_lbl.pack()
        self.hex_lbl.pack()

        # RIGHT panel
        right = tk.Frame(main, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="TEXT", font=("Courier",8), bg=C["bg"], fg=C["muted"]).pack(anchor="w")
        wrap = tk.Frame(right, bg=C["border"], padx=1, pady=1)
        wrap.pack(fill="both", expand=True, pady=(4,0))
        self.tv = tk.Text(wrap, bg=C["panel"], fg=C["text"],
                           font=("Courier",12), relief="flat",
                           wrap="word", padx=12, pady=10, state="disabled")
        sb = tk.Scrollbar(wrap, command=self.tv.yview,
                           bg=C["border"], troughcolor=C["bg"])
        self.tv.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tv.pack(fill="both", expand=True)
        self.tv.tag_configure("hi", background=C["accent"], foreground=C["bg"])
        self.tv.tag_configure("done", foreground="#3a3d45")

        # Progress
        pf = tk.Frame(self, bg=C["bg"], pady=4)
        pf.pack(fill="x", padx=16)
        self.pcanv = tk.Canvas(pf, height=6, bg=C["border"], highlightthickness=0)
        self.pcanv.pack(fill="x")
        self.pbar = self.pcanv.create_rectangle(0,0,0,6, fill=C["accent"], outline="")

        # Controls
        bot = tk.Frame(self, bg=C["panel"], pady=10)
        bot.pack(fill="x")
        self.sim_btn = tk.Button(bot, text="▶  SIMULATE GLOVE",
                                  font=("Courier",11,"bold"),
                                  bg=C["green"], fg=C["bg"],
                                  relief="flat", padx=18, pady=8,
                                  cursor="hand2", command=self._toggle_sim)
        self.sim_btn.pack(side="left", padx=16)
        tk.Button(bot, text="⟳ RESET",
                  font=("Courier",10), bg=C["card"], fg=C["muted"],
                  relief="flat", padx=12, pady=8,
                  cursor="hand2", command=self._reset).pack(side="left")
        self.status_lbl = tk.Label(bot, text="Ready.", font=("Courier",9),
                                    bg=C["panel"], fg=C["muted"])
        self.status_lbl.pack(side="right", padx=16)

    def load_text(self, text):
        self.text = text
        self.tv.config(state="normal")
        self.tv.delete("1.0", tk.END)
        self.tv.insert(tk.END, text)
        self.tv.config(state="disabled")
        self._update(0)

    def update_position(self, pos):
        if not self.text: return
        pos = max(0, min(pos, len(self.text)-1))
        ch = self.text[pos]
        bits = char_to_braille_bits(ch)
        self.cell.set_char(ch)
        self.char_lbl.config(text=ch if ch.strip() else "␣")
        self.bits_lbl.config(text=format(bits,'06b'))
        self.pos_lbl.config(text=f"pos: {pos}")
        self.hex_lbl.config(text=f"byte: 0x{bits:02X}")
        self.pcanv.update_idletasks()
        w = self.pcanv.winfo_width()
        self.pcanv.coords(self.pbar, 0, 0, w*(pos+1)/len(self.text), 6)
        self._update(pos)
        self.status_lbl.config(text=f"Char {pos+1}/{len(self.text)}  '{ch}'")
        if self.app.serial_conn and self.app.serial_conn.is_open:
            try: self.app.serial_conn.write(bytes([bits]))
            except: pass

    def _update(self, pos):
        self.tv.config(state="normal")
        self.tv.tag_remove("hi","1.0",tk.END)
        self.tv.tag_remove("done","1.0",tk.END)
        if pos > 0:
            self.tv.tag_add("done","1.0",f"1.0+{pos}c")
        self.tv.tag_add("hi",f"1.0+{pos}c",f"1.0+{pos+1}c")
        self.tv.see(f"1.0+{pos}c")
        self.tv.config(state="disabled")

    def _toggle_sim(self):
        if self.sim_btn.cget("text").startswith("▶"):
            self.sim_btn.config(text="■  STOP SIM", bg=C["red"], fg="white")
            self.app.ws_send({"cmd":"start_sim"})
        else:
            self.sim_btn.config(text="▶  SIMULATE GLOVE", bg=C["green"], fg=C["bg"])
            self.app.ws_send({"cmd":"stop_sim"})

    def _reset(self):
        self.sim_btn.config(text="▶  SIMULATE GLOVE", bg=C["green"], fg=C["bg"])
        self.app.ws_send({"cmd":"reset"})
        self._update(0)

    def on_done(self):
        self.sim_btn.config(text="▶  SIMULATE GLOVE", bg=C["green"], fg=C["bg"])
        self.status_lbl.config(text="✔ Complete! Full text read.", fg=C["green"])

# ─────────────────────────────────────────
# APP CONTROLLER
# ─────────────────────────────────────────
class BraillieApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Braill'ie")
        self.root.geometry("820x560")
        self.root.configure(bg=C["bg"])

        self.pdf_text   = ""
        self.serial_conn= None
        self.ws         = None
        self.ws_loop    = None
        self._ws_queue  = []

        self.s_welcome   = WelcomeScreen(self.root, self.go_to_calibrate)
        self.s_calibrate = CalibrateScreen(self.root, self)
        self.s_pdf       = PDFScreen(self.root, self)
        self.s_reading   = ReadingScreen(self.root, self)

        self.s_welcome.show()
        self._start_ws()

    def go_to_calibrate(self):
        self.s_welcome.hide()
        self.s_calibrate.show()

    def go_to_pdf(self):
        self.s_calibrate.hide()
        self.s_reading.hide()
        self.s_pdf.show()

    def go_to_reading(self):
        self.s_pdf.hide()
        self.s_reading.load_text(self.pdf_text)
        self.s_reading.show()

    # WebSocket
    def _start_ws(self):
        if not WS_AVAILABLE: return
        threading.Thread(target=self._ws_thread, daemon=True).start()

    def _ws_thread(self):
        self.ws_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.ws_loop)
        self.ws_loop.run_until_complete(self._ws_run())

    async def _ws_run(self):
        while True:
            try:
                async with websockets.connect("ws://localhost:8765") as ws:
                    self.ws = ws
                    self.root.after(0, lambda: self.s_pdf.set_ws(True))
                    while self._ws_queue:
                        await ws.send(json.dumps(self._ws_queue.pop(0)))
                    async for msg in ws:
                        self.root.after(0, self._on_msg, json.loads(msg))
            except Exception:
                self.ws = None
                self.root.after(0, lambda: self.s_pdf.set_ws(False))
                await asyncio.sleep(2)

    def _on_msg(self, data):
        t = data.get("type")
        if t == "position":
            self.s_reading.update_position(data["position"])
        elif t == "done":
            self.s_reading.on_done()

    def ws_send(self, msg):
        if self.ws and self.ws_loop:
            asyncio.run_coroutine_threadsafe(
                self.ws.send(json.dumps(msg)), self.ws_loop)
        else:
            self._ws_queue.append(msg)

# ─────────────────────────────────────────
# ENTRY
# ─────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = BraillieApp(root)
    root.mainloop()
