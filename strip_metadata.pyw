import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import piexif

# Set GUI theme and color scheme
ctk.set_appearance_mode("System")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".tif", ".tiff", ".bmp"}


def strip_image_metadata(file_path):
    """
    Strips metadata/EXIF from the given image file.
    Saves the file in-place safely using a temporary file.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    # Method 1: JPEG / TIFF via piexif (Lossless, no re-encoding)
    if ext in {".jpg", ".jpeg", ".tif", ".tiff"}:
        try:
            piexif.remove(file_path)
            return True, "EXIF removed losslessly via piexif"
        except Exception:
            # Fallback to Pillow if piexif encounters an unhandled JPEG structure
            pass

    # Method 2: Universal Pillow method for PNG, WEBP, GIF, BMP, JPEG fallback
    try:
        with Image.open(file_path) as img:
            # Copy raw pixel data into a new clean image object
            data = list(img.getdata())
            clean_img = Image.new(img.mode, img.size)
            clean_img.putdata(data)
            
            # Save to temporary file first to prevent corruption
            temp_path = file_path + ".tmp"
            
            # Match original format options
            save_args = {}
            if ext in {".jpg", ".jpeg"}:
                save_args["quality"] = 95
            elif ext == ".webp":
                save_args["quality"] = 95
            
            clean_img.save(temp_path, **save_args)

        # Overwrite original file
        os.replace(temp_path, file_path)
        return True, "Metadata stripped successfully"

    except Exception as e:
        if os.path.exists(file_path + ".tmp"):
            os.remove(file_path + ".tmp")
        return False, str(e)


class ExifStripperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Batch EXIF / Metadata Stripper")
        self.geometry("600 x 480")
        self.resizable(False, False)

        self.selected_directory = ""
        self.is_processing = False

        # --- UI Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # Title Label
        self.title_label = ctk.CTkLabel(
            self, 
            text="Image EXIF & Metadata Stripper", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Subtitle / Info
        self.info_label = ctk.CTkLabel(
            self, 
            text="Supports PNG, JPG, JPEG, GIF, WEBP, TIFF, BMP (includes subdirectories)",
            font=ctk.CTkFont(size=12)
        )
        self.info_label.grid(row=1, column=0, padx=20, pady=(0, 15))

        # Directory Selector Frame
        self.dir_frame = ctk.CTkFrame(self)
        self.dir_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.dir_frame.grid_columnconfigure(0, weight=1)

        self.dir_entry = ctk.CTkEntry(
            self.dir_frame, 
            placeholder_text="No directory selected..."
        )
        self.dir_entry.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")

        self.browse_btn = ctk.CTkButton(
            self.dir_frame, 
            text="Browse Folder", 
            width=120, 
            command=self.browse_folder
        )
        self.browse_btn.grid(row=0, column=1, padx=(5, 10), pady=10)

        # Process Button
        self.start_btn = ctk.CTkButton(
            self, 
            text="Strip Metadata From All Images", 
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#D32F2F", 
            hover_color="#B71C1C",
            height=40,
            command=self.start_processing_thread
        )
        self.start_btn.grid(row=3, column=0, padx=20, pady=15, sticky="ew")

        # Progress Bar & Status
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=4, column=0, padx=20, pady=(5, 5), sticky="ew")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self, text="Ready", font=ctk.CTkFont(size=11))
        self.status_label.grid(row=5, column=0, padx=20, pady=(0, 5), sticky="n")

        # Log Text Area
        self.log_textbox = ctk.CTkTextbox(self, height=140)
        self.log_textbox.grid(row=6, column=0, padx=20, pady=(5, 20), sticky="ew")

    def log(self, message):
        """Append text to the log box."""
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")

    def browse_folder(self):
        """Open native folder picker."""
        folder = filedialog.askdirectory()
        if folder:
            self.selected_directory = folder
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, folder)
            self.status_label.configure(text=f"Selected: {folder}")

    def start_processing_thread(self):
        """Runs the processing in a separate thread to keep UI responsive."""
        if not self.selected_directory or not os.path.isdir(self.selected_directory):
            messagebox.showwarning("Warning", "Please select a valid directory first!")
            return

        if self.is_processing:
            return

        self.is_processing = True
        self.start_btn.configure(state="disabled")
        self.browse_btn.configure(state="disabled")
        self.log_textbox.delete("1.0", "end")
        
        # Start worker thread
        threading.Thread(target=self.process_images, daemon=True).start()

    def process_images(self):
        """Traverses directory recursively and strips EXIF data."""
        self.log(f"Scanning directory: {self.selected_directory}\n")

        # Gather all matching images across subdirectories
        image_files = []
        for root, _, files in os.walk(self.selected_directory):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    image_files.append(os.path.join(root, file))

        total_files = len(image_files)

        if total_files == 0:
            self.log("No supported image files found in the selected folder.")
            self.status_label.configure(text="No images found.")
            self.finish_processing()
            return

        self.log(f"Found {total_files} image(s) to process.\n" + "-" * 50)

        success_count = 0
        error_count = 0

        for idx, file_path in enumerate(image_files, start=1):
            rel_path = os.path.relpath(file_path, self.selected_directory)
            self.status_label.configure(text=f"Processing [{idx}/{total_files}]: {rel_path}")
            
            success, message = strip_image_metadata(file_path)

            if success:
                success_count += 1
                self.log(f"[OK] {rel_path}")
            else:
                error_count += 1
                self.log(f"[ERROR] {rel_path} -> {message}")

            # Update progress bar on UI thread
            self.progress_bar.set(idx / total_files)

        self.log("-" * 50)
        self.log(f"Finished! Successfully stripped: {success_count} | Failed: {error_count}")
        self.status_label.configure(text="Processing complete!")
        
        self.finish_processing()

    def finish_processing(self):
        """Reset UI state after completion."""
        self.is_processing = False
        self.start_btn.configure(state="normal")
        self.browse_btn.configure(state="normal")


if __name__ == "__main__":
    app = ExifStripperApp()
    app.mainloop()