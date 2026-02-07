import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

class PortfolioUpdater(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("HTML Portfolio Image Updater")
        self.geometry("950x900")
        ctk.set_appearance_mode("Dark")
        
        self.html_dir = os.path.dirname(os.path.abspath(__file__))
        self.img_dir = None
        self.selected_images = []

        # --- UI Layout ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Top Section: Folders
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        
        ctk.CTkLabel(self.top_frame, text="1. HTML Folder:", font=("", 12, "bold")).grid(row=0, column=0, padx=10, sticky="w")
        self.html_label = ctk.CTkLabel(self.top_frame, text=self.html_dir, text_color="gray")
        self.html_label.grid(row=0, column=1, padx=10, sticky="w")
        ctk.CTkButton(self.top_frame, text="Change HTML Folder", command=self.browse_html, width=150).grid(row=0, column=2, padx=10, pady=5)

        ctk.CTkLabel(self.top_frame, text="2. Images Folder:", font=("", 12, "bold")).grid(row=1, column=0, padx=10, sticky="w")
        self.img_label = ctk.CTkLabel(self.top_frame, text="No folder selected", text_color="#E67E22")
        self.img_label.grid(row=1, column=1, padx=10, sticky="w")
        ctk.CTkButton(self.top_frame, text="Select Images Folder", command=self.browse_images, width=150).grid(row=1, column=2, padx=10, pady=5)

        # Middle Section: Lists
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.list_frame.grid_columnconfigure(0, weight=1)
        self.list_frame.grid_columnconfigure(2, weight=1)
        self.list_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.list_frame, text="Available Images").grid(row=0, column=0)
        sort_container = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        sort_container.grid(row=0, column=2)
        ctk.CTkButton(sort_container, text="A-Z", width=40, command=lambda: self.sort_selected("az")).pack(side="left", padx=2)
        ctk.CTkButton(sort_container, text="Z-A", width=40, command=lambda: self.sort_selected("za")).pack(side="left", padx=2)

        self.available_listbox = tk.Listbox(self.list_frame, selectmode=tk.EXTENDED, bg="#2b2b2b", fg="white", borderwidth=0, font=("Inter", 10))
        self.available_listbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        btn_mid_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        btn_mid_frame.grid(row=1, column=1)
        ctk.CTkButton(btn_mid_frame, text="Add →", width=110, command=self.add_image).pack(pady=5)
        ctk.CTkButton(btn_mid_frame, text="← Remove", width=110, command=self.remove_image).pack(pady=5)
        ctk.CTkButton(btn_mid_frame, text="Clear List", width=110, fg_color="#A8324C", hover_color="#7a2437", command=self.clear_selection).pack(pady=20)

        self.selected_listbox = tk.Listbox(self.list_frame, selectmode=tk.SINGLE, bg="#2b2b2b", fg="white", borderwidth=0, font=("Inter", 10))
        self.selected_listbox.grid(row=1, column=2, sticky="nsew", padx=10, pady=10)
        self.selected_listbox.bind("<B1-Motion>", self.on_drag_motion)

        # Output & Action Section
        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        
        # Code Generation Area
        ctk.CTkLabel(self.bottom_frame, text="Manual Code Output:", font=("", 11, "bold")).pack(pady=(5,0))
        self.output_text = ctk.CTkTextbox(self.bottom_frame, height=100, font=("Consolas", 10))
        self.output_text.pack(fill="x", padx=15, pady=5)
        
        btn_container = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        btn_container.pack(pady=10)

        ctk.CTkButton(btn_container, text="Update 'Illustraties'", fg_color="#1f6aa5", 
                      command=lambda: self.update_files(["portfolio.html", "index.html"])).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_container, text="Update 'Schetsen'", fg_color="#2c3e50", 
                      command=lambda: self.update_files(["schetsen.html"])).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_container, text="Generate & Copy Code", fg_color="#00774f", hover_color="#005c3d",
                      command=self.generate_and_copy).pack(side="left", padx=5)

    # --- Logic ---

    def browse_html(self):
        folder = filedialog.askdirectory()
        if folder: self.html_dir = folder; self.html_label.configure(text=self.html_dir)

    def browse_images(self):
        folder = filedialog.askdirectory()
        if folder:
            self.img_dir = folder
            self.img_label.configure(text=self.img_dir, text_color="white")
            self.scan_images()

    def scan_images(self):
        self.available_listbox.delete(0, tk.END)
        files = [f for f in os.listdir(self.img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
        for f in sorted(files): self.available_listbox.insert(tk.END, f)

    def add_image(self):
        for i in self.available_listbox.curselection():
            img = self.available_listbox.get(i)
            if img not in self.selected_images: self.selected_images.append(img)
        self.refresh_selected_ui()

    def remove_image(self):
        for i in reversed(self.selected_listbox.curselection()): self.selected_images.pop(i)
        self.refresh_selected_ui()

    def clear_selection(self):
        if messagebox.askyesno("Confirm", "Clear selection?"):
            self.selected_images.clear(); self.refresh_selected_ui()

    def sort_selected(self, mode):
        self.selected_images.sort(key=lambda x: x.lower(), reverse=(mode == "za"))
        self.refresh_selected_ui()

    def refresh_selected_ui(self):
        self.selected_listbox.delete(0, tk.END)
        for img in self.selected_images: self.selected_listbox.insert(tk.END, img)

    def on_drag_motion(self, event):
        index = self.selected_listbox.nearest(event.y)
        current = self.selected_listbox.curselection()
        if not current or index == current[0]: return
        item = self.selected_images.pop(current[0])
        self.selected_images.insert(index, item)
        self.refresh_selected_ui(); self.selected_listbox.selection_set(index)

    def get_path_prefix(self):
        if not self.img_dir: return "images/projecten/unknown/"
        # Logic to find path relative to 'images' or just use folder name
        folder_name = os.path.basename(self.img_dir)
        # If the parent is 'projecten', it builds 'images/projecten/name/'
        parent_name = os.path.basename(os.path.dirname(self.img_dir))
        if parent_name == "projecten":
            return f"images/projecten/{folder_name}/"
        return f"images/{folder_name}/"

    def generate_and_copy(self):
        if not self.selected_images:
            messagebox.showwarning("Warning", "No images selected.")
            return
        
        prefix = self.get_path_prefix()
        code = "\n".join([f'<img data-src="{prefix}{img}">' for img in self.selected_images])
        
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", code)
        
        self.clipboard_clear()
        self.clipboard_append(code)

    def update_files(self, filenames):
        if not self.img_dir or not self.selected_images:
            messagebox.showwarning("Warning", "Select Images folder first.")
            return

        prefix = self.get_path_prefix()
        img_tags = [f'                <img data-src="{prefix}{img}">' for img in self.selected_images]
        new_inner_html = "\n" + "\n".join(img_tags) + "\n            "
        pattern = re.compile(r'(<div[^>]*id=["\']image-grid-container["\'][^>]*>)(.*?)(</div>)', re.DOTALL | re.IGNORECASE)

        success = []
        for name in filenames:
            path = os.path.join(self.html_dir, name)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f: content = f.read()
                if pattern.search(content):
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(pattern.sub(rf'\1{new_inner_html}\3', content))
                    success.append(name)

        messagebox.showinfo("Result", f"Updated: {', '.join(success) if success else 'None'}")

if __name__ == "__main__":
    app = PortfolioUpdater()
    app.mainloop()