import os
import re
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
import pyperclip
from queue import Queue


class PinterestDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pinterest Downloader")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Variables
        self.downloading = False
        self.stop_flag = False
        self.download_queue = Queue()
        self.downloaded_count = 0
        self.failed_count = 0
        self.total_count = 0
        
        # UI Colors
        self.bg_color = "#f0f2f5"
        self.button_color = "#2196F3"  # Cool blue
        self.button_hover = "#1976D2"
        self.text_color = "#333333"
        self.success_color = "#00BFA5"  # Teal
        self.error_color = "#7C4DFF"    # Deep purple
        
        self.setup_ui()
        
    def setup_ui(self):
        # Configure modern style
        style = ttk.Style()
        style.configure("TFrame", background="#ffffff")
        style.configure("TLabel", background="#ffffff", foreground="#1a1a1a")
        style.configure("TButton", padding=10, font=("Helvetica", 10))
        style.configure("Accent.TButton", background=self.button_color, foreground="white")
        style.map("Accent.TButton",
                 background=[("active", self.button_hover), ("disabled", "#cccccc")])
                 
        # Set window icon and theme
        self.root.configure(bg="#ffffff")
        self.root.option_add("*TButton*padding", 5)
        
        # Main frame with shadow effect
        main_frame = ttk.Frame(self.root, padding="20", style="Card.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title with modern font
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, 
                               text="Pinterest Downloader", 
                               font=("Segoe UI", 24, "bold"),
                               foreground=self.button_color)
        title_label.pack(side=tk.LEFT)
        
        # URL Input with rounded corners
        url_frame = ttk.LabelFrame(main_frame, text="Pinterest URLs", padding="15")
        url_frame.pack(fill=tk.BOTH, expand=True)
        
        self.url_text = tk.Text(url_frame, 
                               height=10, 
                               wrap=tk.WORD, 
                               font=("Segoe UI", 11),
                               bg="#f8f9fa",
                               relief="flat",
                               padx=10,
                               pady=10)
        self.url_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(url_frame, command=self.url_text.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.url_text.config(yscrollcommand=scrollbar.set)
        
        # Modern button layout
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.clear_button = ttk.Button(button_frame, text="Clear", command=self.clear_links)
        self.clear_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.paste_button = ttk.Button(button_frame, text="Paste", command=self.paste_links)
        self.paste_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.browse_button = ttk.Button(button_frame, text="Browse", command=self.browse_folder)
        self.browse_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Download buttons with accent color
        download_frame = ttk.Frame(main_frame)
        download_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.download_button = ttk.Button(download_frame, 
                                        text="▼ Download", 
                                        command=self.start_download,
                                        style="Accent.TButton")
        self.download_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.stop_button = ttk.Button(download_frame, 
                                     text="■ Stop", 
                                     command=self.stop_download,
                                     state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Save path with modern entry
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Label(path_frame, text="Save Path:", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        
        self.save_path_var = tk.StringVar()
        self.save_path_var.set(os.path.expanduser("~/Downloads/Pinterest"))
        
        self.path_entry = ttk.Entry(path_frame, 
                                   textvariable=self.save_path_var,
                                   font=("Segoe UI", 10))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Status section with modern design
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="15")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))
        
        # Modern progress bar
        self.progress = ttk.Progressbar(status_frame, 
                                      orient=tk.HORIZONTAL, 
                                      mode='determinate',
                                      style="Accent.Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X, pady=(0, 15))
        
        # Counters with icons
        counter_frame = ttk.Frame(status_frame)
        counter_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(counter_frame, text="📊 Total:", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self.total_label = ttk.Label(counter_frame, text="0", font=("Segoe UI", 10, "bold"))
        self.total_label.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(counter_frame, text="✓ Done:", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self.downloaded_label = ttk.Label(counter_frame, text="0", 
                                        font=("Segoe UI", 10, "bold"),
                                        foreground=self.success_color)
        self.downloaded_label.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(counter_frame, text="❌ Failed:", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self.failed_label = ttk.Label(counter_frame, text="0", 
                                     font=("Segoe UI", 10, "bold"),
                                     foreground=self.error_color)
        self.failed_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Modern log view
        self.log_text = tk.Text(status_frame, 
                               height=8, 
                               wrap=tk.WORD, 
                               state=tk.DISABLED,
                               font=("Consolas", 9),
                               bg="#f8f9fa",
                               relief="flat",
                               padx=10,
                               pady=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Add status label
        self.status_label = ttk.Label(status_frame, 
                        text="Ready", 
                        font=("Segoe UI", 10),
                        foreground=self.text_color)
        self.status_label.pack(fill=tk.X, pady=(0, 5))

        # Add scrollbar to log
        log_scrollbar = ttk.Scrollbar(status_frame, command=self.log_text.yview)
        log_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
    def clear_links(self):
        self.url_text.delete("1.0", tk.END)
        
    def paste_links(self):
        clipboard = pyperclip.paste()
        if clipboard:
            self.url_text.insert(tk.END, clipboard)
            
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.save_path_var.get())
        if folder:
            self.save_path_var.set(folder)
            
    def start_download(self):
        urls = self.url_text.get("1.0", tk.END).strip()
        if not urls:
            messagebox.showwarning("Warning", "Please enter at least one Pinterest URL")
            return
            
        save_path = self.save_path_var.get()
        if not save_path:
            messagebox.showwarning("Warning", "Please select a save path")
            return
            
        if not os.path.exists(save_path):
            os.makedirs(save_path)
            
        # Reset counters
        self.downloaded_count = 0
        self.failed_count = 0
        self.total_count = len([url for url in urls.split('\n') if url.strip()])
        
        self.update_counters()
        self.progress["maximum"] = self.total_count
        self.progress["value"] = 0
        
        # Prepare URLs
        url_list = [url.strip() for url in urls.split('\n') if url.strip()]
        self.download_queue = Queue()
        for url in url_list:
            self.download_queue.put(url)
            
        # Start download thread
        self.downloading = True
        self.stop_flag = False
        self.download_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        self.log_message("Starting download...")
        
        download_thread = threading.Thread(target=self.download_thread_func, daemon=True)
        download_thread.start()
        
        # Start progress updater
        self.update_progress()
        
    def stop_download(self):
        self.stop_flag = True
        self.log_message("Stopping download after current item completes...")
        self.stop_button.config(state=tk.DISABLED)
        
    def download_thread_func(self):
        save_path = self.save_path_var.get()
        
        while not self.download_queue.empty() and not self.stop_flag:
            url = self.download_queue.get()
            
            try:
                # Use gallery-dl to download the Pinterest content
                command = [
                    'gallery-dl',
                    '--write-metadata',
                    '--directory', save_path,
                    url
                ]
                
                self.log_message(f"Downloading: {url}")
                
                result = subprocess.run(command, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.downloaded_count += 1
                    self.log_message(f"Successfully downloaded: {url}", is_success=True)
                else:
                    self.failed_count += 1
                    error_msg = result.stderr if result.stderr else "Unknown error"
                    self.log_message(f"Failed to download {url}: {error_msg}", is_error=True)
                    
                # Update progress in the queue
                self.root.event_generate("<<DownloadProgress>>", when="tail")
                
            except Exception as e:
                self.failed_count += 1
                self.log_message(f"Error downloading {url}: {str(e)}", is_error=True)
                self.root.event_generate("<<DownloadProgress>>", when="tail")
                
        # Download complete
        self.downloading = False
        self.root.event_generate("<<DownloadComplete>>", when="tail")
        
    def update_progress(self):
        if self.downloading:
            self.progress["value"] = self.downloaded_count + self.failed_count
            self.update_counters()
            self.root.after(100, self.update_progress)
            
    def update_counters(self):
        self.total_label.config(text=str(self.total_count))
        self.downloaded_label.config(text=str(self.downloaded_count))
        self.failed_label.config(text=str(self.failed_count))
        
    def log_message(self, message, is_success=False, is_error=False):
        self.log_text.config(state=tk.NORMAL)
        
        if is_success:
            self.log_text.insert(tk.END, message + "\n", "success")
        elif is_error:
            self.log_text.insert(tk.END, message + "\n", "error")
        else:
            self.log_text.insert(tk.END, message + "\n")
            
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
        
    def on_download_complete(self, event):
        self.download_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        if not self.stop_flag:
            messagebox.showinfo("Complete", f"Download completed!\n\nSuccess: {self.downloaded_count}\nFailed: {self.failed_count}")
            
            # Open the save folder
            save_path = self.save_path_var.get()
            if os.path.exists(save_path):
                webbrowser.open(save_path)
                
    def run(self):
        # Configure text tags for coloring
        self.log_text.tag_config("success", foreground=self.success_color)
        self.log_text.tag_config("error", foreground=self.error_color)
        
        # Bind events
        self.root.bind("<<DownloadComplete>>", self.on_download_complete)
        
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = PinterestDownloaderApp(root)
    app.run()