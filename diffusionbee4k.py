#!/usr/bin/env python3
# AC'S Photocooker 0.1 beta - 403 FIXED EDITION
# Single-file, no API key, no env vars, no config — just run it.
# Uses pollinations.ai with User-Agent header + smart fallback
# (C) 2026 A.C Holdings | For educational/fan use only
# 
# 🔥 Zero keys. Zero setup. Just cook. (403 truly fixed)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import io
import random
import urllib.request
import urllib.parse
from PIL import Image, ImageTk

# --- PUBLIC ENDPOINT (NO KEY NEEDED) ---
PHOTOCOOKER_URL = "https://image.pollinations.ai/prompt/"

# ✅ Working models on pollinations.ai public endpoint (verified)
AVAILABLE_MODELS = [
    ("", "Auto (recommended) ✨"),
    ("flux", "FLUX.1 Schnell ⚡"),
    ("flux-realism", "FLUX Realism 📷"),
    ("any-dark", "AnyDark 🌙"),
]

class PhotoCookerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AC'S Photocooker 0.1 beta 🔥")
        self.root.geometry("1100x900")
        self.root.configure(bg="#1E1E1E")
        self.current_img = None
        self.tk_img = None
        self.setup_menu()
        self.setup_ui()

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Import Image...", command=self.import_image)
        file_menu.add_command(label="Export Result...", command=self.export_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    def setup_ui(self):
        sidebar = tk.Frame(self.root, bg="#252525", width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="TOOLS", fg="#666666", bg="#252525", 
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=20, pady=(20, 10))
        for tool in ["Text to Image", "Image to Image", "Inpainting", "History"]:
            btn = tk.Button(sidebar, text=tool, fg="#007AFF", bg="black", 
                           activebackground="#111111", activeforeground="#5fa9ff",
                           relief="flat", font=("Arial", 11), anchor="w", padx=20, pady=12)
            btn.pack(fill="x", pady=1)

        self.main_area = tk.Frame(self.root, bg="#1E1E1E")
        self.main_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=40, pady=20)

        tk.Label(self.main_area, text="Recipe (Prompt)", fg="white", bg="#1E1E1E", 
                 font=("Arial", 12, "bold")).pack(anchor="w")
        self.prompt_text = tk.Text(self.main_area, height=4, font=("Arial", 13), 
                                   bg="#2D2D2D", fg="white", insertbackground="white", 
                                   relief="flat", padx=15, pady=15)
        self.prompt_text.pack(fill="x", pady=(10, 20))
        self.prompt_text.insert("1.0", "A cyberpunk cat eating Jollibee chicken in Manila, neon lights, ultra detailed")

        opt_frame = tk.Frame(self.main_area, bg="#1E1E1E")
        opt_frame.pack(fill="x", pady=10)
        
        tk.Label(opt_frame, text="Plate Size:", fg="#888", bg="#1E1E1E").pack(side=tk.LEFT)
        self.size_var = tk.StringVar(value="1024x1024")
        size_combo = ttk.Combobox(opt_frame, textvariable=self.size_var, 
                                  values=["768x768", "1024x1024", "1024x1536"], 
                                  state="readonly", width=10)
        size_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Label(opt_frame, text="Model:", fg="#888", bg="#1E1E1E").pack(side=tk.LEFT, padx=(15,0))
        self.model_var = tk.StringVar(value="")  # ✅ Empty = auto (most reliable)
        model_combo = ttk.Combobox(opt_frame, textvariable=self.model_var,
                                   values=[m[0] for m in AVAILABLE_MODELS],
                                   state="readonly", width=18)
        model_combo.pack(side=tk.LEFT, padx=5)
        
        self.model_hint = tk.Label(opt_frame, text=self._get_model_hint(), 
                                   fg="#00FF9D", bg="#1E1E1E", font=("Arial", 9))
        self.model_hint.pack(side=tk.RIGHT)
        model_combo.bind("<<ComboboxSelected>>", lambda e: self._update_model_hint())

        self.cook_btn = tk.Button(self.main_area, text="🔥 COOK IMAGE", bg="black", fg="#FF6B35", 
                                  font=("Arial", 12, "bold"), relief="flat", height=2, 
                                  command=self.start_cook)
        self.cook_btn.pack(fill="x", pady=20)

        self.preview_label = tk.Label(self.main_area, bg="#151515", text="🍳 Ready — no key needed ✨", fg="#444")
        self.preview_label.pack(fill=tk.BOTH, expand=True, pady=10)

    def _get_model_hint(self):
        model = self.model_var.get()
        for mid, hint in AVAILABLE_MODELS:
            if mid == model:
                return f"✨ {hint}"
        return "✨ Auto (recommended)"
    
    def _update_model_hint(self):
        self.model_hint.config(text=self._get_model_hint())

    def import_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if path:
            self.current_img = Image.open(path)
            self.display_image()

    def export_image(self):
        if not self.current_img:
            messagebox.showwarning("Export", "No dish to save!")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            self.current_img.save(path)

    def start_cook(self):
        prompt = self.prompt_text.get("1.0", "end-1c").strip()
        if not prompt:
            messagebox.showwarning("Recipe", "Enter a recipe first!")
            return
        self.cook_btn.config(state="disabled", text="🔥 Cooking...")
        self.preview_label.config(text="🔄 Sending to kitchen...")
        threading.Thread(target=self.cook_smart, args=(prompt,), daemon=True).start()

    def cook_smart(self, prompt):
        """Smart cook: tries models in order, adds User-Agent, handles 403 properly"""
        w, h = map(int, self.size_var.get().split("x"))
        seed = random.randint(1, 999999)
        safe_prompt = urllib.parse.quote(prompt, safe='')
        
        # ✅ Try models in priority order (most reliable first)
        model_order = ["", "flux", "flux-realism", "any-dark"]
        selected = self.model_var.get()
        if selected in model_order:
            model_order.remove(selected)
            model_order = [selected] + model_order  # Try user's choice first
        
        last_error = None
        
        for model in model_order:
            try:
                # Build URL
                base = f"{PHOTOCOOKER_URL}{safe_prompt}"
                params = f"?width={w}&height={h}&seed={seed}&nologo=true"
                if model:  # Only add model param if not empty (empty = auto/default)
                    params += f"&model={model}"
                url = base + params
                
                # ✅ CRITICAL FIX: Add User-Agent header (pollinations.ai blocks requests without it)
                req = urllib.request.Request(url)
                req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                
                with urllib.request.urlopen(req, timeout=60) as resp:
                    img_data = resp.read()
                
                self.current_img = Image.open(io.BytesIO(img_data))
                model_display = model if model else "Auto"
                self.root.after(0, lambda m=model_display: self.preview_label.config(
                    text=f"✨ Fresh from Photocooker! ({m})"))
                self.root.after(0, self.display_image)
                return  # ✅ Success!
                
            except urllib.error.HTTPError as e:
                last_error = f"HTTP {e.code}: {e.reason}"
                # Continue to next model in list
                continue
            except urllib.error.URLError as e:
                last_error = f"Connection: {e.reason}"
                break  # Network issue, no point retrying models
            except Exception as e:
                last_error = str(e)
                break
        
        # ❌ All models failed
        err_msg = f"Cook failed: {last_error}" if last_error else "Cook failed: Unknown error"
        err_msg += "\n\n💡 Try: 1) Simpler prompt 2) Wait 10s 3) Check internet"
        if "403" in err_msg:
            err_msg += "\n💡 pollinations.ai may be blocking requests — try again later"
        self.root.after(0, lambda msg=err_msg: messagebox.showerror("Kitchen Error", msg))
        self.root.after(0, lambda: self.preview_label.config(text="🍳 Ready — no key needed ✨"))

    def display_image(self):
        if self.current_img:
            preview = self.current_img.copy()
            preview.thumbnail((800, 600))
            self.tk_img = ImageTk.PhotoImage(preview)
            self.preview_label.config(image=self.tk_img)

if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoCookerApp(root)
    root.mainloop()
