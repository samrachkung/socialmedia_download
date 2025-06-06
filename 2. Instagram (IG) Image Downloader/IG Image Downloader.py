import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from subprocess import Popen, PIPE
from datetime import datetime
import webbrowser

# Global configuration and state
DOWNLOAD_FOLDER = os.path.expanduser("~")  # Default download folder: user's home
PAUSED = False   # When True, new downloads will wait before starting
STOP = False     # When True, in-progress downloads will be terminated
TOTAL_COUNT = 0
SUCCESS_COUNT = 0
ERROR_COUNT = 0

# Instagram-themed color scheme
PRIMARY_COLOR = "#C13584"    # Instagram purple/pink
SECONDARY_COLOR = "#E1306C"  # Instagram pink
ACCENT_COLOR = "#833AB4"     # Instagram purple
BG_COLOR = "#FAFAFA"         # Instagram light gray background
TEXT_COLOR = "#262626"       # Instagram dark gray text

# Modern font configuration
FONT_FAMILY = "Inter" if os.name == "nt" else "SF Pro Display"  # Modern fonts
FONT_REGULAR = (FONT_FAMILY, 11)
FONT_MEDIUM = (FONT_FAMILY, 11, "normal")
FONT_BOLD = (FONT_FAMILY, 11, "bold")
FONT_HEADER = (FONT_FAMILY, 16, "bold")
BUTTON_FONT = (FONT_FAMILY, 10, "bold")  # Bold font specifically for buttons

class ModernButton(tk.Button):
    """Custom button class with modern styling"""
    def __init__(self, master, text, command=None, custom_bg=None, is_action_button=True):
        bg_color = custom_bg if custom_bg else PRIMARY_COLOR
        # Text color based on button type
        text_color = "white"  # White text for better contrast
        hover_color = SECONDARY_COLOR if is_action_button else ACCENT_COLOR
        
        super().__init__(
            master,
            text=text,
            command=command,
            font=BUTTON_FONT,  # Using bold font for buttons
            bg=bg_color,
            fg=text_color,
            activebackground=hover_color,
            activeforeground=text_color,
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.default_bg = bg_color
        self.default_fg = text_color
        self.hover_bg = hover_color
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self.config(bg=self.hover_bg)

    def on_leave(self, e):
        self.config(bg=self.default_bg)

def open_facebook(event=None):
    webbrowser.open("https://www.facebook.com/sorithyacreator")

def open_telegram(event=None):
    webbrowser.open("https://t.me/mmotoolcollection")

def open_contact(event=None):
    webbrowser.open("https://t.me/SorithyaDigital")

class InstagramPhotoDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram Image Downloader (Images Only)")
        self.root.configure(bg=BG_COLOR)
        
        # Variables
        self.save_folder = DOWNLOAD_FOLDER
        self.process = None
        self.url_queue = []
        
        # Configure ttk styles for progress bar
        self.setup_styles()
        self.setup_ui()

    def setup_styles(self):
        """Configure custom styles for ttk widgets"""
        self.style = ttk.Style()
        self.style.configure(
            "Instagram.Horizontal.TProgressbar",
            troughcolor="#EFEFEF",
            background=ACCENT_COLOR,
            thickness=20
        )

    def setup_ui(self):
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        
        # Header
        header = tk.Frame(self.root, bg=BG_COLOR)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(10,5))
        header.grid_columnconfigure(0, weight=1)
        
        # Logo and title container
        title_logo_frame = tk.Frame(header, bg=BG_COLOR)
        title_logo_frame.grid(row=0, column=0, sticky="ew")
        title_logo_frame.grid_columnconfigure(0, weight=1)

        # Title and logo side by side
        title = tk.Label(
            title_logo_frame,
            text="Instagram Image Downloader (Images Only)",
            font=(FONT_FAMILY, 25, "bold"),
            bg=BG_COLOR,
            fg=PRIMARY_COLOR
        )
        title.grid(row=0, column=0, sticky="w")

        # Logo
        try:
            self.logo_img = tk.PhotoImage(file="instagram_logo.png")
            logo_label = tk.Label(title_logo_frame, image=self.logo_img, bg=BG_COLOR)
            logo_label.grid(row=0, column=1, padx=10)
        except Exception as e:
            print("Logo image not found:", e)

        # Date display with month name
        self.date_label = tk.Label(
            header,
            font=FONT_REGULAR,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        )
        self.date_label.grid(row=1, column=0, sticky="w")
        self.update_datetime()

        # Main content frame
        main_frame = tk.Frame(self.root, bg=BG_COLOR)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)

        # URL input with label
        url_label = tk.Label(
            main_frame,
            text="Enter Instagram URLs (Posts, Stories, Profiles - one per line): [Videos will be skipped]",
            font=FONT_BOLD,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        )
        url_label.pack(anchor="w")

        # Text widget for URL input
        self.url_text = tk.Text(
            main_frame,
            wrap=tk.WORD,
            font=FONT_REGULAR,
            height=8,
            relief="flat",
            padx=10,
            pady=10,
            bg="#FFFFFF",  # White background for better contrast
            fg=TEXT_COLOR
        )
        self.url_text.pack(fill="both", expand=True, pady=(5,10))

        # Progress frame
        progress_frame = tk.Frame(main_frame, bg=BG_COLOR)
        progress_frame.pack(fill="x", pady=5)
        
        # Progress variable and bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            length=100,
            mode="indeterminate",
            style="Instagram.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill="x", padx=5)

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Total: 0 | Success: 0 | Error: 0",
            font=FONT_REGULAR,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        )
        self.status_label.pack(pady=5)

        # Folder label
        self.folder_label = tk.Label(
            main_frame,
            text=f"Save Folder: {self.save_folder}",
            font=FONT_REGULAR,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        )
        self.folder_label.pack(pady=5)

        # Console output
        console_label = tk.Label(
            main_frame,
            text="Download Log:",
            font=FONT_BOLD,
            bg=BG_COLOR,
            fg=TEXT_COLOR
        )
        console_label.pack(anchor="w", pady=(10, 5))
        
        self.output_console = tk.Text(
            main_frame,
            wrap=tk.WORD,
            font=FONT_REGULAR,
            height=6,
            relief="flat",
            padx=10,
            pady=10,
            bg="#FFFFFF",
            fg=TEXT_COLOR
        )
        self.output_console.pack(fill="both", pady=(0, 10))
        
        # Add a scrollbar to the console
        scrollbar = tk.Scrollbar(self.output_console)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_console.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.output_console.yview)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg=BG_COLOR)
        button_frame.pack(pady=(10, 20))

        # Centered buttons with specific spacing
        ModernButton(
            button_frame,
            text="Save To Folder",
            command=self.browse_folder,
            is_action_button=True
        ).pack(side="left", padx=3)

        ModernButton(
            button_frame,
            text="Download Images Only",
            command=self.start_download,
            is_action_button=True
        ).pack(side="left", padx=3)

        # Stop button
        ModernButton(
            button_frame,
            text="Stop",
            command=self.stop_download,
            custom_bg=ACCENT_COLOR,
            is_action_button=False
        ).pack(side="left", padx=3)
        
        # Clear button
        ModernButton(
            button_frame,
            text="Clear All",
            command=self.clear_fields,
            custom_bg="#777777",
            is_action_button=False
        ).pack(side="left", padx=3)

        # Footer frame
        footer = tk.Frame(self.root, bg=BG_COLOR)
        footer.grid(row=2, column=0, sticky="ew", padx=20, pady=(5,10))
        footer.grid_columnconfigure(0, weight=1)

        # Creator label
        creator_label = tk.Label(
            footer,
            text="This application created by MMO Tool Collection @ 2025",
            font=(FONT_FAMILY, 9),
            bg=BG_COLOR,
            fg=TEXT_COLOR
        )
        creator_label.grid(row=0, column=0, sticky="w")

        # Social icons frame
        icons_frame = tk.Frame(footer, bg=BG_COLOR)
        icons_frame.grid(row=0, column=1, sticky="e")

        # Load social media icons
        try:
            # Facebook
            self.fb_img = tk.PhotoImage(file="facebook.png")
            fb_label = tk.Label(icons_frame, image=self.fb_img, bg=BG_COLOR, cursor="hand2")
            fb_label.pack(side="left", padx=5)
            fb_label.bind("<Button-1>", open_facebook)

            # Telegram
            self.tg_img = tk.PhotoImage(file="telegram.png")
            tg_label = tk.Label(icons_frame, image=self.tg_img, bg=BG_COLOR, cursor="hand2")
            tg_label.pack(side="left", padx=5)
            tg_label.bind("<Button-1>", open_telegram)

            # Contact
            self.contact_img = tk.PhotoImage(file="contact.png")
            contact_label = tk.Label(icons_frame, image=self.contact_img, bg=BG_COLOR, cursor="hand2")
            contact_label.pack(side="left", padx=5)
            contact_label.bind("<Button-1>", open_contact)
        except Exception as e:
            print("Could not load social media icons:", e)

    def update_datetime(self):
        """Update date/time with month name format"""
        now = datetime.now()
        formatted_time = now.strftime("%B %d, %Y %I:%M:%S %p")
        self.date_label.config(text=formatted_time)
        self.root.after(1000, self.update_datetime)

    def browse_folder(self):
        """Open a dialog to choose the download folder."""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.save_folder = folder_selected
            self.folder_label.config(text=f"Save Folder: {self.save_folder}")

    def append_to_console(self, message):
        """Add message to output console and scroll to the end"""
        self.output_console.config(state="normal")
        self.output_console.insert(tk.END, message + "\n")
        self.output_console.see(tk.END)
        self.output_console.config(state="disabled")
        
        # Update the main window to show changes immediately
        self.root.update_idletasks()

    def clear_output_console(self):
        """Clear the output console"""
        self.output_console.config(state="normal")
        self.output_console.delete("1.0", tk.END)
        self.output_console.config(state="disabled")

    def start_download(self):
        """Start downloading photos (images only) from entered URLs"""
        urls = self.url_text.get("1.0", tk.END).strip().split("\n")
        
        if not urls or all(url.strip() == "" for url in urls):
            messagebox.showerror("Error", "Please enter at least one valid Instagram URL.")
            return

        if not self.save_folder:
            messagebox.showerror("Error", "Please select a save folder.")
            return

        # Reset counters
        global TOTAL_COUNT, SUCCESS_COUNT, ERROR_COUNT, STOP
        TOTAL_COUNT = len([url for url in urls if url.strip()])
        SUCCESS_COUNT = 0
        ERROR_COUNT = 0
        STOP = False
        
        # Update UI
        self.status_label.config(text=f"Total: {TOTAL_COUNT} | Success: {SUCCESS_COUNT} | Error: {ERROR_COUNT}")
        
        # Clear console and start indeterminate progress
        self.clear_output_console()
        self.append_to_console("Starting downloads (images only, videos will be skipped)...")
        self.progress_bar.start(10)  # Start animation
        
        # Queue up valid URLs
        self.url_queue = [url.strip() for url in urls if url.strip()]
        
        # Start downloading URLs sequentially in a separate thread
        threading.Thread(target=self.download_urls_sequentially, daemon=True).start()

    def stop_download(self):
        """Stop all downloads and reset UI"""
        global STOP
        STOP = True
        
        if self.process:
            try:
                self.process.terminate()
            except:
                pass
                
        self.append_to_console("All downloads stopped by user.")
        self.progress_bar.stop()  # Stop animation

    def clear_fields(self):
        """Clear all input fields and console"""
        self.url_text.delete("1.0", tk.END)
        self.clear_output_console()
        self.progress_bar.stop()
        
        # Reset counters
        global TOTAL_COUNT, SUCCESS_COUNT, ERROR_COUNT
        TOTAL_COUNT = SUCCESS_COUNT = ERROR_COUNT = 0
        self.status_label.config(text=f"Total: {TOTAL_COUNT} | Success: {SUCCESS_COUNT} | Error: {ERROR_COUNT}")

    def download_urls_sequentially(self):
        """Process each URL in the queue sequentially"""
        global SUCCESS_COUNT, ERROR_COUNT, STOP

        while self.url_queue and not STOP:
            url = self.url_queue.pop(0)
            self.append_to_console(f"Downloading from: {url}")
            success = self.run_gallery_dl(url, self.save_folder)
            
            if success:
                SUCCESS_COUNT += 1
            else:
                ERROR_COUNT += 1
                
            # Update status
            self.status_label.config(text=f"Total: {TOTAL_COUNT} | Success: {SUCCESS_COUNT} | Error: {ERROR_COUNT}")

        # Finish up
        self.progress_bar.stop()
        
        if not STOP:
            self.append_to_console("All downloads completed.")
            messagebox.showinfo("Download Complete", "All downloads finished!")
            try:
                os.startfile(self.save_folder)
            except Exception as e:
                print(f"Could not open folder: {e}")

    
    def run_gallery_dl(self, url, folder):
        """Run gallery-dl command to download Instagram content (images only)"""
        try:
            # Construct gallery-dl command with Instagram-specific options and image-only filter
            command = [
               "gallery-dl.exe",
                "--destination", folder,
                # Save metadata (includes captions)
                "--write-metadata",
                # Optional: Save caption in filename (adjust as needed)
                # "--filter", "filename = '{caption[:50]}_{media_id}.{extension}'",
                # Image-only filter (skip videos)
                "--filter", "extension in ['jpg', 'jpeg', 'png', 'gif', 'webp']",
                # Instagram-specific options (login if needed)
                "--cookies", "cookies.txt",  # Optional: for private content
                url
            ]

            # Run gallery-dl
            self.process = Popen(command, stdout=PIPE, stderr=PIPE, text=True)

            while True:
                if STOP:
                    break

                output = self.process.stdout.readline()
                if output == '' and self.process.poll() is not None:
                    break

                if output:
                    output_text = output.strip()
                    self.append_to_console(output_text)
                    
                    # Add a note when videos are skipped
                    if "extension not in" in output_text.lower() or ".mp4" in output_text.lower() or "video" in output_text.lower():
                        self.append_to_console("⚠️ Video file detected - skipping (images only mode)")

            # Check for errors
            if self.process.returncode != 0 and not STOP:
                error_output = self.process.stderr.read()
                self.append_to_console(f"Error: {error_output}")
                return False
            elif STOP:
                return False
            else:
                self.append_to_console(f"Successfully downloaded from {url}")
                return True

        except Exception as e:
            self.append_to_console(f"Error: {str(e)}")
            return False

    def extract_caption_from_json(self, json_path):
        """Extract description/caption from gallery-dl's JSON metadata file"""
        try:
            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("description", "").strip()  # Return caption if exists
        except Exception as e:
            self.append_to_console(f"⚠️ Failed to read {json_path}: {str(e)}")
            return ""

    def save_caption_as_txt(self, image_path, caption):
        """Save caption as a .txt file with the same name as the image"""
        if not caption:
            return False
        
        try:
            txt_path = os.path.splitext(image_path)[0] + ".txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(caption)
            return True
        except Exception as e:
            self.append_to_console(f"⚠️ Failed to save caption: {str(e)}")
            return False
def main():
    root = tk.Tk()
    root.minsize(600, 600)
    try:
        root.iconbitmap("instagram.ico")
    except:
        pass
    app = InstagramPhotoDownloader(root)
    root.mainloop()

if __name__ == "__main__":
    main()