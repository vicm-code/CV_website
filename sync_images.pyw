import os
import re
import shutil
import tempfile
import tkinter as tk
from tkinter import filedialog

from bs4 import BeautifulSoup
from PIL import Image, ImageSequence
import customtkinter as ctk
import piexif


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

GALLERY_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
METADATA_EXTENSIONS = GALLERY_EXTENSIONS | {".tif", ".tiff", ".bmp"}
GALLERY_ID = "image-grid-container"
PAGE_IMAGE_FOLDERS = {
    "index.html": "images/index",
    "boeken.html": "images/boeken",
    "kuleuven_muurschildering.html": "images/kuleuven_muurschildering",
    "schetsen.html": "images/schetsen",
    "schilderijen.html": "images/schilderijen",
    "tour_elentrik.html": "images/tour_elentrik",
}
PROJECT_THUMBNAILS = {
    "Schilderijen": ("schilderijen.html", "images/schilderijen"),
    "Boeken": ("boeken.html", "images/boeken"),
    "Tour Elentrik": ("tour_elentrik.html", "images/tour_elentrik"),
    "KU Leuven Muurschildering": (
        "kuleuven_muurschildering.html",
        "images/kuleuven_muurschildering",
    ),
}


def strip_image_metadata(file_path):
    """Strip image metadata, replacing the original only after a successful write."""
    extension = os.path.splitext(file_path)[1].lower()
    if extension not in METADATA_EXTENSIONS:
        return False, f"Unsupported image type: {extension}"

    temp_path = None
    exif_error = None
    if extension in {".jpg", ".jpeg", ".tif", ".tiff"}:
        try:
            descriptor, temp_path = tempfile.mkstemp(
                prefix="metadata-clean-",
                suffix=extension,
                dir=os.path.dirname(os.path.abspath(file_path)),
            )
            os.close(descriptor)
            shutil.copy2(file_path, temp_path)
            piexif.remove(temp_path)
            os.replace(temp_path, file_path)
            return True, "EXIF removed losslessly"
        except Exception as error:
            exif_error = error
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            temp_path = None

    try:
        with Image.open(file_path) as image:
            image_format = image.format
            if not image_format:
                return False, "Could not determine image format"
            frames = [frame.copy() for frame in ImageSequence.Iterator(image)]
            image_info = image.info.copy()

        if not frames:
            return False, "Image contains no frames"

        save_options = {}
        if len(frames) > 1:
            save_options["save_all"] = True
            save_options["append_images"] = frames[1:]
        if image_format == "JPEG":
            if frames[0].mode not in {"RGB", "L", "CMYK"}:
                frames[0] = frames[0].convert("RGB")
            save_options["quality"] = 95
        elif image_format == "WEBP":
            save_options["quality"] = 95

        if image_format in {"GIF", "PNG"} and "transparency" in image_info:
            save_options["transparency"] = image_info["transparency"]
        if image_format == "GIF":
            if len(frames) > 1:
                save_options["duration"] = [
                    frame.info.get("duration", image_info.get("duration", 0))
                    for frame in frames
                ]
            elif "duration" in image_info:
                save_options["duration"] = image_info["duration"]
            for option in ("loop", "disposal"):
                if option in image_info:
                    save_options[option] = image_info[option]
        elif image_format == "WEBP" and len(frames) > 1:
            save_options["duration"] = [
                frame.info.get("duration", image_info.get("duration", 0))
                for frame in frames
            ]
            if "loop" in image_info:
                save_options["loop"] = image_info["loop"]

        descriptor, temp_path = tempfile.mkstemp(
            prefix="metadata-clean-",
            suffix=extension,
            dir=os.path.dirname(os.path.abspath(file_path)),
        )
        os.close(descriptor)
        frames[0].save(temp_path, format=image_format, **save_options)
        os.replace(temp_path, file_path)
        return True, "Metadata stripped"
    except Exception as error:
        if exif_error:
            return False, f"EXIF removal failed ({exif_error}); image rewrite failed ({error})"
        return False, str(error)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


class ImageSyncApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Portfolio Image Manager")
        self.geometry("1050x720")
        self.minsize(760, 560)

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.images_dir = os.path.join(self.base_dir, "images")
        self.gallery_pages = {}
        self.gallery_images = []
        self.gallery_dirty = False
        self.current_page = ""
        self.project_images = {}
        self.thumbnail_dirty = False
        self.info_visible = False

        self.create_widgets()
        self.load_gallery_pages()
        self.protocol("WM_DELETE_WINDOW", self.close_app)

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=18, pady=(14, 4), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="Portfolio Image Manager",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        self.info_button = ctk.CTkButton(
            header, text="Show info", width=90, command=self.toggle_info
        )
        self.info_button.grid(row=0, column=1, padx=(8, 0))

        self.info_label = ctk.CTkLabel(
            self,
            text=(
                "Choose a gallery, add or reorder images, edit alt text, then save. "
                "Added files are copied into the selected gallery folder. Removing "
                "an entry leaves its file intact. Enable metadata stripping to "
                "remove metadata from imported copies. Project thumbnails are "
                "managed separately below."
            ),
            justify="left",
            anchor="w",
            wraplength=950,
        )
        self.info_label.grid(row=1, column=0, padx=20, pady=(2, 8), sticky="ew")
        self.info_label.grid_remove()

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=2, column=0, padx=18, pady=6, sticky="ew")
        controls.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(controls, text="Gallery page:").grid(
            row=0, column=0, padx=(0, 8), sticky="w"
        )
        self.page_menu = ctk.CTkOptionMenu(
            controls, values=["Loading..."], command=self.change_gallery_page
        )
        self.page_menu.grid(row=0, column=1, sticky="ew")
        self.strip_added_metadata_var = ctk.BooleanVar(value=False)
        self.strip_added_metadata_checkbox = ctk.CTkCheckBox(
            controls,
            text="Strip metadata from imported copies",
            variable=self.strip_added_metadata_var,
        )
        self.strip_added_metadata_checkbox.grid(
            row=0, column=2, padx=(14, 0), sticky="e"
        )

        gallery_frame = ctk.CTkFrame(self)
        gallery_frame.grid(row=3, column=0, padx=18, pady=7, sticky="nsew")
        gallery_frame.grid_columnconfigure(0, weight=1)
        gallery_frame.grid_rowconfigure(1, weight=1)
        self.gallery_heading = ctk.CTkLabel(
            gallery_frame,
            text="Gallery images (Ctrl/Shift-click to select multiple)",
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        self.gallery_heading.grid(
            row=0, column=0, columnspan=2, padx=12, pady=(10, 6), sticky="ew"
        )

        list_frame = ctk.CTkFrame(gallery_frame)
        list_frame.grid(row=1, column=0, padx=(12, 6), pady=(0, 8), sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        scrollbar = ctk.CTkScrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.image_list = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            exportselection=False,
            activestyle="dotbox",
            font=("Segoe UI", 10),
            yscrollcommand=scrollbar.set,
        )
        self.image_list.grid(row=0, column=0, sticky="nsew")
        scrollbar.configure(command=self.image_list.yview)
        self.image_list.bind("<<ListboxSelect>>", self.select_gallery_images)

        actions = ctk.CTkFrame(gallery_frame, fg_color="transparent")
        actions.grid(row=1, column=1, padx=(6, 12), pady=(0, 8), sticky="ns")
        for row, (label, command) in enumerate(
            (
                ("Add images...", self.add_gallery_images),
                ("Remove selected", self.remove_gallery_images),
                ("Move selected up", lambda: self.move_gallery_images(-1)),
                ("Move selected down", lambda: self.move_gallery_images(1)),
            )
        ):
            ctk.CTkButton(actions, text=label, command=command, width=150).grid(
                row=row, column=0, padx=4, pady=4, sticky="ew"
            )

        alt_row = ctk.CTkFrame(gallery_frame, fg_color="transparent")
        alt_row.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="ew")
        alt_row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(alt_row, text="Alt text:").grid(
            row=0, column=0, padx=(0, 8), sticky="w"
        )
        self.alt_entry = ctk.CTkEntry(
            alt_row, placeholder_text="Select one or more images to edit alt text"
        )
        self.alt_entry.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(
            alt_row, text="Apply to selected", command=self.update_gallery_alt
        ).grid(row=0, column=2, padx=(8, 0))
        self.save_gallery_button = ctk.CTkButton(
            gallery_frame,
            text="Save gallery",
            command=self.save_gallery,
            width=140,
        )
        self.save_gallery_button.grid(
            row=2, column=1, padx=12, pady=(0, 10), sticky="e"
        )

        thumbnail_frame = ctk.CTkFrame(self)
        thumbnail_frame.grid(row=4, column=0, padx=18, pady=7, sticky="ew")
        thumbnail_frame.grid_columnconfigure(1, weight=1)
        thumbnail_frame.grid_columnconfigure(3, weight=1)
        ctk.CTkLabel(
            thumbnail_frame,
            text="Project-card thumbnail (projecten.html)",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, columnspan=4, padx=12, pady=(9, 5), sticky="w")
        ctk.CTkLabel(thumbnail_frame, text="Project:").grid(
            row=1, column=0, padx=(12, 6), pady=(3, 10), sticky="w"
        )
        self.project_menu = ctk.CTkOptionMenu(
            thumbnail_frame,
            values=list(PROJECT_THUMBNAILS),
            command=self.change_project_thumbnail,
        )
        self.project_menu.grid(
            row=1, column=1, padx=(0, 12), pady=(3, 10), sticky="ew"
        )
        ctk.CTkLabel(thumbnail_frame, text="Image:").grid(
            row=1, column=2, padx=(0, 6), pady=(3, 10), sticky="w"
        )
        self.thumbnail_menu = ctk.CTkOptionMenu(
            thumbnail_frame,
            values=["No images found"],
            command=self.select_thumbnail_image,
        )
        self.thumbnail_menu.grid(
            row=1, column=3, padx=(0, 12), pady=(3, 10), sticky="ew"
        )
        self.save_thumbnail_button = ctk.CTkButton(
            thumbnail_frame,
            text="Save thumbnail",
            command=self.save_project_thumbnail,
        )
        self.save_thumbnail_button.grid(
            row=1, column=4, padx=(0, 12), pady=(3, 10)
        )

        self.status_label = ctk.CTkLabel(
            self, text="Ready.", anchor="w", justify="left", wraplength=1000
        )
        self.status_label.grid(
            row=5, column=0, padx=20, pady=(3, 12), sticky="ew"
        )

    def set_status(self, message):
        self.status_label.configure(text=message)

    def toggle_info(self):
        if self.info_visible:
            self.info_label.grid_remove()
            self.info_button.configure(text="Show info")
        else:
            self.info_label.grid()
            self.info_button.configure(text="Hide info")
        self.info_visible = not self.info_visible

    @staticmethod
    def find_gallery_container(soup):
        return soup.find("div", id=GALLERY_ID, class_="image-grid")

    @staticmethod
    def clean_alt_text(filename):
        name, _ = os.path.splitext(filename)
        cleaned = re.sub(r"^\d{4}[_-]?", "", name)
        cleaned = re.sub(r"^IMG[_-]?", "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace("_", " ").replace("-", " ").strip()
        return cleaned.capitalize() if cleaned else "Illustratie"

    @staticmethod
    def create_img_tag(soup, source, alt):
        image = soup.new_tag("img")
        image["src"] = source
        image["data-src"] = source
        image["alt"] = alt
        image["loading"] = "lazy"
        return image

    def load_gallery_pages(self):
        pages = []
        for page in PAGE_IMAGE_FOLDERS:
            path = os.path.join(self.base_dir, page)
            try:
                with open(path, "r", encoding="utf-8") as html_file:
                    soup = BeautifulSoup(html_file.read(), "html.parser")
            except (OSError, UnicodeError) as error:
                self.set_status(f"Could not read {page}: {error}")
                continue
            if self.find_gallery_container(soup):
                pages.append(page)

        if not pages:
            self.page_menu.configure(values=["No matching galleries"])
            self.page_menu.set("No matching galleries")
            self.set_status(f"No pages contain div.image-grid#{GALLERY_ID}.")
            return

        self.gallery_pages = {
            page: PAGE_IMAGE_FOLDERS[page] for page in pages
        }
        self.page_menu.configure(values=pages)
        self.page_menu.set(pages[0])
        self.current_page = pages[0]
        self.load_gallery(pages[0])
        self.project_menu.set(next(iter(PROJECT_THUMBNAILS)))
        self.load_project_thumbnail_options(next(iter(PROJECT_THUMBNAILS)))

    def load_gallery(self, page):
        try:
            with open(os.path.join(self.base_dir, page), "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
        except (OSError, UnicodeError) as error:
            self.set_status(f"Could not read {page}: {error}")
            return False
        container = self.find_gallery_container(soup)
        if not container:
            self.set_status(f"{page} no longer contains the expected image grid.")
            return False

        self.gallery_images = [
            (image["src"], image.get("alt", ""))
            for image in container.find_all("img", src=True)
        ]
        self.current_page = page
        self.gallery_dirty = False
        self.render_gallery()
        self.gallery_heading.configure(
            text=f"{page} — {len(self.gallery_images)} image(s) "
            "(Ctrl/Shift-click to select multiple)"
        )
        return True

    def change_gallery_page(self, page):
        if page == self.current_page:
            return
        previous_page = self.current_page
        if self.gallery_dirty and not self.save_gallery():
            self.page_menu.set(previous_page)
            return
        if not self.load_gallery(page):
            self.page_menu.set(previous_page)

    def render_gallery(self, selected_indices=()):
        self.image_list.delete(0, "end")
        for source, alt in self.gallery_images:
            self.image_list.insert("end", f"{source}  |  {alt}")
        for index in selected_indices:
            if 0 <= index < len(self.gallery_images):
                self.image_list.selection_set(index)
        self.select_gallery_images()

    def selected_gallery_indices(self):
        return [int(index) for index in self.image_list.curselection()]

    def select_gallery_images(self, _event=None):
        selected = self.selected_gallery_indices()
        self.alt_entry.delete(0, "end")
        if len(selected) == 1:
            self.alt_entry.insert(0, self.gallery_images[selected[0]][1])
        elif selected:
            self.alt_entry.configure(
                placeholder_text=f"Apply one alt text to {len(selected)} images"
            )
        else:
            self.alt_entry.configure(
                placeholder_text="Select one or more images to edit alt text"
            )

    def add_gallery_images(self):
        selected_files = filedialog.askopenfilenames(
            parent=self,
            title="Add images to the selected gallery",
            filetypes=[
                ("Supported images", "*.jpg *.jpeg *.png *.webp *.gif"),
                ("All files", "*.*"),
            ],
        )
        if not selected_files:
            return

        target_dir = os.path.join(self.base_dir, self.gallery_pages[self.current_page])
        try:
            os.makedirs(target_dir, exist_ok=True)
        except OSError as error:
            self.set_status(f"Could not access {target_dir}: {error}")
            return

        existing_sources = {source for source, _ in self.gallery_images}
        added_indices = []
        errors = []
        for source_path in selected_files:
            extension = os.path.splitext(source_path)[1].lower()
            if extension not in GALLERY_EXTENSIONS:
                errors.append(f"Unsupported image type: {source_path}")
                continue

            source_dir = os.path.normcase(os.path.abspath(os.path.dirname(source_path)))
            target_dir_abs = os.path.normcase(os.path.abspath(target_dir))
            if source_dir == target_dir_abs:
                target_path = source_path
            else:
                target_path = self.unique_image_path(target_dir, source_path)
                temp_path = None
                try:
                    descriptor, temp_path = tempfile.mkstemp(
                        prefix="image-import-",
                        suffix=extension,
                        dir=target_dir,
                    )
                    os.close(descriptor)
                    shutil.copy2(source_path, temp_path)
                    os.replace(temp_path, target_path)
                except OSError as error:
                    errors.append(f"Could not copy {source_path}: {error}")
                    continue
                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)

            relative_path = os.path.relpath(target_path, self.base_dir).replace(
                "\\", "/"
            )
            if relative_path in existing_sources:
                continue

            if self.strip_added_metadata_var.get() and source_dir != target_dir_abs:
                success, detail = strip_image_metadata(target_path)
                if not success:
                    errors.append(
                        f"Added {relative_path}, but metadata stripping failed: "
                        f"{detail}"
                    )

            self.gallery_images.append(
                (relative_path, self.clean_alt_text(os.path.basename(target_path)))
            )
            added_indices.append(len(self.gallery_images) - 1)
            existing_sources.add(relative_path)

        if added_indices:
            self.gallery_dirty = True
            self.render_gallery(added_indices)
        message = f"Added {len(added_indices)} image(s) to {self.current_page}."
        if errors:
            message += " " + " ".join(errors)
        self.set_status(message)

    @staticmethod
    def unique_image_path(target_dir, source_path):
        filename = os.path.basename(source_path)
        stem, extension = os.path.splitext(filename)
        path = os.path.join(target_dir, filename)
        suffix = 2
        while os.path.exists(path):
            path = os.path.join(target_dir, f"{stem} ({suffix}){extension}")
            suffix += 1
        return path

    def remove_gallery_images(self):
        selected = self.selected_gallery_indices()
        if not selected:
            self.set_status("Select one or more gallery entries to remove.")
            return
        for index in reversed(selected):
            self.gallery_images.pop(index)
        self.gallery_dirty = True
        self.render_gallery()
        self.set_status(
            f"Removed {len(selected)} gallery entry/entries. Image files were kept."
        )

    def move_gallery_images(self, direction):
        selected = self.selected_gallery_indices()
        if not selected:
            self.set_status("Select one or more images to reorder.")
            return
        if direction < 0:
            if selected[0] == 0:
                return
            for index in selected:
                self.gallery_images[index - 1], self.gallery_images[index] = (
                    self.gallery_images[index],
                    self.gallery_images[index - 1],
                )
            selected = [index - 1 for index in selected]
        else:
            if selected[-1] == len(self.gallery_images) - 1:
                return
            for index in reversed(selected):
                self.gallery_images[index + 1], self.gallery_images[index] = (
                    self.gallery_images[index],
                    self.gallery_images[index + 1],
                )
            selected = [index + 1 for index in selected]
        self.gallery_dirty = True
        self.render_gallery(selected)
        self.set_status(f"Moved {len(selected)} image(s). Save to keep the new order.")

    def update_gallery_alt(self):
        selected = self.selected_gallery_indices()
        if not selected:
            self.set_status("Select one or more images before applying alt text.")
            return
        alt = self.alt_entry.get().strip()
        for index in selected:
            source, _ = self.gallery_images[index]
            self.gallery_images[index] = (source, alt)
        self.gallery_dirty = True
        self.render_gallery(selected)
        self.set_status(f"Updated alt text for {len(selected)} image(s).")

    def save_gallery(self):
        if not self.current_page:
            return False
        path = os.path.join(self.base_dir, self.current_page)
        temp_path = None
        try:
            with open(path, "r", encoding="utf-8") as html_file:
                soup = BeautifulSoup(html_file.read(), "html.parser")
            container = self.find_gallery_container(soup)
            if not container:
                raise ValueError(
                    f"{self.current_page} no longer contains "
                    f"div.image-grid#{GALLERY_ID}"
                )
            container.clear()
            for source, alt in self.gallery_images:
                container.append(self.create_img_tag(soup, source, alt))
                container.append("\n                ")
            if container.contents:
                container.contents[-1].replace_with("\n            ")

            descriptor, temp_path = tempfile.mkstemp(
                prefix="gallery-edit-", suffix=".html", dir=self.base_dir
            )
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as f:
                f.write(str(soup))
            os.replace(temp_path, path)
        except (OSError, UnicodeError, ValueError) as error:
            self.set_status(f"Could not save {self.current_page}: {error}")
            return False
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

        self.gallery_dirty = False
        self.set_status(f"Saved {len(self.gallery_images)} image(s) to {self.current_page}.")
        return True

    def change_project_thumbnail(self, project):
        if self.thumbnail_dirty and not self.save_project_thumbnail():
            self.project_menu.set(self.current_project)
            return
        self.load_project_thumbnail_options(project)

    def load_project_thumbnail_options(self, project):
        self.current_project = project
        page, image_folder = PROJECT_THUMBNAILS[project]
        html_path = os.path.join(self.base_dir, "projecten.html")
        try:
            with open(html_path, "r", encoding="utf-8") as html_file:
                soup = BeautifulSoup(html_file.read(), "html.parser")
            link = soup.find("a", href=page, class_="project-link")
            wrapper = link.find("div", class_="project-image-wrapper") if link else None
            card_image = wrapper.find("img") if wrapper else None
            if not card_image:
                raise ValueError(f"Could not find the project card for {project}.")
            self.current_thumbnail_src = card_image.get("src", "")
        except (OSError, UnicodeError, ValueError) as error:
            self.set_status(f"Could not read project thumbnail: {error}")
            return

        directory = os.path.join(self.base_dir, image_folder)
        try:
            filenames = sorted(
                (
                    filename
                    for filename in os.listdir(directory)
                    if os.path.splitext(filename)[1].lower() in GALLERY_EXTENSIONS
                ),
                key=str.lower,
            )
        except OSError as error:
            self.set_status(f"Could not read {image_folder}: {error}")
            filenames = []

        self.project_images = {
            self.relative_site_path(os.path.join(directory, filename)): filename
            for filename in filenames
        }
        options = list(self.project_images)
        if self.current_thumbnail_src and self.current_thumbnail_src not in options:
            options.insert(0, self.current_thumbnail_src)
        if not options:
            options = ["No images found"]
        self.thumbnail_menu.configure(values=options)
        self.thumbnail_menu.set(
            self.current_thumbnail_src
            if self.current_thumbnail_src in options
            else options[0]
        )
        self.thumbnail_dirty = False
        self.set_status(f"Choose a thumbnail image for {project}.")

    def select_thumbnail_image(self, source):
        if source != "No images found":
            self.thumbnail_dirty = source != self.current_thumbnail_src

    def save_project_thumbnail(self):
        source = self.thumbnail_menu.get()
        if not source or source == "No images found":
            self.set_status("No thumbnail image is selected.")
            return False
        page, _ = PROJECT_THUMBNAILS[self.current_project]
        path = os.path.join(self.base_dir, "projecten.html")
        temp_path = None
        try:
            with open(path, "r", encoding="utf-8") as html_file:
                soup = BeautifulSoup(html_file.read(), "html.parser")
            link = soup.find("a", href=page, class_="project-link")
            wrapper = link.find("div", class_="project-image-wrapper") if link else None
            image = wrapper.find("img") if wrapper else None
            if not image:
                raise ValueError(f"Could not find the project card for {self.current_project}.")
            image["src"] = source
            descriptor, temp_path = tempfile.mkstemp(
                prefix="thumbnail-edit-", suffix=".html", dir=self.base_dir
            )
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as html_file:
                html_file.write(str(soup))
            os.replace(temp_path, path)
        except (OSError, UnicodeError, ValueError) as error:
            self.set_status(f"Could not save project thumbnail: {error}")
            return False
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

        self.current_thumbnail_src = source
        self.thumbnail_dirty = False
        self.set_status(f"Saved {self.current_project} thumbnail to projecten.html.")
        return True

    def relative_site_path(self, path):
        return os.path.relpath(path, self.base_dir).replace("\\", "/")

    def close_app(self):
        if self.gallery_dirty and not self.save_gallery():
            return
        if self.thumbnail_dirty and not self.save_project_thumbnail():
            return
        self.destroy()


if __name__ == "__main__":
    app = ImageSyncApp()
    app.mainloop()
