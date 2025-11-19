import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, Scrollbar
import customtkinter as ctk


class ImageSelectorApp(ctk.CTk):
    """A clean and logical CustomTkinter UI for managing portfolio images."""

    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("Portfolio Image Manager")
        self.geometry("950x700")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.base_dir = None
        self.available_images = []
        self.selected_images = []

        # --- Layout Config ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Top Controls ---
        self.top_frame = ctk.CTkFrame(self, corner_radius=10)
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        self.top_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.top_frame, text="Portfolio Folder:", font=('Inter', 12, 'bold')).grid(row=0, column=0, sticky="w", padx=5)
        self.folder_label = ctk.CTkLabel(self.top_frame, text="No folder selected", font=('Inter', 12))
        self.folder_label.grid(row=0, column=1, sticky="w", padx=5)

        ctk.CTkButton(self.top_frame, text="Browse Folder", command=self.browse_folder, width=160).grid(row=0, column=2, padx=10)

        ctk.CTkLabel(self.top_frame, text="Link Prefix (optional):", font=('Inter', 12, 'bold')).grid(row=1, column=0, sticky="w", padx=5, pady=(10, 0))
        self.prefix_entry = ctk.CTkEntry(self.top_frame, placeholder_text="e.g. images/project/", width=350)
        self.prefix_entry.grid(row=1, column=1, sticky="w", padx=5, pady=(10, 0))

        # --- Middle: Image Lists ---
        self.list_frame = ctk.CTkFrame(self, corner_radius=10)
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.list_frame.grid_columnconfigure(0, weight=1)
        self.list_frame.grid_columnconfigure(2, weight=1)
        self.list_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.list_frame, text="Available Images", font=('Inter', 12, 'bold')).grid(row=0, column=0, pady=(10, 0))
        ctk.CTkLabel(self.list_frame, text="Selected Images", font=('Inter', 12, 'bold')).grid(row=0, column=2, pady=(10, 0))

        # --- Sorting Controls ---
        sort_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        sort_frame.grid(row=0, column=3, padx=(10, 0))
        ctk.CTkLabel(sort_frame, text="Sort:", font=('Inter', 11, 'bold')).pack(side="left", padx=(0, 5))
        ctk.CTkButton(sort_frame, text="A–Z", width=60, command=lambda: self.sort_selected("az")).pack(side="left", padx=2)
        ctk.CTkButton(sort_frame, text="Z–A", width=60, command=lambda: self.sort_selected("za")).pack(side="left", padx=2)
        ctk.CTkButton(sort_frame, text="By Folder", width=90, command=lambda: self.sort_selected("folder")).pack(side="left", padx=2)
        ctk.CTkButton(sort_frame, text="Manual", width=80, command=lambda: self.sort_selected("manual")).pack(side="left", padx=2)

        # --- Available Listbox ---
        self.available_listbox = tk.Listbox(
            self.list_frame, selectmode=tk.EXTENDED, font=('Inter', 10),
            bg="#2b2b2b", fg="white", selectbackground="#1f6aa5", relief=tk.FLAT
        )
        self.available_listbox.grid(row=1, column=0, sticky="nsew", padx=(15, 0), pady=10)
        Scrollbar(self.list_frame, command=self.available_listbox.yview).grid(row=1, column=1, sticky="ns", pady=10)

        # --- Middle Buttons ---
        button_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        button_frame.grid(row=1, column=1, sticky="ns", padx=10)
        ctk.CTkButton(button_frame, text="Add →", command=self.add_image, width=100).pack(pady=(20, 5))
        ctk.CTkButton(button_frame, text="← Remove", command=self.remove_image, width=100).pack(pady=5)

        # --- Selected Listbox ---
        self.selected_listbox = tk.Listbox(
            self.list_frame, selectmode=tk.EXTENDED, font=('Inter', 10),
            bg="#2b2b2b", fg="white", selectbackground="#1f6aa5", relief=tk.FLAT
        )
        self.selected_listbox.grid(row=1, column=2, sticky="nsew", padx=(0, 15), pady=10)
        self.selected_listbox.bind("<B1-Motion>", self.on_drag_motion)
        self.selected_listbox.bind("<ButtonRelease-1>", self.on_drag_release)

        # --- Output Section ---
        self.output_frame = ctk.CTkFrame(self, corner_radius=10)
        self.output_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(5, 15))
        self.output_frame.grid_rowconfigure(1, weight=1)
        self.output_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.output_frame, text="Generated JavaScript Code", font=('Inter', 12, 'bold')).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))
        self.output_text = ctk.CTkTextbox(self.output_frame, height=120, font=('Consolas', 10))
        self.output_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # --- Action Buttons ---
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=3, column=0, pady=(0, 15))
        ctk.CTkButton(self.bottom_frame, text="Generate Code", command=self.generate_code, fg_color="#1f6aa5").pack(side="left", padx=10)
        ctk.CTkButton(self.bottom_frame, text="Copy Code", command=self.copy_code, fg_color="#00774f").pack(side="left", padx=10)
        ctk.CTkButton(self.bottom_frame, text="Clear Output", command=lambda: self.output_text.delete("1.0", "end"), fg_color="#A8324C").pack(side="left", padx=10)

    # --- Core Logic ---

    def browse_folder(self):
        self.base_dir = filedialog.askdirectory(title="Select Portfolio Folder")
        if not self.base_dir:
            return
        self.folder_label.configure(text=self.base_dir)
        self.populate_available_listbox(self.base_dir)
        script_path = os.path.join(self.base_dir, 'script.js')
        if os.path.exists(script_path):
            self.load_images_from_script(script_path)

    def populate_available_listbox(self, folder_path):
        self.available_listbox.delete(0, tk.END)
        self.available_images.clear()
        for root, _, files in os.walk(folder_path):
            for filename in files:
                if re.search(r'\.(jpg|jpeg|png|gif|webp)$', filename, re.IGNORECASE):
                    rel_path = os.path.relpath(os.path.join(root, filename), folder_path).replace("\\", "/")
                    self.available_images.append(rel_path)
        for img in sorted(self.available_images):
            self.available_listbox.insert(tk.END, img)

    def load_images_from_script(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.search(r"const\s+images\s*=\s*\[([\s\S]*?)\];", content)
            if match:
                found = re.findall(r"['\"]([^'\"]+\.(?:jpg|jpeg|png|gif|webp))['\"]", match.group(1), re.IGNORECASE)
                self.selected_images = [i for i in found if i in self.available_images]
                self.update_selected_listbox()
                if self.selected_images:
                    messagebox.showinfo("Loaded", f"{len(self.selected_images)} images loaded from script.js.")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot read script.js: {e}")

    def update_selected_listbox(self):
        self.selected_listbox.delete(0, tk.END)
        for img in self.selected_images:
            self.selected_listbox.insert(tk.END, img)

    def add_image(self):
        for i in self.available_listbox.curselection():
            item = self.available_listbox.get(i)
            if item not in self.selected_images:
                self.selected_images.append(item)
        self.update_selected_listbox()

    def remove_image(self):
        """Allow multi-selection removal just like the available list."""
        selected_indices = list(self.selected_listbox.curselection())
        if not selected_indices:
            return
        for index in reversed(selected_indices):
            self.selected_images.pop(index)
        self.update_selected_listbox()

    def on_drag_motion(self, event):
        index = self.selected_listbox.nearest(event.y)
        current = self.selected_listbox.curselection()
        if not current or index == current[0]:
            return
        item = self.selected_images.pop(current[0])
        self.selected_images.insert(index, item)
        self.update_selected_listbox()
        self.selected_listbox.selection_set(index)

    def on_drag_release(self, event):
        pass

    def sort_selected(self, mode):
        """Sort selected images by the chosen mode."""
        if not self.selected_images:
            return

        if mode == "az":
            self.selected_images.sort(key=lambda x: x.lower())
        elif mode == "za":
            self.selected_images.sort(key=lambda x: x.lower(), reverse=True)
        elif mode == "folder":
            self.selected_images.sort(key=lambda x: (os.path.dirname(x).lower(), os.path.basename(x).lower()))
        elif mode == "manual":
            # keep current order
            pass

        self.update_selected_listbox()

    def generate_code(self):
        if not self.selected_images:
            messagebox.showwarning("No Images", "Please select images first.")
            return
        prefix = self.prefix_entry.get().strip()
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        code = "const images = [\n" + "\n".join(f"    '{prefix}{img}'," for img in self.selected_images) + "\n];"
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", code)

    def copy_code(self):
        """Copy the generated code to clipboard."""
        code = self.output_text.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Empty", "No code to copy.")
            return
        self.clipboard_clear()
        self.clipboard_append(code)  # spell checker problems in VS Code
        self.update()


if __name__ == "__main__":
    app = ImageSelectorApp()
    app.mainloop()
