import os
import customtkinter as ctk
from bs4 import BeautifulSoup

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}

class AutoGallerySyncApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Auto Gallery Sync Tool")
        self.geometry("680x520")
        self.minsize(580, 420)

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.images_dir = os.path.join(self.base_dir, "images")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header Frame
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="Dynamic Folder-to-HTML Synchronizer", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.title_label.pack(padx=15, pady=12, anchor="w")

        # Action Button Frame
        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.sync_button = ctk.CTkButton(
            self.action_frame, 
            text="Auto-Detect & Sync Galleries", 
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.run_auto_sync
        )
        self.sync_button.pack(padx=15, pady=12, fill="x")

        # Log Output Console
        self.log_textbox = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_textbox.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")

        self.log("Ready. Click button to scan 'images/' and match root HTML files...\n")

    def log(self, message):
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")

    def discover_image_folders(self):
        """Recursively scan images/ and return a dict mapping html_name -> relative_folder_path."""
        matched_map = {}

        if not os.path.exists(self.images_dir):
            self.log("[ERROR] 'images/' directory not found in root.")
            return matched_map

        for root_path, dirs, _ in os.walk(self.images_dir):
            for dir_name in dirs:
                folder_full_path = os.path.join(root_path, dir_name)
                
                # Relative path from root dir (e.g. "images/projecten/boeken")
                rel_folder_path = os.path.relpath(folder_full_path, self.base_dir).replace("\\", "/")
                
                # Corresponding expected HTML filename (e.g. "boeken.html")
                target_html = f"{dir_name}.html"
                target_html_path = os.path.join(self.base_dir, target_html)

                if os.path.exists(target_html_path):
                    matched_map[target_html] = rel_folder_path

        return matched_map

    def run_auto_sync(self):
        self.log("--- Starting Dynamic Folder Discovery ---")
        matches = self.discover_image_folders()

        if not matches:
            self.log("[WARNING] No matching HTML files found for subfolders in 'images/'.")
            self.log("Ensure folder names match HTML filenames (e.g., 'images/schetsen' -> 'schetsen.html').\n")
            return

        self.log(f"Discovered {len(matches)} folder-to-HTML pairings:")
        for html_file, folder in matches.items():
            self.log(f"  • {folder}  ==>  {html_file}")
        self.log("")

        total_updated = 0
        for html_filename, img_folder_path in matches.items():
            full_html_path = os.path.join(self.base_dir, html_filename)
            full_img_folder = os.path.join(self.base_dir, img_folder_path)

            images = sorted([
                f for f in os.listdir(full_img_folder)
                if os.path.splitext(f)[1].lower() in VALID_EXTENSIONS
            ])

            with open(full_html_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")

            gallery_div = soup.find(id="gallery")
            if not gallery_div:
                self.log(f"[SKIP] <div id='gallery'></div> missing in {html_filename}")
                continue

            gallery_div.clear()
            for img_filename in images:
                rel_img_path = f"{img_folder_path}/{img_filename}"
                clean_alt = os.path.splitext(img_filename)[0].replace("-", " ").replace("_", " ").capitalize()

                img_tag = soup.new_tag("img", **{
                    "src": rel_img_path,
                    "alt": clean_alt,
                    "loading": "lazy"
                })
                gallery_div.append(img_tag)

            with open(full_html_path, "w", encoding="utf-8") as f:
                f.write(soup.prettify())

            self.log(f"[SUCCESS] {html_filename} updated with {len(images)} images.")
            total_updated += 1

        self.log(f"\n--- Batch Sync Finished: {total_updated} page(s) updated ---\n")

if __name__ == "__main__":
    app = AutoGallerySyncApp()
    app.mainloop()