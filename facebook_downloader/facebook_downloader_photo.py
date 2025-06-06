import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import gallery_dl
from urllib.parse import urlparse
import webbrowser
import queue
import subprocess  # Added for gallery-dl subprocess

class FacebookDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Downloader")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f2f5')
        self.style.configure('TLabel', background='#f0f2f5', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10), padding=5)
        self.style.configure('TEntry', font=('Arial', 10), padding=5)
        self.style.configure('TText', font=('Arial', 10))
        self.style.configure('Header.TLabel', font=('Arial', 14, 'bold'), foreground='#1877f2')
        
        # Variables
        self.download_folder = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.download_queue = queue.Queue()
        self.is_downloading = False
        self.current_downloads = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.total_downloads = 0  # Added to track total downloads
        
        # Create UI
        self.create_widgets()
        
        # Start download thread
        self.download_thread = threading.Thread(target=self.process_download_queue, daemon=True)
        self.download_thread.start()
    
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Facebook Downloader", style='Header.TLabel').pack(side=tk.LEFT)
        
        # URL input section
        url_frame = ttk.LabelFrame(main_frame, text="Facebook URLs", padding="10")
        url_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.url_text = tk.Text(url_frame, height=10, wrap=tk.WORD)
        self.url_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        button_frame = ttk.Frame(url_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Paste Links", command=self.paste_links).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Links", command=self.clear_links).pack(side=tk.LEFT, padx=5)
        
        # Options section
        options_frame = ttk.LabelFrame(main_frame, text="Download Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Download folder selection
        folder_frame = ttk.Frame(options_frame)
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(folder_frame, text="Save to:").pack(side=tk.LEFT)
        
        folder_entry = ttk.Entry(folder_frame, textvariable=self.download_folder)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(folder_frame, text="Browse...", command=self.browse_folder).pack(side=tk.LEFT)
        
        # Download buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.download_button = ttk.Button(button_frame, text="Start Download", command=self.start_download)
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop Download", command=self.stop_download, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Download Status", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(status_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Status labels
        self.status_label = ttk.Label(status_frame, text="Ready to download")
        self.status_label.pack(anchor=tk.W)
        
        stats_frame = ttk.Frame(status_frame)
        stats_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(stats_frame, text="Current:").pack(side=tk.LEFT)
        self.current_label = ttk.Label(stats_frame, text="0")
        self.current_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(stats_frame, text="Success:").pack(side=tk.LEFT, padx=(10, 0))
        self.success_label = ttk.Label(stats_frame, text="0")
        self.success_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(stats_frame, text="Failed:").pack(side=tk.LEFT, padx=(10, 0))
        self.failed_label = ttk.Label(stats_frame, text="0")
        self.failed_label.pack(side=tk.LEFT, padx=5)
        
        # Log area
        self.log_text = tk.Text(status_frame, height=8, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
    
    def paste_links(self):
        try:
            clipboard_content = self.root.clipboard_get()
            if clipboard_content:
                self.url_text.insert(tk.END, clipboard_content + "\n")
        except tk.TclError:
            self.log_message("Clipboard is empty or doesn't contain text.")
    
    def clear_links(self):
        self.url_text.delete(1.0, tk.END)
    
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_folder.get())
        if folder:
            self.download_folder.set(folder)
    
    def start_download(self):
        urls = self.url_text.get(1.0, tk.END).strip().split('\n')
        urls = [url.strip() for url in urls if url.strip()]
        
        if not urls:
            messagebox.showwarning("Warning", "Please enter at least one URL.")
            return
        
        # Reset counters
        self.current_downloads = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.total_downloads = len(urls)  # Set total downloads
        self.update_status_labels()
        
        # Clear log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Clear queue and add new URLs
        with self.download_queue.mutex:
            self.download_queue.queue.clear()
        for url in urls:
            self.download_queue.put(url)
        
        # Update UI
        self.progress_bar['maximum'] = len(urls)
        self.progress_bar['value'] = 0
        self.is_downloading = True
        self.download_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text=f"Downloading {len(urls)} items...")
    
    def stop_download(self):
        self.is_downloading = False
        self.download_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Download stopped by user")
        # Clear the queue
        with self.download_queue.mutex:
            self.download_queue.queue.clear()
    
    def process_download_queue(self):
        while True:
            try:
                url = self.download_queue.get(timeout=1)
                
                if not self.is_downloading:
                    continue
                
                self.current_downloads += 1
                self.update_status_labels()
                
                self.log_message(f"Processing URL {self.current_downloads}: {url}")
                
                try:
                    # Determine if URL is for video or image
                    if self.is_video_url(url):
                        success = self.download_video(url)
                    else:
                        success = self.download_image(url)
                    
                    if success:
                        self.successful_downloads += 1
                    else:
                        self.failed_downloads += 1
                    
                    self.update_status_labels()
                    self.progress_bar.step(1)
                    self.root.update()
                    
                except Exception as e:
                    self.failed_downloads += 1
                    self.log_message(f"Error downloading {url}: {str(e)}")
                    self.update_status_labels()
                
                # Check if all downloads are complete
                if self.current_downloads >= self.total_downloads:
                    self.is_downloading = False
                    self.download_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.DISABLED)
                    self.status_label.config(text="Download complete")
                    
                    # Show completion message
                    messagebox.showinfo("Complete", 
                                      f"Download finished!\n\nSuccess: {self.successful_downloads}\nFailed: {self.failed_downloads}")
                    
                    # Open download folder if at least one download succeeded
                    if self.successful_downloads > 0:
                        try:
                            webbrowser.open(f"file://{os.path.abspath(self.download_folder.get())}")
                        except Exception as e:
                            self.log_message(f"Could not open download folder: {str(e)}")
                
            except queue.Empty:
                continue
    
    def is_video_url(self, url):
        # Simple check to determine if URL is likely a video
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        
        # Check for common video paths
        if 'videos' in path_parts or 'reel' in path_parts or 'watch' in path_parts:
            return True
        
        # If it's not clearly a video, assume it's an image
        return False
    
    def download_video(self, url):
        try:
            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(self.download_folder.get(), '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writeinfojson': True,  # Save metadata including caption
                'writethumbnail': True,
                'merge_output_format': 'mp4',
                'ignoreerrors': True,  # Continue on download errors
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            self.log_message(f"Successfully downloaded video: {url}")
            return True
        except Exception as e:
            self.log_message(f"Error downloading video {url}: {str(e)}")
            return False
    
    def download_image(self, url):
        try:
            # Build the output directory from your GUI field
            output_dir = os.path.abspath(self.download_folder.get())

            # Construct the command
            cmd = [
                "gallery-dl",
                "--write-metadata",
                "-d", output_dir,
                url
            ]

            # Run the command
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)

            # Check result
            if result.returncode == 0:
                self.log_message(f"Successfully downloaded: {url}")
                return True
            else:
                error_msg = result.stderr if result.stderr else "Unknown error occurred"
                self.log_message(f"gallery-dl error for {url}:\n{error_msg}")
                return False

        except subprocess.TimeoutExpired:
            self.log_message(f"Timeout while downloading {url}")
            return False
        except Exception as e:
            self.log_message(f"Exception while downloading {url}:\n{str(e)}")
            return False

    def update_status_labels(self):
        self.current_label.config(text=str(self.current_downloads))
        self.success_label.config(text=str(self.successful_downloads))
        self.failed_label.config(text=str(self.failed_downloads))
    
    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()

if __name__ == "__main__":
    root = tk.Tk()
    app = FacebookDownloaderApp(root)
    root.mainloop()