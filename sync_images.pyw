import os
import re
from bs4 import BeautifulSoup
import customtkinter as ctk

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class ImageSyncApp(ctk.CTk):
    EXCLUDE_FOLDERS = {
        "contact",
        "over-mij",
        "projecten",
        "icons",
        "menu",
        "other",
        "favicon",
    }

    # Custom folder-to-HTML mapping for subprojects or shortened names
    FOLDER_ALIASES = {
        "schilder": "schilderijen.html",
        "schilderijen": "schilderijen.html",
        "boeken": "boeken.html",
        "muurschildering": "kuleuven_muurschildering.html",
    }

    def __init__(self):
        super().__init__()

        self.title("Portfolio Image Auto-Sync")
        self.geometry("620x480")
        self.resizable(True, True)

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.images_dir = os.path.join(self.base_dir, "images")

        self.create_widgets()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.header_label = ctk.CTkLabel(
            self,
            text="Portfolio Gallery Image Auto-Sync",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.header_label.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="ew")

        self.log_textbox = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=12), wrap="word"
        )
        self.log_textbox.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        self.sync_button = ctk.CTkButton(
            self,
            text="Sync All Galleries",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self.run_auto_sync,
        )
        self.sync_button.grid(row=2, column=0, padx=20, pady=(10, 15), sticky="ew")

        self.log("Ready. Click 'Sync All Galleries' to update HTML pages.")

    def log(self, text):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", text + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def clean_alt_text(self, filename):
        name, _ = os.path.splitext(filename)
        cleaned = re.sub(r"^\d{4}[_-]?", "", name)
        cleaned = re.sub(r"^IMG[_-]?", "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace("_", " ").replace("-", " ").strip()
        return cleaned.capitalize() if cleaned else "Illustratie"

    def discover_image_folders(self):
        """Scans images/ recursively for subfolders and maps them to HTML pages."""
        matched_map = {}

        if not os.path.exists(self.images_dir):
            self.log("[ERROR] 'images/' folder directory not found.")
            return matched_map

        for root_path, dirs, _ in os.walk(self.images_dir):
            for dir_name in dirs:
                dir_lower = dir_name.lower()

                if dir_lower in self.EXCLUDE_FOLDERS:
                    continue

                folder_full_path = os.path.join(root_path, dir_name)
                rel_folder_path = os.path.relpath(
                    folder_full_path, self.base_dir
                ).replace("\\", "/")

                # Check alias mapping first, fallback to exact name match
                target_html = self.FOLDER_ALIASES.get(dir_lower, f"{dir_name}.html")
                target_html_path = os.path.join(self.base_dir, target_html)

                if os.path.exists(target_html_path):
                    matched_map[target_html] = rel_folder_path

        return matched_map

    def create_img_tag(self, soup, img_rel_path, alt_text):
        img_tag = soup.new_tag("img")
        img_tag["src"] = img_rel_path
        img_tag["data-src"] = img_rel_path
        img_tag["alt"] = alt_text
        img_tag["loading"] = "lazy"
        return img_tag

    def run_auto_sync(self):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

        self.log("--- Scanning images/ directory for page folders ---")
        folder_map = self.discover_image_folders()

        if not folder_map:
            self.log("[INFO] No matching HTML and image folder pairs found.")
            return

        for html_file, rel_img_dir in folder_map.items():
            self.log(f"  • {rel_img_dir}  ==>  {html_file}")

        self.log("")
        updated_count = 0
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

        for html_file, rel_img_dir in folder_map.items():
            html_path = os.path.join(self.base_dir, html_file)
            img_dir_path = os.path.join(self.base_dir, rel_img_dir)

            try:
                with open(html_path, "r", encoding="utf-8") as f:
                    soup = BeautifulSoup(f.read(), "html.parser")
            except Exception as e:
                self.log(f"[ERROR] Could not read {html_file}: {e}")
                continue

            # Target gallery container without touching sibling text elements
            container = soup.find(id="image-grid-container") or soup.find(id="gallery")

            if not container:
                self.log(f"[SKIP] No valid gallery container in {html_file}")
                continue

            container["id"] = "image-grid-container"
            container.clear()

            try:
                image_files = sorted(
                    [
                        f
                        for f in os.listdir(img_dir_path)
                        if os.path.splitext(f)[1].lower() in valid_extensions
                    ],
                    reverse=True,
                )
            except Exception as e:
                self.log(f"[ERROR] Could not read directory {rel_img_dir}: {e}")
                continue

            for img_file in image_files:
                img_rel_path = f"{rel_img_dir}/{img_file}"
                alt_text = self.clean_alt_text(img_file)
                img_tag = self.create_img_tag(soup, img_rel_path, alt_text)
                container.append(img_tag)
                container.append("\n                ")

            if container.contents:
                container.contents[-1] = "\n            "

            try:
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(str(soup))
                self.log(
                    f"[SUCCESS] {html_file} updated with {len(image_files)} images from '{rel_img_dir}'."
                )
                updated_count += 1
            except Exception as e:
                self.log(f"[ERROR] Could not write updates to {html_file}: {e}")

        self.log(f"\n--- Batch Sync Completed: {updated_count} file(s) updated ---")


if __name__ == "__main__":
    app = ImageSyncApp()
    app.mainloop()