import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from moviepy.editor import *
import threading
from moviepy.video.fx.mirror_x import mirror_x
from moviepy.video.fx.speedx import speedx
from moviepy.audio.fx.audio_loop import audio_loop
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, TextClip
from moviepy.config import change_settings
from PIL import Image
import cv2
import numpy as np

change_settings({"IMAGEMAGICK_BINARY": r"C:/Program Files/ImageMagick-7.1.1-Q16-HDRI/magick.exe"})


class VideoEditorGUI:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Video Editor V1.7.6 By @KungSamRach")
        self.root.geometry("675x600")
        self.root.configure(bg="#1A1A2E")  # Dark background for a modern look

        # Enable scrolling
        self.main_canvas = tk.Canvas(self.root, bg="#1A1A2E", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.main_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.main_canvas, style="TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )

        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add mouse scroll functionality
        def _on_mouse_wheel(event):
            self.main_canvas.yview_scroll(-1 * int(event.delta / 120), "units")

        self.main_canvas.bind_all("<MouseWheel>", _on_mouse_wheel)

        # Initialize styles
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TButton", background="#0F3460", foreground="white", font=("JetBrains Mono", 12, "bold"),
                             borderwidth=0)
        self.style.map("TButton", background=[("active", "#16213E")])  # Darker blue on hover
        self.style.configure("TRadiobutton", background="#1A1A2E", foreground="white", font=("JetBrains Mono", 11))
        self.style.configure("TLabel", background="#1A1A2E", foreground="white", font=("JetBrains Mono", 11))
        self.style.configure("TFrame", background="#1A1A2E")
        self.style.configure("TProgressbar", thickness=20, troughcolor="#0F3460", background="#E94560")

        # Initialize variables
        self.video_folder = ""
        self.music_file = ""
        self.logo_file = ""
        self.speed_value = tk.DoubleVar(value=1.0)
        self.output_folder = "./edited"
        self.processing = False
        self.logo_position = tk.StringVar(value="top_left")
        self.logo_opacity = tk.DoubleVar(value=1.0)
        self.logo_size = tk.DoubleVar(value=0.1)
        self.text_content = tk.StringVar()
        self.text_position = tk.StringVar(value="top_left")
        self.text_opacity = tk.DoubleVar(value=1.0)
        self.text_size = tk.IntVar(value=20)

        # Create widgets and output directories
        self.create_widgets()
        self.create_output_dirs()

    def create_output_dirs(self):
        directories = [
            "./edited/flip",
            "./edited/speed",
            "./edited/flip_speed",
            "./edited/add_music",
            "./edited/music_speed",
            "./edited/flip_speed_music",
            "./edited/upscale_basic",
            "./edited/upscale_hd",
            "./edited/cut_video",
            "./edited/add_logo",
            "./edited/add_text"
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.scrollable_frame, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Editor", font=("JetBrains Mono", 20, "bold"))
        title_label.pack(pady=(0, 20))

        # Input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=10)

        # Video folder selection
        folder_label = ttk.Label(input_frame, text="📁 Folder:")
        folder_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.folder_path = tk.StringVar()
        folder_entry = ttk.Entry(input_frame, textvariable=self.folder_path, width=50)
        folder_entry.grid(row=0, column=1, padx=5, pady=5)

        browse_button = ttk.Button(input_frame, text="Browse", command=self.browse_folder)
        browse_button.grid(row=0, column=2, padx=5, pady=5)

        # Music file selection
        music_label = ttk.Label(input_frame, text="🎵 Music File:")
        music_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.music_path = tk.StringVar()
        music_entry = ttk.Entry(input_frame, textvariable=self.music_path, width=50)
        music_entry.grid(row=1, column=1, padx=5, pady=5)

        music_button = ttk.Button(input_frame, text="Browse", command=self.browse_music)
        music_button.grid(row=1, column=2, padx=5, pady=5)

        # Speed control
        speed_frame = ttk.Frame(main_frame)
        speed_frame.pack(fill=tk.X, pady=10)

        speed_label = ttk.Label(speed_frame, text="⏩ Speed:")
        speed_label.pack(side=tk.LEFT, padx=5)

        speed_scale = ttk.Scale(speed_frame, from_=0.1, to=5.0, orient=tk.HORIZONTAL,
                                variable=self.speed_value, length=300)
        speed_scale.pack(side=tk.LEFT, padx=5)

        speed_value_label = ttk.Label(speed_frame, text=f"{self.speed_value.get():.1f}x")
        speed_value_label.pack(side=tk.LEFT, padx=5)

        def update_speed_label(*args):
            speed_value_label.config(text=f"{self.speed_value.get():.1f}x")

        self.speed_value.trace_add("write", update_speed_label)

        # Options and Configuration frame
        options_frame = ttk.LabelFrame(main_frame, text="🎛️ Edit Options & Configuration", padding=10)
        options_frame.pack(fill=tk.BOTH, pady=10, expand=True)

        self.edit_option = tk.StringVar(value="flip")

        # Edit options
        options = [
            ("Flip Horizontal", "flip"),
            ("Change Speed", "speed"),
            ("Flip & Speed", "flip_speed"),
            ("Add Music", "add_music"),
            ("Speed & Music", "speed_music"),
            ("Flip, Speed & Music", "flip_speed_music"),
            ("Upscale (Basic)", "upscale_basic"),
            ("Upscale (HD)", "upscale_hd"),
            ("Cut Video Long", "cut_video"),
            ("Add Logo", "add_logo"),
            ("Add Text", "add_text")
        ]

        options_frame_inner = ttk.Frame(options_frame)
        options_frame_inner.pack(fill=tk.BOTH, expand=True)

        for i, (text, value) in enumerate(options):
            rb = ttk.Radiobutton(options_frame_inner, text=text, value=value, variable=self.edit_option)
            rb.grid(row=i // 2, column=i % 2, padx=10, pady=5, sticky="w")

        # Logo configuration
        logo_frame = ttk.LabelFrame(options_frame, text="🖼️ Logo Configuration", padding=10)
        logo_frame.pack(fill=tk.BOTH, pady=10, expand=True)

        logo_label = ttk.Label(logo_frame, text="Logo File:")
        logo_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.logo_path = tk.StringVar()
        logo_entry = ttk.Entry(logo_frame, textvariable=self.logo_path, width=40)
        logo_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        logo_button = ttk.Button(logo_frame, text="Browse", command=self.browse_logo)
        logo_button.grid(row=0, column=2, padx=5, pady=5)

        position_label = ttk.Label(logo_frame, text="Position:")
        position_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        positions = ["top_left", "top_center", "top_right", "bottom_left", "bottom_center", "bottom_right", "center"]
        position_menu = ttk.Combobox(logo_frame, textvariable=self.logo_position, values=positions, state="readonly")
        position_menu.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        opacity_label = ttk.Label(logo_frame, text="Opacity (0-1):")
        opacity_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        opacity_scale = ttk.Scale(logo_frame, from_=0, to=1, orient=tk.HORIZONTAL, variable=self.logo_opacity)
        opacity_scale.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        size_label = ttk.Label(logo_frame, text="Size (% of height):")
        size_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        size_scale = ttk.Scale(logo_frame, from_=0.05, to=0.5, orient=tk.HORIZONTAL, variable=self.logo_size)
        size_scale.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Text configuration
        text_frame = ttk.LabelFrame(options_frame, text="✍️ Text Configuration", padding=10)
        text_frame.pack(fill=tk.BOTH, pady=10, expand=True)

        text_content_label = ttk.Label(text_frame, text="Text Content:")
        text_content_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        text_entry = ttk.Entry(text_frame, textvariable=self.text_content, width=40)
        text_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        text_position_label = ttk.Label(text_frame, text="Position:")
        text_position_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        text_position_menu = ttk.Combobox(text_frame, textvariable=self.text_position, values=positions,
                                          state="readonly")
        text_position_menu.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        text_opacity_label = ttk.Label(text_frame, text="Opacity (0-1):")
        text_opacity_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        text_opacity_scale = ttk.Scale(text_frame, from_=0, to=1, orient=tk.HORIZONTAL, variable=self.text_opacity)
        text_opacity_scale.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        text_size_label = ttk.Label(text_frame, text="Font Size:")
        text_size_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        text_size_entry = ttk.Entry(text_frame, textvariable=self.text_size, width=10)
        text_size_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)

        self.status_label = ttk.Label(status_frame, text="Ready", font=("JetBrains Mono", 11))
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.progress = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL, length=300, mode="determinate")
        self.progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)

        process_button = ttk.Button(button_frame, text="🚀 Start Processing", command=self.process_videos)
        process_button.pack(pady=10)

    def browse_logo(self):
        logo_file = filedialog.askopenfilename(title="Select Logo File",
                                               filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if logo_file:
            self.logo_path.set(logo_file)
            self.logo_file = logo_file

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self.folder_path.set(folder)
            self.video_folder = folder

    def browse_music(self):
        music_file = filedialog.askopenfilename(title="Select Music File",
                                                filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.aac")])
        if music_file:
            self.music_path.set(music_file)
            self.music_file = music_file

    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def get_clip_list(self, file_list):
        return [file for file in file_list if file.lower().endswith((".mp4", ".mkv", ".png", ".jpg", ".jpeg", ".bmp"))]

    def process_videos(self):
        if self.processing:
            messagebox.showwarning("Warning", "Processing is already in progress!")
            return

        if not self.video_folder:
            messagebox.showerror("Error", "Please select a video folder!")
            return

        edit_option = self.edit_option.get()

        if ("music" in edit_option) and not self.music_file:
            messagebox.showerror("Error", "Please select a music file!")
            return

        if edit_option == "add_logo" and not self.logo_file:
            messagebox.showerror("Error", "Please select a logo file!")
            return

        if edit_option == "add_text" and not self.text_content.get().strip():
            messagebox.showerror("Error", "Please enter text content!")
            return

        # Start processing in a separate thread
        threading.Thread(target=self.process, daemon=True).start()

    def process(self):
        self.processing = True

        try:
            file_list = os.listdir(self.video_folder)
            clip_list = self.get_clip_list(file_list)

            if not clip_list:
                self.update_status("No videos/images files found!")
                messagebox.showinfo("Info", "No video or image files found in the selected folder.")
                self.processing = False
                return

            self.update_status(f"Found {len(clip_list)} videos/images")

            edit_option = self.edit_option.get()
            speed_value = self.speed_value.get()

            output_dir = f"./edited/{edit_option}"
            os.makedirs(output_dir, exist_ok=True)

            self.progress["maximum"] = len(clip_list)
            self.progress["value"] = 0

            for i, file in enumerate(clip_list):
                input_file = os.path.join(self.video_folder, file)
                file_ext = os.path.splitext(file)[1].lower()

                # Determine if file is video or image
                is_video = file_ext in (".mp4", ".mkv")

                # Set appropriate output extension
                if is_video:
                    output_ext = ".mp4"
                else:
                    output_ext = file_ext

                output_file = os.path.join(output_dir, f"{os.path.splitext(file)[0]}{output_ext}")

                if os.path.exists(output_file):
                    self.update_status(f"File {file} already exists, skipping...")
                    self.progress["value"] = i + 1
                    self.root.update_idletasks()
                    continue

                self.update_status(f"Processing: {file}")

                try:
                    if edit_option == "flip":
                        self.flip(input_file, output_file)
                    elif edit_option == "speed":
                        self.speed(input_file, speed_value, output_file)
                    elif edit_option == "flip_speed":
                        self.speednflip(input_file, speed_value, output_file)
                    elif edit_option == "add_music":
                        if is_video:
                            self.addmusic(input_file, self.music_file, output_file)
                        else:
                            self.update_status(f"Skipping {file} - cannot add music to images")
                    elif edit_option == "speed_music":
                        if is_video:
                            self.musicnspeed(input_file, self.music_file, speed_value, output_file)
                        else:
                            self.update_status(f"Skipping {file} - cannot add music to images")
                    elif edit_option == "flip_speed_music":
                        if is_video:
                            self.musicnspeednflip(input_file, self.music_file, speed_value, output_file)
                        else:
                            self.update_status(f"Skipping {file} - cannot add music to images")
                    elif edit_option == "upscale_basic":
                        if not is_video:
                            self.upscale_image_basic(input_file, output_file)
                        else:
                            self.update_status(f"Skipping {file} - cannot upscale videos with basic method")
                    elif edit_option == "upscale_hd":
                        if not is_video:
                            self.upscale_image_hd(input_file, output_file)
                        else:
                            self.update_status(f"Skipping {file} - cannot upscale videos with HD method")
                    elif edit_option == "cut_video":
                        if is_video:
                            self.cut_video(input_file, output_dir)
                        else:
                            self.update_status(f"Skipping {file} - cannot cut images")
                    elif edit_option == "add_logo":
                        self.add_logo(input_file, output_file, is_video)
                    elif edit_option == "add_text":
                        self.add_text(input_file, output_file, is_video)

                except Exception as e:
                    self.update_status(f"Error processing {file}: {str(e)}")
                    print(f"Error processing {file}: {str(e)}")

                self.progress["value"] = i + 1
                self.root.update_idletasks()

            self.update_status("Processing complete!")
            messagebox.showinfo("Success", "All videos/images processed successfully!")

        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))

        finally:
            self.processing = False


    def add_logo(self, input_file, output_file, is_video=True):
                """
                Add a logo to a video or image.
                """
                try:
                    if not os.path.exists(input_file):
                        raise FileNotFoundError(f"Input file not found: {input_file}")

                    if not self.logo_file or not os.path.exists(self.logo_file):
                        raise ValueError("Logo file not selected or missing!")

                    clip = VideoFileClip(input_file) if is_video else ImageClip(input_file)
                    logo = ImageClip(self.logo_file).set_opacity(self.logo_opacity.get())

                    # Resize logo
                    logo_height = int(clip.size[1] * self.logo_size.get())
                    logo = logo.resize(height=logo_height)

                    # Position logo
                    positions = {
                        "top_left": (10, 10),
                        "top_center": ((clip.size[0] - logo.size[0]) // 2, 10),
                        "top_right": (clip.size[0] - logo.size[0] - 10, 10),
                        "bottom_left": (10, clip.size[1] - logo.size[1] - 10),
                        "bottom_center": ((clip.size[0] - logo.size[0]) // 2, clip.size[1] - logo.size[1] - 10),
                        "bottom_right": (clip.size[0] - logo.size[0] - 10, clip.size[1] - logo.size[1] - 10),
                        "center": ((clip.size[0] - logo.size[0]) // 2, (clip.size[1] - logo.size[1]) // 2)
                    }
                    logo = logo.set_position(positions.get(self.logo_position.get(), (10, 10)))

                    if is_video:
                        logo = logo.set_duration(clip.duration)

                    final_clip = CompositeVideoClip([clip, logo])

                    if is_video:
                        final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", threads=4)
                    else:
                        final_clip.save_frame(output_file)

                    self.update_status(f"Added logo to {os.path.basename(input_file)}")

                except Exception as e:
                    self.update_status(f"Error adding logo: {str(e)}")
                    raise

    def add_text(self, input_file, output_file, is_video=True):
                """
                Add text to a video or image.
                """
                try:
                    if not os.path.exists(input_file):
                        raise FileNotFoundError(f"Input file not found: {input_file}")

                    text = self.text_content.get().strip()
                    if not text:
                        raise ValueError("Text content is empty!")

                    clip = VideoFileClip(input_file) if is_video else ImageClip(input_file)

                    # Ensure a safe font is used
                    font_name = "Arial"
                    try:
                        available_fonts = TextClip.list("font")
                        if font_name not in available_fonts:
                            font_name = available_fonts[0]  # Use the first available font
                    except Exception:
                        pass  # Fallback to default MoviePy font

                    # Create text clip
                    text_clip = TextClip(
                        text,
                        fontsize=self.text_size.get(),
                        color="white",
                        font=font_name,
                        bg_color="black",
                        size=(clip.size[0] // 2, None)
                    ).set_opacity(self.text_opacity.get())

                    # Position text
                    positions = {
                        "top_left": (10, 10),
                        "top_center": ((clip.size[0] - text_clip.size[0]) // 2, 10),
                        "top_right": (clip.size[0] - text_clip.size[0] - 10, 10),
                        "bottom_left": (10, clip.size[1] - text_clip.size[1] - 10),
                        "bottom_center": ((clip.size[0] - text_clip.size[0]) // 2, clip.size[1] - text_clip.size[1] - 10),
                        "bottom_right": (clip.size[0] - text_clip.size[0] - 10, clip.size[1] - text_clip.size[1] - 10),
                        "center": ((clip.size[0] - text_clip.size[0]) // 2, (clip.size[1] - text_clip.size[1]) // 2)
                    }
                    text_clip = text_clip.set_position(positions.get(self.text_position.get(), (10, 10)))

                    if is_video:
                        text_clip = text_clip.set_duration(clip.duration)

                    final_clip = CompositeVideoClip([clip, text_clip])

                    if is_video:
                        final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", threads=4)
                    else:
                        final_clip.save_frame(output_file)

                    self.update_status(f"Added text to {os.path.basename(input_file)}")

                except Exception as e:
                    self.update_status(f"Error adding text: {str(e)}")
                    raise

    def flip(self, input_file, output_file):
            clip = None
            try:
                # Check if it's an image or video
                if input_file.lower().endswith(('.mp4', '.mkv')):
                    clip = VideoFileClip(input_file)
                    clip = mirror_x(clip)
                    clip.write_videofile(output_file, verbose=False, logger=None, codec='libx264', audio_codec="aac")
                else:
                    # For images
                    img = Image.open(input_file)
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                    img.save(output_file)
            except Exception as e:
                self.update_status(f"Error flipping {input_file}: {str(e)}")
                raise
            finally:
                if clip is not None:
                    clip.close()

    def speed(self, input_file, speed, output_file):
        clip = None
        try:
            if not input_file.lower().endswith(('.mp4', '.mkv')):
                self.update_status(f"Cannot change speed of image {input_file}")
                # Just copy the image
                import shutil
                shutil.copy(input_file, output_file)
                return

            clip = VideoFileClip(input_file)
            clip = speedx(clip, speed)
            clip.write_videofile(output_file, verbose=False, logger=None, codec='libx264', audio_codec="aac")
        except Exception as e:
            self.update_status(f"Error changing speed of {input_file}: {str(e)}")
            raise
        finally:
            if clip is not None:
                clip.close()

    def speednflip(self, input_file, speed, output_file):
        clip = None
        try:
            if not input_file.lower().endswith(('.mp4', '.mkv')):
                self.update_status(f"Cannot change speed of image {input_file}")
                # Just flip the image
                img = Image.open(input_file)
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
                img.save(output_file)
                return

            clip = VideoFileClip(input_file)
            clip = mirror_x(clip)
            clip = speedx(clip, speed)
            clip.write_videofile(output_file, verbose=False, logger=None, codec='libx264', audio_codec="aac")
        except Exception as e:
            self.update_status(f"Error processing {input_file}: {str(e)}")
            raise
        finally:
            if clip is not None:
                clip.close()

    def addmusic(self, input_file, music, output_file):
        videoclip = None
        audioclip = None
        try:
            videoclip = VideoFileClip(input_file)
            audioclip = AudioFileClip(music)
            audioclip = audio_loop(audioclip, duration=videoclip.duration)
            videoclip = videoclip.set_audio(audioclip)
            videoclip.write_videofile(output_file, verbose=False, logger=None, codec='libx264', audio_codec="aac")
        except Exception as e:
            self.update_status(f"Error adding music to {input_file}: {str(e)}")
            raise
        finally:
            if videoclip is not None:
                videoclip.close()
            if audioclip is not None:
                audioclip.close()

    def musicnspeed(self, input_file, music, speed, output_file):
        videoclip = None
        audioclip = None
        try:
            videoclip = VideoFileClip(input_file)
            audioclip = AudioFileClip(music)
            audioclip = audio_loop(audioclip, duration=videoclip.duration)
            videoclip = speedx(videoclip, speed)
            videoclip = videoclip.set_audio(audioclip)
            videoclip.write_videofile(output_file, verbose=False, logger=None, codec='libx264', audio_codec="aac")
        except Exception as e:
            self.update_status(f"Error processing {input_file}: {str(e)}")
            raise
        finally:
            if videoclip is not None:
                videoclip.close()
            if audioclip is not None:
                audioclip.close()

    def musicnspeednflip(self, input_file, music, speed, output_file):
        videoclip = None
        audioclip = None
        try:
            videoclip = VideoFileClip(input_file)
            audioclip = AudioFileClip(music)
            audioclip = audio_loop(audioclip, duration=videoclip.duration)
            videoclip = mirror_x(videoclip)  # Flip the video
            videoclip = speedx(videoclip, speed)  # Change speed
            videoclip = videoclip.set_audio(audioclip)  # Add music
            videoclip.write_videofile(output_file, verbose=False, logger=None, codec='libx264', audio_codec="aac")
        except Exception as e:
            self.update_status(f"Error processing {input_file}: {str(e)}")
            raise
        finally:
            if videoclip is not None:
                videoclip.close()
            if audioclip is not None:
                audioclip.close()

    def upscale_image_basic(self, input_file, output_file):
        try:
            img = Image.open(input_file)
            new_size = (img.size[0] * 2, img.size[1] * 2)  # Double the resolution
            img = img.resize(new_size, Image.BICUBIC)  # Use bicubic interpolation for better quality
            img.save(output_file)
            self.update_status(f"Upscaled (Basic) {os.path.basename(input_file)}")
        except Exception as e:
            self.update_status(f"Error upscaling {input_file}: {str(e)}")
            raise

    def upscale_image_hd(self, input_file, output_file):
        try:
            img = cv2.imread(input_file)
            # Apply denoising to remove noise
            img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
            # Double the resolution with cubic interpolation
            new_size = (img.shape[1] * 2, img.shape[0] * 2)
            img = cv2.resize(img, new_size, interpolation=cv2.INTER_CUBIC)
            cv2.imwrite(output_file, img)
            self.update_status(f"Upscaled (HD) {os.path.basename(input_file)}")
        except Exception as e:
            self.update_status(f"Error upscaling {input_file}: {str(e)}")
            raise

    def cut_video(self, input_file, output_dir="./edited/cut_video"):
        try:
            os.makedirs(output_dir, exist_ok=True)

            clip = VideoFileClip(input_file)
            duration = clip.duration
            segment_duration = 60  # Split into 1-minute segments

            # Calculate total number of segments
            total_segments = int(duration // segment_duration) + (1 if duration % segment_duration > 0 else 0)
            self.update_status(f"Starting to cut {os.path.basename(input_file)} into {total_segments} segments")

            for i in range(0, int(duration), segment_duration):
                start_time = i
                end_time = min(i + segment_duration, duration)
                segment = clip.subclip(start_time, end_time)

                # Create output filename with segment number
                segment_number = i // segment_duration + 1
                base_name = os.path.splitext(os.path.basename(input_file))[0]
                segment_output_file = os.path.join(output_dir, f"{base_name}_part{segment_number:03d}.mp4")

                # Show progress
                self.update_status(f"Cutting segment {segment_number}/{total_segments}...")

                # Write the segment to file
                segment.write_videofile(segment_output_file, verbose=False, logger=None, codec='libx264',
                                        audio_codec="aac")
                segment.close()

            clip.close()
            self.update_status(f"Successfully cut video {os.path.basename(input_file)} into {total_segments} segments")
        except Exception as e:
            self.update_status(f"Error cutting {input_file}: {str(e)}")
            raise


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoEditorGUI(root)
    root.mainloop()

