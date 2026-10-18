import html
import os
import re
import shutil
import tempfile
import tkinter as tk
import unicodedata
import xml.etree.ElementTree as ET
from tkinter import filedialog, messagebox, simpledialog
from urllib.parse import quote, unquote, urlsplit

from bs4 import BeautifulSoup, NavigableString, Tag
from PIL import Image, ImageSequence
import customtkinter as ctk
import piexif


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

GALLERY_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
METADATA_EXTENSIONS = GALLERY_EXTENSIONS | {".tif", ".tiff", ".bmp"}
GALLERY_ID = "image-grid-container"
SITE_BASE_URL = "https://charlottevandeputte.com"
PAGE_IMAGE_FOLDERS = {
    "/": ("index.html", "images/index"),
    "/schetsen/": ("schetsen/index.html", "schetsen/images"),
    "/projecten/": ("projecten/index.html", "projecten/images"),
    "/over-mij/": ("over-mij/index.html", "over-mij/images"),
    "/contact/": ("contact/index.html", "contact/images"),
}


def image_year_sort_key(source):
    """Sort images by the first year in their filename, newest year first."""
    filename = os.path.basename(unquote(urlsplit(source).path))
    match = re.search(r"(?<!\d)(?:19|20)\d{2}(?!\d)", filename)
    if not match:
        return (1, 0)
    return (0, -int(match.group()))


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
        except (OSError, ValueError, piexif.InvalidImageDataError) as error:
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
    except (
        OSError,
        ValueError,
        EOFError,
        SyntaxError,
        Image.DecompressionBombError,
        piexif.InvalidImageDataError,
    ) as error:
        if exif_error:
            return False, f"EXIF removal failed ({exif_error}); image rewrite failed ({error})"
        return False, str(error)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


class ImageSyncApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.gallery_pages = {}
        self.gallery_images = []
        self.gallery_dirty = False
        self.current_page = ""
        self.project_thumbnails = {}
        self.page_image_folders = PAGE_IMAGE_FOLDERS.copy()
        self.current_project = ""
        self.thumbnail_dirty = False
        self.pending_thumbnails = {}
        self.project_image_options = {}
        self.preview_photo = None
        self.project_text_dirty = False
        self.project_text_loading = False

        self.create_widgets()
        self.load_gallery_pages()
        self.protocol("WM_DELETE_WINDOW", self.close_app)

    def create_widgets(self):
        self.title("Portfolio Website Manager")
        self.geometry("1080x760")
        self.minsize(840, 620)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="Portfolio Website Manager",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Manage gallery images and project pages",
            anchor="e",
        ).grid(row=0, column=1, sticky="e")

        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=1, column=0, padx=20, pady=8, sticky="nsew")
        self.gallery_tab = self.tabs.add("Galleries")
        self.project_tab = self.tabs.add("Project pages")
        self.gallery_tab.grid_columnconfigure(0, weight=1)
        self.gallery_tab.grid_rowconfigure(1, weight=1)
        self.project_tab.grid_columnconfigure(0, weight=1)
        self.project_tab.grid_rowconfigure(1, weight=1)

        gallery_controls = ctk.CTkFrame(self.gallery_tab, fg_color="transparent")
        gallery_controls.grid(row=0, column=0, padx=8, pady=(8, 12), sticky="ew")
        gallery_controls.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(gallery_controls, text="Gallery page").grid(
            row=0, column=0, padx=(0, 10), sticky="w"
        )
        self.page_menu = ctk.CTkOptionMenu(
            gallery_controls, values=["Loading..."], command=self.change_gallery_page
        )
        self.page_menu.grid(row=0, column=1, padx=(0, 18), sticky="ew")
        self.strip_added_metadata_var = ctk.BooleanVar(value=True)
        self.strip_added_metadata_checkbox = ctk.CTkCheckBox(
            gallery_controls,
            text="Strip metadata from imported copies",
            variable=self.strip_added_metadata_var,
        )
        self.strip_added_metadata_checkbox.grid(row=0, column=2, sticky="e")

        gallery_frame = ctk.CTkFrame(self.gallery_tab)
        gallery_frame.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="nsew")
        gallery_frame.grid_columnconfigure(0, weight=1)
        gallery_frame.grid_rowconfigure(1, weight=1)
        self.gallery_heading = ctk.CTkLabel(
            gallery_frame,
            text="Images in this gallery",
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        self.gallery_heading.grid(
            row=0, column=0, columnspan=2, padx=14, pady=(12, 6), sticky="ew"
        )

        list_frame = ctk.CTkFrame(gallery_frame)
        list_frame.grid(row=1, column=0, padx=(14, 8), pady=(0, 10), sticky="nsew")
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
        actions.grid(row=1, column=1, padx=(4, 14), pady=(0, 10), sticky="ns")
        for row, (label, command) in enumerate(
            (
                ("Add images...", self.add_gallery_images),
                ("Remove from gallery", self.remove_gallery_images),
                ("Move up", lambda: self.move_gallery_images(-1)),
                ("Move down", lambda: self.move_gallery_images(1)),
            )
        ):
            ctk.CTkButton(actions, text=label, command=command, width=170).grid(
                row=row, column=0, padx=4, pady=5, sticky="ew"
            )
        ctk.CTkLabel(
            actions,
            text="Removing an entry keeps\nits image file on disk.",
            justify="left",
            anchor="w",
        ).grid(row=4, column=0, padx=4, pady=(10, 0), sticky="ew")

        alt_row = ctk.CTkFrame(gallery_frame, fg_color="transparent")
        alt_row.grid(row=2, column=0, columnspan=2, padx=14, pady=(0, 12), sticky="ew")
        alt_row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(alt_row, text="Alt text:").grid(
            row=0, column=0, padx=(0, 10), sticky="w"
        )
        self.alt_entry = ctk.CTkEntry(
            alt_row, placeholder_text="Select image(s), then enter descriptive alt text"
        )
        self.alt_entry.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(
            alt_row, text="Apply alt text", command=self.update_gallery_alt
        ).grid(row=0, column=2, padx=(10, 0))
        self.save_gallery_button = ctk.CTkButton(
            alt_row,
            text="Save gallery changes",
            command=self.save_gallery,
            width=170,
        )
        self.save_gallery_button.grid(row=0, column=3, padx=(12, 0), sticky="e")

        project_toolbar = ctk.CTkFrame(self.project_tab, fg_color="transparent")
        project_toolbar.grid(row=0, column=0, padx=8, pady=(8, 12), sticky="ew")
        project_toolbar.grid_columnconfigure(1, weight=1)
        self.project_menu = ctk.CTkOptionMenu(
            project_toolbar,
            values=["Loading..."],
            command=self.change_project,
        )
        self.project_menu.grid(row=0, column=1, padx=(0, 10), sticky="ew")
        ctk.CTkLabel(project_toolbar, text="Project").grid(
            row=0, column=0, padx=(0, 10), sticky="w"
        )
        ctk.CTkButton(
            project_toolbar,
            text="Add project page",
            command=self.add_project_page,
        ).grid(row=0, column=2, padx=(6, 0))
        ctk.CTkButton(
            project_toolbar,
            text="Remove project",
            command=self.remove_project_page,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
        ).grid(row=0, column=3, padx=(8, 0))

        self.project_settings_tabs = ctk.CTkTabview(self.project_tab)
        self.project_settings_tabs.grid(
            row=1, column=0, padx=8, pady=(0, 8), sticky="nsew"
        )
        self.project_text_tab = self.project_settings_tabs.add("Text & history")
        self.project_thumbnail_tab = self.project_settings_tabs.add("Card image")
        self.project_text_tab.grid_columnconfigure(0, weight=1)
        self.project_text_tab.grid_rowconfigure(3, weight=1)
        self.project_thumbnail_tab.grid_columnconfigure(0, weight=1)
        self.project_thumbnail_tab.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(
            self.project_text_tab,
            text="Short description",
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=12, pady=(12, 4), sticky="ew")
        self.project_intro_text = ctk.CTkTextbox(
            self.project_text_tab, height=100, wrap="word"
        )
        self.project_intro_text.grid(
            row=1, column=0, padx=12, pady=(0, 8), sticky="ew"
        )
        ctk.CTkLabel(
            self.project_text_tab,
            text="Optional links: [link text](URL). Separate paragraphs with a blank line.",
            anchor="w",
        ).grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")
        history_frame = ctk.CTkFrame(self.project_text_tab, fg_color="transparent")
        history_frame.grid(row=3, column=0, padx=12, pady=(0, 8), sticky="nsew")
        history_frame.grid_columnconfigure(0, weight=1)
        history_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            history_frame,
            text="History / events — one entry per line, starting with a four-digit year",
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, pady=(0, 4), sticky="ew")
        self.project_history_text = ctk.CTkTextbox(history_frame, wrap="word")
        self.project_history_text.grid(row=1, column=0, sticky="nsew")
        self.project_text_save_button = ctk.CTkButton(
            self.project_text_tab,
            text="Save project text",
            command=self.save_project_text,
        )
        self.project_text_save_button.grid(
            row=4, column=0, padx=12, pady=(4, 12), sticky="e"
        )
        self.project_intro_text.bind("<KeyRelease>", self.mark_project_text_dirty)
        self.project_history_text.bind("<KeyRelease>", self.mark_project_text_dirty)

        project_content = ctk.CTkFrame(self.project_thumbnail_tab)
        project_content.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        project_content.grid_columnconfigure(0, weight=1)
        project_content.grid_columnconfigure(1, weight=0)
        project_content.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            project_content,
            text="Project card image",
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=14, pady=(12, 4), sticky="w")
        ctk.CTkLabel(
            project_content,
            text="Choose a project image for the card on the Projects page.",
            anchor="w",
        ).grid(row=0, column=1, padx=14, pady=(12, 4), sticky="e")
        thumbnail_controls = ctk.CTkFrame(project_content, fg_color="transparent")
        thumbnail_controls.grid(row=1, column=0, padx=14, pady=8, sticky="new")
        thumbnail_controls.grid_columnconfigure(0, weight=1)
        self.thumbnail_menu = ctk.CTkOptionMenu(
            thumbnail_controls,
            values=["No images found"],
            command=self.select_thumbnail_image,
        )
        self.thumbnail_menu.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        self.thumbnail_path_label = ctk.CTkLabel(
            thumbnail_controls,
            text="No thumbnail selected",
            anchor="w",
            justify="left",
            wraplength=440,
        )
        self.thumbnail_path_label.grid(row=1, column=0, pady=(0, 10), sticky="ew")
        self.save_thumbnail_button = ctk.CTkButton(
            thumbnail_controls,
            text="Save project card image",
            command=self.save_project_thumbnail,
        )
        self.save_thumbnail_button.grid(row=2, column=0, sticky="w")

        preview_frame = ctk.CTkFrame(project_content, width=280, height=280)
        preview_frame.grid(row=1, column=1, padx=14, pady=8, sticky="ne")
        preview_frame.grid_propagate(False)
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)
        self.thumbnail_preview = ctk.CTkLabel(
            preview_frame, text="Select an image to preview", wraplength=240
        )
        self.thumbnail_preview.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")

        self.status_label = ctk.CTkLabel(
            self, text="Ready.", anchor="w", justify="left", wraplength=1040
        )
        self.status_label.grid(
            row=2, column=0, padx=22, pady=(2, 12), sticky="ew"
        )

    def set_status(self, message):
        self.status_label.configure(text=message)

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

    def resolve_local_image_source(self, source, html_path):
        parsed = urlsplit(source)
        if parsed.scheme or parsed.netloc or not parsed.path:
            return None

        source_path = unquote(parsed.path)
        if source_path.startswith("/"):
            file_path = os.path.join(self.base_dir, source_path.lstrip("/"))
        else:
            document_dir = os.path.dirname(os.path.join(self.base_dir, html_path))
            file_path = os.path.join(document_dir, source_path)
        file_path = os.path.abspath(os.path.normpath(file_path))
        try:
            if os.path.commonpath((self.base_dir, file_path)) != self.base_dir:
                return None
        except ValueError:
            return None
        return file_path if os.path.isfile(file_path) else None

    def relative_url_for_file(self, file_path, html_path):
        document_dir = os.path.dirname(os.path.join(self.base_dir, html_path))
        relative_path = os.path.relpath(file_path, document_dir).replace("\\", "/")
        return quote(relative_path, safe="/-._~")

    def normalize_image_source(self, source, route):
        html_path, _image_folder = self.page_image_folders[route]
        file_path = self.resolve_local_image_source(source, html_path)
        return self.relative_url_for_file(file_path, html_path) if file_path else source

    def load_gallery_pages(self, preferred_page=None, preferred_project=None):
        try:
            self.load_project_registry()
        except (OSError, UnicodeError, ValueError) as error:
            self.set_status(f"Could not load project pages: {error}")
            return

        pages = []
        for route, (page, _image_folder) in self.page_image_folders.items():
            path = os.path.join(self.base_dir, page)
            try:
                with open(path, "r", encoding="utf-8") as html_file:
                    soup = BeautifulSoup(html_file.read(), "html.parser")
            except (OSError, UnicodeError) as error:
                self.set_status(f"Could not read {page}: {error}")
                continue
            if self.find_gallery_container(soup):
                pages.append(route)

        if not pages:
            self.page_menu.configure(values=["No matching galleries"])
            self.page_menu.set("No matching galleries")
            self.set_status(f"No pages contain div.image-grid#{GALLERY_ID}.")
            return

        self.gallery_pages = {route: self.page_image_folders[route][1] for route in pages}
        selected_page = preferred_page if preferred_page in pages else pages[0]
        self.page_menu.configure(values=pages)
        self.page_menu.set(selected_page)
        self.current_page = selected_page
        self.load_gallery(selected_page)
        projects = list(self.project_thumbnails)
        if projects:
            selected_project = (
                preferred_project if preferred_project in projects else projects[0]
            )
            self.project_menu.configure(values=projects)
            self.project_menu.set(selected_project)
            self.load_project_thumbnail_options(selected_project)
            self.load_project_text(selected_project)
        else:
            self.project_menu.configure(values=["No projects found"])
            self.project_menu.set("No projects found")
            self.project_intro_text.configure(state="disabled")
            self.project_history_text.configure(state="disabled")

    def load_project_registry(self):
        listing_path = os.path.join(self.base_dir, "projecten", "index.html")
        with open(listing_path, "r", encoding="utf-8") as html_file:
            soup = BeautifulSoup(html_file.read(), "html.parser")
        self.project_thumbnails = {}
        self.page_image_folders = PAGE_IMAGE_FOLDERS.copy()
        for link in soup.find_all("a", class_="project-link", href=True):
            slug = link["href"].strip("/")
            if not re.fullmatch(r"[A-Za-z0-9_-]+", slug):
                continue
            title = link.find("h3")
            if not title:
                continue
            route = f"/projecten/{slug}/"
            page = f"projecten/{slug}/index.html"
            image_folder = f"projecten/{slug}/images"
            if not os.path.isfile(os.path.join(self.base_dir, page)):
                continue
            project_name = title.get_text(" ", strip=True)
            self.project_thumbnails[project_name] = (route, image_folder)
            self.page_image_folders[route] = (page, image_folder)

    @staticmethod
    def inline_text_from_html(node):
        parts = []
        for child in node.children:
            if isinstance(child, NavigableString):
                parts.append(re.sub(r"\s+", " ", str(child)))
            elif isinstance(child, Tag) and child.name == "br":
                parts.append("\n")
            elif isinstance(child, Tag) and child.name == "a":
                label = child.get_text(" ", strip=True)
                href = child.get("href", "").strip()
                parts.append(f"[{label}]({href})" if href else label)
            elif isinstance(child, Tag):
                parts.append(ImageSyncApp.inline_text_from_html(child))
        return "".join(parts).strip()

    @staticmethod
    def project_text_from_soup(soup):
        wrapper = soup.find("div", class_="text-box-wrapper")
        if not wrapper:
            raise ValueError("Could not find the project text section.")
        heading = wrapper.find("h2", recursive=False)
        if not heading:
            raise ValueError("Could not find the project title heading.")

        descriptions = []
        events = []
        intro_container = wrapper.find(attrs={"data-project-intro": True})
        history_container = wrapper.find(attrs={"data-project-history": True})
        paragraphs = wrapper.find_all("p", recursive=False)

        if intro_container:
            paragraphs = intro_container.find_all("p")
        for paragraph in paragraphs:
            if paragraph.find("strong", string=re.compile(r"^\s*\d{4}\s*$")):
                continue
            text = ImageSyncApp.inline_text_from_html(paragraph)
            if text:
                descriptions.append(text)

        event_paragraphs = (
            history_container.find_all("p")
            if history_container
            else wrapper.find_all("p", recursive=False)
        )
        for paragraph in event_paragraphs:
            years = paragraph.find_all("strong")
            year_nodes = [
                year for year in years
                if re.fullmatch(r"\s*\d{4}\s*", year.get_text())
            ]
            for year_node in year_nodes:
                event_parts = []
                for sibling in year_node.next_siblings:
                    if isinstance(sibling, Tag) and (
                        sibling.name == "br"
                        or (
                            sibling.name == "strong"
                            and re.fullmatch(r"\s*\d{4}\s*", sibling.get_text())
                        )
                    ):
                        break
                    text = (
                        sibling.get_text(" ", strip=True)
                        if isinstance(sibling, Tag)
                        else str(sibling).strip()
                    )
                    if text:
                        event_parts.append(text)
                event = " ".join(event_parts).strip()
                if event:
                    events.append(f"{year_node.get_text(strip=True)} {event}")
        return heading.get_text(" ", strip=True), "\n\n".join(descriptions), "\n".join(events)

    def load_project_text(self, project):
        if project not in self.project_thumbnails:
            return False
        route, _image_folder = self.project_thumbnails[project]
        page_path, _gallery_folder = self.page_image_folders[route]
        try:
            with open(
                os.path.join(self.base_dir, page_path), "r", encoding="utf-8"
            ) as html_file:
                soup = BeautifulSoup(html_file.read(), "html.parser")
            _title, intro, history = self.project_text_from_soup(soup)
        except (OSError, UnicodeError, ValueError) as error:
            self.set_status(f"Could not load project text: {error}")
            return False

        self.project_text_loading = True
        try:
            for textbox, text in (
                (self.project_intro_text, intro),
                (self.project_history_text, history),
            ):
                textbox.configure(state="normal")
                textbox.delete("1.0", "end")
                textbox.insert("1.0", text)
            self.project_text_dirty = False
        finally:
            self.project_text_loading = False
        self.set_status(f"Editing text for {project}.")
        return True

    def mark_project_text_dirty(self, _event=None):
        if self.project_text_loading:
            return
        self.project_text_dirty = True
        self.set_status(
            f"Unsaved text changes for {self.current_project}. Save project text to apply."
        )

    @staticmethod
    def append_inline_text(soup, parent, text):
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
        for line_index, line in enumerate(text.split("\n")):
            if line_index:
                parent.append(soup.new_tag("br"))
            cursor = 0
            for match in link_pattern.finditer(line):
                if match.start() > cursor:
                    parent.append(line[cursor:match.start()])
                href = match.group(2)
                parsed = urlsplit(href)
                if parsed.scheme not in {"", "http", "https", "mailto"} or href.startswith("//"):
                    parent.append(match.group(0))
                else:
                    link = soup.new_tag("a", href=href)
                    link.string = match.group(1)
                    if parsed.scheme in {"http", "https"}:
                        link["target"] = "_blank"
                        link["rel"] = "noopener"
                    parent.append(link)
                cursor = match.end()
            if cursor < len(line):
                parent.append(line[cursor:])

    def save_project_text(self):
        project = self.current_project
        if project not in self.project_thumbnails:
            self.set_status("Select a project page first.")
            return False

        intro = self.project_intro_text.get("1.0", "end-1c").strip()
        raw_events = self.project_history_text.get("1.0", "end-1c")
        events = []
        for line_number, line in enumerate(raw_events.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            match = re.fullmatch(r"(\d{4})\s+(.+)", line)
            if not match:
                self.set_status(
                    f"History line {line_number} must start with a year, "
                    "for example: 2026 New exhibition"
                )
                return False
            events.append((match.group(1), match.group(2).strip()))

        route, _image_folder = self.project_thumbnails[project]
        page_path, _gallery_folder = self.page_image_folders[route]
        path = os.path.join(self.base_dir, page_path)
        try:
            with open(path, "r", encoding="utf-8") as html_file:
                soup = BeautifulSoup(html_file.read(), "html.parser")
            wrapper = soup.find("div", class_="text-box-wrapper")
            if not wrapper:
                raise ValueError("Could not find the project text section.")
            heading = wrapper.find("h2", recursive=False)
            if not heading:
                raise ValueError("Could not find the project title heading.")

            for child in list(wrapper.contents):
                if child is not heading:
                    child.extract()

            intro_container = soup.new_tag("div")
            intro_container["data-project-intro"] = ""
            for paragraph_text in re.split(r"\n\s*\n", intro):
                paragraph_text = paragraph_text.strip()
                if not paragraph_text:
                    continue
                paragraph = soup.new_tag("p")
                self.append_inline_text(soup, paragraph, paragraph_text)
                intro_container.append(paragraph)

            history_container = soup.new_tag("div")
            history_container["data-project-history"] = ""
            if events:
                paragraph = soup.new_tag("p")
                for index, (year, description) in enumerate(events):
                    if index:
                        paragraph.append(soup.new_tag("br"))
                    year_node = soup.new_tag("strong")
                    year_node.string = year
                    paragraph.append(year_node)
                    paragraph.append(f" {description}")
                history_container.append(paragraph)

            wrapper.append(intro_container)
            wrapper.append(history_container)
            self.write_text_atomic(path, str(soup))
        except (OSError, UnicodeError, ValueError) as error:
            self.set_status(f"Could not save project text: {error}")
            return False

        self.project_text_dirty = False
        self.set_status(f"Saved description and {len(events)} event(s) for {project}.")
        return True

    @staticmethod
    def project_page_html(title, slug):
        safe_title = html.escape(title)
        route = f"{SITE_BASE_URL}/projecten/{slug}/"
        return f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title} – Charlotte Vandeputte</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&amp;display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../../style.css">
    <link rel="icon" type="image/x-icon" href="../../favicon/favicon.ico">
    <meta name="description" content="{safe_title} – project van illustrator Charlotte Vandeputte.">
    <link rel="canonical" href="{route}">
</head>
<body>
    <nav class="sidebar" aria-label="Hoofdnavigatie">
        <a href="../../" class="logo-link">
            <img src="../../images/menu/cvdp2.png" alt="Charlotte Vandeputte Logo" class="sidebar-logo">
        </a>
        <div class="mobile-name">Charlotte Vandeputte</div>
        <button class="menu-toggle" aria-label="Menu openen" aria-expanded="false">
            <span></span><span></span>
        </button>
        <ul class="nav-links">
            <li><a href="../../"><span>Portfolio</span></a></li>
            <li class="active"><a href="../"><span>Projecten</span></a></li>
            <li><a href="../../schetsen/"><span>Schetsen</span></a></li>
            <li><a href="../../over-mij/"><span>Over mij</span></a></li>
            <li><a href="../../contact/"><span>Contact</span></a></li>
        </ul>
        <div class="social-links">
            <a href="mailto:vandeputtecharlotte@outlook.com" target="_blank" aria-label="E-mail sturen">
                <img src="../../images/icons/mail.png" alt="Email icon">
            </a>
            <a href="https://www.linkedin.com/in/charlottevandeputte" target="_blank" rel="noopener" aria-label="LinkedIn Profiel">
                <img src="../../images/icons/linkedin.png" alt="LinkedIn icon">
            </a>
            <a href="https://www.instagram.com/charlotteillustratie" target="_blank" rel="noopener" aria-label="Instagram Profiel">
                <img src="../../images/icons/instagram.png" alt="Instagram icon">
            </a>
        </div>
    </nav>
    <div class="main-container">
        <main class="content">
            <div class="text-box-wrapper">
                <h2>{safe_title}</h2>
                <div data-project-intro></div>
                <div data-project-history></div>
            </div>
            <div class="image-grid" id="{GALLERY_ID}"></div>
        </main>
        <footer class="site-footer">
            <p>&copy; <span id="year"></span> Charlotte Vandeputte</p>
        </footer>
    </div>
    <dialog aria-label="Afbeelding vergroten" class="lightbox" id="lightbox">
        <button aria-label="Sluiten" class="lightbox-close">Sluiten</button>
        <button aria-label="Vorige afbeelding" class="lightbox-nav lightbox-prev">Vorige</button>
        <img alt="" class="lightbox-image" src="">
        <button aria-label="Volgende afbeelding" class="lightbox-nav lightbox-next">Volgende</button>
    </dialog>
    <script src="../../script.js"></script>
</body>
</html>
"""

    @staticmethod
    def update_sitemap(content, route, remove=False):
        root = ET.fromstring(content)
        namespace = ""
        if root.tag.startswith("{"):
            namespace = root.tag.split("}", 1)[0] + "}"
            ET.register_namespace("", namespace[1:-1])
        location = f"{SITE_BASE_URL}{route}"
        entries = root.findall(f"{namespace}url")
        matching_entries = [
            entry
            for entry in entries
            if (entry.findtext(f"{namespace}loc") or "").strip() == location
        ]
        if remove:
            if len(matching_entries) != 1:
                raise ValueError(f"Expected one sitemap entry for {route}.")
            root.remove(matching_entries[0])
        elif matching_entries:
            raise ValueError(f"Sitemap already contains {route}.")
        else:
            entry = ET.SubElement(root, f"{namespace}url")
            ET.SubElement(entry, f"{namespace}loc").text = location
            ET.SubElement(entry, f"{namespace}priority").text = "0.80"
        ET.indent(root, space="    ")
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            + ET.tostring(root, encoding="unicode")
            + "\n"
        )

    @staticmethod
    def write_text_atomic(path, content):
        temp_path = None
        try:
            descriptor, temp_path = tempfile.mkstemp(
                prefix="website-manager-", suffix=".tmp", dir=os.path.dirname(path)
            )
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as output:
                output.write(content)
            os.replace(temp_path, path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def add_project_page(self):
        if self.project_text_dirty and not self.save_project_text():
            return
        if self.gallery_dirty and not self.save_gallery():
            return
        if self.thumbnail_dirty and not self.save_project_thumbnail():
            return
        title = simpledialog.askstring(
            "Add project page", "Project name:", parent=self
        )
        if title is None:
            return
        title = title.strip()
        if not title:
            self.set_status("Enter a project name.")
            return
        slug_source = unicodedata.normalize("NFKD", title)
        slug_source = slug_source.encode("ascii", "ignore").decode("ascii").lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug_source).strip("-")
        if not slug:
            self.set_status("The project name must contain at least one letter or number.")
            return
        route = f"/projecten/{slug}/"
        project_dir = os.path.join(self.base_dir, "projecten", slug)
        if (
            route in self.page_image_folders
            or os.path.exists(project_dir)
            or title in self.project_thumbnails
        ):
            self.set_status(f"A project page named '{title}' or '{slug}' already exists.")
            return

        listing_path = os.path.join(self.base_dir, "projecten", "index.html")
        sitemap_path = os.path.join(self.base_dir, "sitemap.xml")
        page_path = os.path.join(project_dir, "index.html")
        image_folder = os.path.join(project_dir, "images")
        try:
            with open(listing_path, "r", encoding="utf-8") as html_file:
                original_listing = html_file.read()
            with open(sitemap_path, "r", encoding="utf-8") as sitemap_file:
                original_sitemap = sitemap_file.read()
            soup = BeautifulSoup(original_listing, "html.parser")
            grid = soup.find("div", class_="projects-grid")
            if not grid:
                raise ValueError("Could not find the project listing grid.")
            item = soup.new_tag("div", **{"class": "project-item"})
            link = soup.new_tag("a", href=f"{slug}/", **{"class": "project-link"})
            wrapper = soup.new_tag("div", **{"class": "project-image-wrapper"})
            heading = soup.new_tag("h3")
            heading.string = title
            link.append(wrapper)
            link.append(heading)
            item.append(link)
            grid.append(item)
            updated_listing = str(soup)
            updated_sitemap = self.update_sitemap(original_sitemap, route)

            os.makedirs(image_folder)
            self.write_text_atomic(page_path, self.project_page_html(title, slug))
            self.write_text_atomic(listing_path, updated_listing)
            self.write_text_atomic(sitemap_path, updated_sitemap)
        except (OSError, UnicodeError, ValueError, ET.ParseError) as error:
            rollback_errors = []
            if os.path.isdir(project_dir):
                try:
                    shutil.rmtree(project_dir)
                except OSError as rollback_error:
                    rollback_errors.append(f"Could not remove new project folder: {rollback_error}")
            if "original_listing" in locals() and os.path.exists(listing_path):
                try:
                    with open(listing_path, "r", encoding="utf-8") as html_file:
                        current_listing = html_file.read()
                    if current_listing != original_listing:
                        self.write_text_atomic(listing_path, original_listing)
                except (OSError, UnicodeError) as rollback_error:
                    rollback_errors.append(f"Could not restore project listing: {rollback_error}")
            if "original_sitemap" in locals() and os.path.exists(sitemap_path):
                try:
                    with open(sitemap_path, "r", encoding="utf-8") as sitemap_file:
                        current_sitemap = sitemap_file.read()
                    if current_sitemap != original_sitemap:
                        self.write_text_atomic(sitemap_path, original_sitemap)
                except (OSError, UnicodeError) as rollback_error:
                    rollback_errors.append(f"Could not restore sitemap: {rollback_error}")
            detail = " ".join(rollback_errors)
            self.set_status(f"Could not add project page: {error} {detail}".strip())
            return

        self.load_gallery_pages(preferred_page=route, preferred_project=title)
        self.set_status(
            f"Created '{title}'. Add images to {route}, then choose a card thumbnail."
        )

    def remove_project_page(self):
        project = self.project_menu.get()
        if project not in self.project_thumbnails:
            self.set_status("Select a project page to remove.")
            return
        route, _image_folder = self.project_thumbnails[project]
        if not messagebox.askyesno(
            "Remove project page",
            f"Remove '{project}', its page, and all its images? This cannot be undone.",
            parent=self,
        ):
            return
        if self.project_text_dirty and not self.save_project_text():
            return
        if self.gallery_dirty and not self.save_gallery():
            return
        if self.thumbnail_dirty and not self.save_project_thumbnail():
            return

        listing_path = os.path.join(self.base_dir, "projecten", "index.html")
        sitemap_path = os.path.join(self.base_dir, "sitemap.xml")
        project_dir = os.path.join(self.base_dir, "projecten", route.strip("/").split("/")[-1])
        try:
            with open(listing_path, "r", encoding="utf-8") as html_file:
                original_listing = html_file.read()
            with open(sitemap_path, "r", encoding="utf-8") as sitemap_file:
                original_sitemap = sitemap_file.read()
            soup = BeautifulSoup(original_listing, "html.parser")
            card = self.find_project_card(soup, route)
            if not card:
                raise ValueError(f"Could not find the project card for {project}.")
            item = card.find_parent("div", class_="project-item")
            if not item:
                raise ValueError(f"Could not find the project item for {project}.")
            item.decompose()
            updated_listing = str(soup)
            updated_sitemap = self.update_sitemap(
                original_sitemap, route, remove=True
            )

            self.write_text_atomic(listing_path, updated_listing)
            self.write_text_atomic(sitemap_path, updated_sitemap)
            shutil.rmtree(project_dir)
        except (OSError, UnicodeError, ValueError, ET.ParseError) as error:
            rollback_errors = []
            for path, original in (
                (listing_path, locals().get("original_listing")),
                (sitemap_path, locals().get("original_sitemap")),
            ):
                if original is None or not os.path.exists(path):
                    continue
                try:
                    with open(path, "r", encoding="utf-8") as current_file:
                        if current_file.read() != original:
                            self.write_text_atomic(path, original)
                except (OSError, UnicodeError) as rollback_error:
                    rollback_errors.append(f"Could not restore {path}: {rollback_error}")
            detail = " ".join(rollback_errors)
            self.set_status(f"Could not remove project page: {error} {detail}".strip())
            return

        self.pending_thumbnails.pop(project, None)
        self.load_gallery_pages()
        self.set_status(f"Removed '{project}', its page, and its images.")

    def load_gallery(self, page):
        html_path = os.path.join(self.base_dir, self.page_image_folders[page][0])
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
        except (OSError, UnicodeError) as error:
            self.set_status(f"Could not read {page}: {error}")
            return False
        container = self.find_gallery_container(soup)
        if not container:
            self.set_status(f"{page} no longer contains the expected image grid.")
            return False

        self.gallery_images = []
        normalized_sources = False
        missing_sources = []
        for image in container.find_all("img", src=True):
            source = self.normalize_image_source(image["src"], page)
            normalized_sources = normalized_sources or source != image["src"]
            if (
                source
                and not urlsplit(source).scheme
                and not self.resolve_local_image_source(
                    source, self.page_image_folders[page][0]
                )
            ):
                missing_sources.append(source)
            self.gallery_images.append((source, image.get("alt", "")))
        original_images = list(self.gallery_images)
        self.gallery_images.sort(key=lambda image: image_year_sort_key(image[0]))
        year_order_changed = self.gallery_images != original_images
        self.current_page = page
        self.gallery_dirty = normalized_sources or year_order_changed
        self.render_gallery()
        self.gallery_heading.configure(
            text=f"{page} — {len(self.gallery_images)} image(s) "
            "(Ctrl/Shift-click to select multiple)"
        )
        if year_order_changed:
            self.set_status(
                "Gallery images ordered by year, newest first. "
                "Save gallery changes to apply the order."
            )
        elif normalized_sources:
            self.set_status("Local image URLs were corrected. Save gallery changes to apply them.")
        if missing_sources:
            order_note = (
                " Gallery order also changed; save gallery changes to apply it."
                if year_order_changed
                else ""
            )
            self.set_status(
                f"{len(missing_sources)} gallery image file(s) could not be found. "
                f"Check the image paths in the list.{order_note}"
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

        existing_sources = {
            self.normalize_image_source(source, self.current_page)
            for source, _ in self.gallery_images
        }
        added_indices = []
        errors = []
        for source_path in selected_files:
            extension = os.path.splitext(source_path)[1].lower()
            if extension not in GALLERY_EXTENSIONS:
                errors.append(f"Unsupported image type: {source_path}")
                continue
            try:
                with Image.open(source_path) as image:
                    image.verify()
            except (
                OSError,
                ValueError,
                EOFError,
                SyntaxError,
                Image.DecompressionBombError,
            ) as error:
                errors.append(f"Could not read image {source_path}: {error}")
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

            relative_path = self.relative_url_for_file(
                target_path, self.page_image_folders[self.current_page][0]
            )
            if relative_path in existing_sources:
                continue

            if (
                self.strip_added_metadata_var.get()
                and source_dir != target_dir_abs
            ):
                success, detail = strip_image_metadata(target_path)
                if not success:
                    errors.append(
                        f"Added {relative_path}, but metadata stripping failed: "
                        f"{detail}"
                    )

            self.gallery_images.append(
                (relative_path, self.clean_alt_text(os.path.basename(target_path)))
            )
            added_indices.append(relative_path)
            existing_sources.add(relative_path)

        if added_indices:
            added_sources = set(added_indices)
            self.gallery_images.sort(
                key=lambda image: image_year_sort_key(image[0])
            )
            added_indices = [
                index
                for index, image in enumerate(self.gallery_images)
                if image[0] in added_sources
            ]
            self.gallery_dirty = True
            self.render_gallery(added_indices)
            if not self.save_gallery():
                error_message = self.status_label.cget("text")
                self.set_status(
                    f"Copied {len(added_indices)} image(s), but could not save "
                    f"the gallery: {error_message}"
                )
                return

        thumbnail_status = ""
        if self.thumbnail_dirty and self.current_page.startswith("/projecten/"):
            if self.save_project_thumbnail():
                thumbnail_status = " Project card image saved."
            else:
                thumbnail_status = (
                    " Gallery saved, but project card image could not be saved: "
                    f"{self.status_label.cget('text')}"
                )
        message = f"Added {len(added_indices)} image(s) to {self.current_page}."
        if added_indices:
            message += " Gallery saved."
        message += thumbnail_status
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
        path = os.path.join(self.base_dir, self.page_image_folders[self.current_page][0])
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
        for project, (route, _image_folder) in self.project_thumbnails.items():
            if route == self.current_page and project == self.current_project:
                self.load_project_thumbnail_options(project)
                break
        return True

    def change_project(self, project):
        if project not in self.project_thumbnails or project == self.current_project:
            return
        previous_project = self.current_project
        if self.project_text_dirty and not self.save_project_text():
            self.project_menu.set(previous_project)
            return
        if self.thumbnail_dirty and not self.save_project_thumbnail():
            self.project_menu.set(previous_project)
            return
        self.load_project_thumbnail_options(project)
        self.load_project_text(project)

    def load_project_thumbnail_options(self, project):
        self.current_project = project
        route, image_folder = self.project_thumbnails[project]
        html_path = os.path.join(self.base_dir, "projecten", "index.html")
        html_relative_path = "projecten/index.html"
        try:
            with open(html_path, "r", encoding="utf-8") as html_file:
                soup = BeautifulSoup(html_file.read(), "html.parser")
            card = self.find_project_card(soup, route)
            if not card:
                raise ValueError(f"Could not find the project card for {project}.")
            card_image = self.find_project_card_image(soup, route)
            original_thumbnail_src = card_image.get("src", "") if card_image else ""
            current_file_path = self.resolve_local_image_source(
                original_thumbnail_src, html_relative_path
            )
            self.current_thumbnail_src = (
                self.relative_url_for_file(current_file_path, html_relative_path)
                if current_file_path
                else original_thumbnail_src
            )
        except (OSError, UnicodeError, ValueError) as error:
            self.set_status(f"Could not read project thumbnail: {error}")
            return

        directory = os.path.join(self.base_dir, image_folder)
        try:
            file_paths = sorted(
                (
                    os.path.join(directory, filename)
                    for filename in os.listdir(directory)
                    if os.path.splitext(filename)[1].lower() in GALLERY_EXTENSIONS
                ),
                key=image_year_sort_key,
            )
        except OSError as error:
            self.set_status(f"Could not read {image_folder}: {error}")
            file_paths = []

        self.project_image_options = {
            os.path.basename(path): self.relative_url_for_file(path, html_relative_path)
            for path in file_paths
        }
        current_file_path = self.resolve_local_image_source(
            self.current_thumbnail_src, html_relative_path
        )
        if (
            self.current_thumbnail_src
            and self.current_thumbnail_src not in self.project_image_options.values()
        ):
            label = "Current thumbnail" if current_file_path else "Missing thumbnail image"
            self.project_image_options[label] = self.current_thumbnail_src
        options = list(self.project_image_options) or ["No images found"]
        for special_label in ("Current thumbnail", "Missing thumbnail image"):
            if special_label in self.project_image_options:
                options = [special_label] + [
                    label for label in options if label != special_label
                ]
        pending_source = self.pending_thumbnails.get(
            project, self.current_thumbnail_src
        )
        available_sources = set(self.project_image_options.values())
        if pending_source and pending_source not in available_sources:
            self.pending_thumbnails.pop(project, None)
            pending_source = self.current_thumbnail_src
        selected = next(
            (
                label
                for label, source in self.project_image_options.items()
                if source == pending_source
            ),
            options[0],
        )
        self.thumbnail_menu.configure(values=options)
        self.thumbnail_menu.set(selected)
        self.thumbnail_dirty = pending_source != self.current_thumbnail_src
        if (
            not self.current_thumbnail_src
            and not self.pending_thumbnails.get(project)
            and file_paths
        ):
            self.pending_thumbnails[project] = self.project_image_options[options[0]]
            self.thumbnail_menu.set(options[0])
            self.thumbnail_dirty = True
            pending_source = self.pending_thumbnails[project]
        self.thumbnail_path_label.configure(
            text=(
                f"Current selection: {self.thumbnail_menu.get()}"
                if selected != "No images found"
                else "No images yet. Add an image in the Galleries tab."
            )
        )
        self.update_thumbnail_preview(pending_source)
        if original_thumbnail_src != self.current_thumbnail_src:
            self.pending_thumbnails[project] = self.current_thumbnail_src
            self.thumbnail_dirty = True
            self.set_status(
                "The project card image URL was corrected for local viewing. "
                "Save project card image to apply it."
            )
        elif not file_paths:
            self.set_status(
                f"No images found for {project}. Add images in the Galleries tab first."
            )
        else:
            self.set_status(f"Choose a project card image for {project}.")

    @staticmethod
    def find_project_card_image(soup, route):
        card = ImageSyncApp.find_project_card(soup, route)
        if not card:
            return None
        wrapper = card.find("div", class_="project-image-wrapper")
        return wrapper.find("img") if wrapper else None

    @staticmethod
    def find_project_card(soup, route):
        slug = route.rstrip("/").rsplit("/", 1)[-1]
        for link in soup.find_all("a", class_="project-link", href=True):
            href = link["href"].strip("/")
            if href not in {slug, f"projecten/{slug}"}:
                continue
            return link
        return None

    def select_thumbnail_image(self, label):
        source = self.project_image_options.get(label)
        if not source:
            self.update_thumbnail_preview("")
            return
        self.pending_thumbnails[self.current_project] = source
        self.thumbnail_dirty = source != self.current_thumbnail_src
        self.thumbnail_path_label.configure(text=f"Selected: {label}")
        self.update_thumbnail_preview(source)

    def save_project_thumbnail(self):
        if self.current_project not in self.project_thumbnails:
            self.set_status("Select a project page first.")
            return False
        label = self.thumbnail_menu.get()
        source = self.project_image_options.get(label)
        if not source or label == "No images found":
            self.set_status("No thumbnail image is selected.")
            return False
        if not self.resolve_local_image_source(source, "projecten/index.html"):
            self.set_status(f"Thumbnail file does not exist: {source}")
            return False
        route, _ = self.project_thumbnails[self.current_project]
        path = os.path.join(self.base_dir, "projecten", "index.html")
        temp_path = None
        try:
            with open(path, "r", encoding="utf-8") as html_file:
                soup = BeautifulSoup(html_file.read(), "html.parser")
            image = self.find_project_card_image(soup, route)
            if not image:
                card = self.find_project_card(soup, route)
                wrapper = card.find("div", class_="project-image-wrapper") if card else None
                if not wrapper:
                    raise ValueError(
                        f"Could not find the project card for {self.current_project}."
                    )
                image = soup.new_tag("img")
                image["alt"] = f"{self.current_project} project thumbnail"
                wrapper.append(image)
            image["src"] = source
            if not image.get("alt"):
                image["alt"] = f"{self.current_project} project thumbnail"
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
        self.pending_thumbnails[self.current_project] = source
        self.thumbnail_path_label.configure(text=f"Saved: {label}")
        self.update_thumbnail_preview(source)
        self.set_status(
            f"Saved {self.current_project} project card image."
        )
        return True

    def update_thumbnail_preview(self, source):
        if not source:
            self.preview_photo = None
            self.thumbnail_preview.configure(
                image=None,
                text="Add an image in Galleries to choose a project card image.",
            )
            return
        file_path = self.resolve_local_image_source(source, "projecten/index.html")
        if not file_path:
            self.preview_photo = None
            self.thumbnail_preview.configure(
                image=None,
                text="Image file is missing or cannot be previewed locally.",
            )
            return
        try:
            with Image.open(file_path) as image:
                preview = image.convert("RGBA")
                preview.thumbnail((250, 250))
            self.preview_photo = ctk.CTkImage(
                light_image=preview,
                dark_image=preview,
                size=preview.size,
            )
            self.thumbnail_preview.configure(image=self.preview_photo, text="")
        except (OSError, ValueError) as error:
            self.preview_photo = None
            self.thumbnail_preview.configure(
                image=None, text=f"Could not preview image: {error}"
            )

    def close_app(self):
        if self.project_text_dirty and not self.save_project_text():
            return
        if self.gallery_dirty and not self.save_gallery():
            return
        if self.thumbnail_dirty and not self.save_project_thumbnail():
            return
        self.destroy()


if __name__ == "__main__":
    app = ImageSyncApp()
    app.mainloop()
