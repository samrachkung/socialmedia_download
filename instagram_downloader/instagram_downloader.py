import instaloader
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import webbrowser
import pyperclip
from queue import Queue

class InstagramDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram Post Downloader V2.0 By Kungsamrach")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Variables
        self.post_ids = tk.StringVar()
        self.download_path = tk.StringVar()
        self.download_path.set(os.path.join(os.path.expanduser('~'), 'Downloads'))
        self.download_status = tk.StringVar()
        self.download_status.set("Ready")
        self.download_queue = Queue()
        self.is_downloading = False
        self.downloaded_count = 0
        self.total_count = 0
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        # Set a modern theme if available
        try:
            style = ttk.Style()
            style.theme_use('clam')
            style.configure("TFrame", background="#23272F")
            style.configure("TLabel", background="#23272F", foreground="#E1E1E6", font=("Segoe UI", 11))
            style.configure("TEntry", fieldbackground="#2C313C", foreground="#E1E1E6")
            style.configure("TButton", background="#3B4252", foreground="#E1E1E6", font=("Segoe UI", 10, "bold"))
            style.configure("TProgressbar", troughcolor="#23272F", background="#4ECDC4", thickness=18)
        except Exception:
            pass

        self.root.configure(bg="#23272F")

        # Main Frame
        main_frame = ttk.Frame(self.root, padding="18 18 18 18", style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = ttk.Label(main_frame, text="Instagram Post Downloader", font=("Segoe UI", 18, "bold"), anchor="center")
        title.pack(fill=tk.X, pady=(0, 16))

        # Post IDs Label and Text Area
        ttk.Label(main_frame, text="Instagram Post IDs (one per line):", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        self.post_text = tk.Text(main_frame, height=8, wrap=tk.WORD, bg="#2C313C", fg="#E1E1E6", insertbackground="#E1E1E6", font=("Consolas", 11), relief=tk.FLAT, borderwidth=6)
        self.post_text.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        # Button Frame
        button_frame = ttk.Frame(main_frame, style="TFrame")
        button_frame.pack(fill=tk.X, pady=(0, 12))

        # Modern Buttons
        btn_style = {"font": ("Segoe UI", 10, "bold"), "relief": tk.FLAT, "bd": 0, "height": 1, "width": 15, "cursor": "hand2"}
        self.clear_btn = tk.Button(
            button_frame, text="1. Clear Links", command=self.clear_links,
            bg="#FF6B6B", fg="white", activebackground="#FF8E8E", activeforeground="white", **btn_style
        )
        self.clear_btn.pack(side=tk.LEFT, padx=6)

        self.paste_btn = tk.Button(
            button_frame, text="2. Paste Links", command=self.paste_links,
            bg="#4ECDC4", fg="#23272F", activebackground="#7FE5DD", activeforeground="#23272F", **btn_style
        )
        self.paste_btn.pack(side=tk.LEFT, padx=6)

        self.browse_btn = tk.Button(
            button_frame, text="3. Browse Save Path", command=self.browse_folder,
            bg="#45B7D1", fg="white", activebackground="#6BCAE2", activeforeground="white", **btn_style
        )
        self.browse_btn.pack(side=tk.LEFT, padx=6)

        # Download Path Frame
        path_frame = ttk.Frame(main_frame, style="TFrame")
        path_frame.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(path_frame, text="Download Path:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.path_entry = ttk.Entry(path_frame, textvariable=self.download_path, width=48, font=("Segoe UI", 10))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        # Download Button Frame
        download_frame = ttk.Frame(main_frame, style="TFrame")
        download_frame.pack(fill=tk.X, pady=(0, 12))

        self.download_btn = tk.Button(
            download_frame, text="4. Download", command=self.start_download,
            bg="#77DD77", fg="#23272F", activebackground="#9AEE9A", activeforeground="#23272F", **btn_style
        )
        self.download_btn.pack(side=tk.LEFT, padx=6)

        self.stop_btn = tk.Button(
            download_frame, text="Stop Download", command=self.stop_download,
            bg="#FF6961", fg="white", activebackground="#FF8982", activeforeground="white",
            state=tk.DISABLED, **btn_style
        )
        self.stop_btn.pack(side=tk.LEFT, padx=6)

        # Status Frame
        status_frame = ttk.Frame(main_frame, style="TFrame")
        status_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(status_frame, text="Status:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, textvariable=self.download_status, font=("Segoe UI", 10))
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        # Progress Frame
        progress_frame = ttk.Frame(main_frame, style="TFrame")
        progress_frame.pack(fill=tk.X, pady=(0, 12))

        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate', style="TProgressbar")
        self.progress_bar.pack(fill=tk.X, ipady=2)

        # Log Frame
        log_frame = ttk.Frame(main_frame, style="TFrame")
        log_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(log_frame, text="Download Log:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        self.log_text = tk.Text(
            log_frame, height=8, state=tk.DISABLED, bg="#181A20", fg="#E1E1E6",
            insertbackground="#E1E1E6", font=("Consolas", 10), relief=tk.FLAT, borderwidth=6
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # Configure tags for colored text
        self.log_text.tag_config("success", foreground="#77DD77")
        self.log_text.tag_config("error", foreground="#FF6B6B")
        self.log_text.tag_config("info", foreground="#45B7D1")
    def clear_links(self):
        self.post_text.delete(1.0, tk.END)
        
    def paste_links(self):
        try:
            clipboard_content = pyperclip.paste()
            self.post_text.insert(tk.END, clipboard_content)
        except Exception as e:
            self.log_message(f"Error pasting from clipboard: {str(e)}", "error")
            
    def browse_folder(self):
        folder_selected = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder_selected:
            self.download_path.set(folder_selected)
            
    def log_message(self, message, tag="info"):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def start_download(self):
        post_ids_text = self.post_text.get(1.0, tk.END).strip()
        if not post_ids_text:
            messagebox.showwarning("Warning", "Please enter at least one post ID")
            return
            
        post_ids = [pid.strip() for pid in post_ids_text.split('\n') if pid.strip()]
        self.total_count = len(post_ids)
        self.downloaded_count = 0
        
        if self.total_count == 0:
            messagebox.showwarning("Warning", "No valid post IDs found")
            return
            
        # Clear the queue and add all post IDs
        while not self.download_queue.empty():
            self.download_queue.get()
            
        for pid in post_ids:
            self.download_queue.put(pid)
            
        # Update UI
        self.download_status.set(f"Downloading 0/{self.total_count}")
        self.progress_bar["maximum"] = self.total_count
        self.progress_bar["value"] = 0
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.is_downloading = True
        
        # Start download thread
        download_thread = threading.Thread(target=self.download_posts, daemon=True)
        download_thread.start()
        
    def stop_download(self):
        self.is_downloading = False
        self.download_status.set("Download stopped")
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log_message("Download stopped by user", "info")
        
    def download_posts(self):
        L = instaloader.Instaloader(
            dirname_pattern=os.path.join(self.download_path.get(), "{shortcode}"),
            save_metadata=True,
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            compress_json=False
        )
        
        while not self.download_queue.empty() and self.is_downloading:
            post_id = self.download_queue.get()
            
            try:
                self.download_status.set(f"Downloading {self.downloaded_count + 1}/{self.total_count}")
                self.log_message(f"Downloading post: {post_id}", "info")
                
                # Download the post
                post = instaloader.Post.from_shortcode(L.context, post_id)
                L.download_post(post, target=post_id)
                
                self.downloaded_count += 1
                self.progress_bar["value"] = self.downloaded_count
                self.log_message(f"Successfully downloaded: {post_id}", "success")
                
            except instaloader.exceptions.InstaloaderException as e:
                self.log_message(f"Error downloading {post_id}: {str(e)}", "error")
            except Exception as e:
                self.log_message(f"Unexpected error with {post_id}: {str(e)}", "error")
                
            # Small delay to prevent rate limiting
            if self.is_downloading:
                threading.Event().wait(2)
                
        if self.is_downloading:
            self.download_status.set(f"Download complete: {self.downloaded_count}/{self.total_count}")
            self.log_message("All downloads completed!", "success")
            
            # Show completion message and open folder
            if self.downloaded_count > 0:
                messagebox.showinfo("Success", f"Downloaded {self.downloaded_count} of {self.total_count} posts")
                webbrowser.open(self.download_path.get())
        
        # Reset UI
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.is_downloading = False

if __name__ == "__main__":
    root = tk.Tk()
    app = InstagramDownloaderApp(root)
    root.mainloop()