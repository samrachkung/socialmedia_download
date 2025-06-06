import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
import requests
import json
import re
from datetime import datetime
import webbrowser

class FacebookPhotoDownloader:
    def __init__(self, master):
        self.master = master
        self.master.title("Facebook Photo Downloader")
        self.master.geometry("600x500")
        self.master.configure(bg="#f0f2f5")  # Facebook-like background color
        
        # Variables
        self.download_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.total_links = tk.IntVar(value=0)
        self.downloaded = tk.IntVar(value=0)
        self.failed = tk.IntVar(value=0)
        self.is_downloading = False
        self.download_thread = None
        
        # Create UI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self.master, bg="#4267B2", padx=10, pady=10)  # Facebook blue
        header_frame.pack(fill=tk.X)
        
        header_label = tk.Label(header_frame, text="Facebook Photo Downloader", 
                               font=("Helvetica", 16, "bold"), bg="#4267B2", fg="white")
        header_label.pack()
        
        # Main content
        content_frame = tk.Frame(self.master, bg="#f0f2f5", padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # URLs input
        url_frame = tk.LabelFrame(content_frame, text="Facebook Photo URLs", bg="#f0f2f5", padx=10, pady=10)
        url_frame.pack(fill=tk.BOTH, expand=True)
        
        # URLs text area with scrollbar
        url_scroll = tk.Scrollbar(url_frame)
        url_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.url_text = tk.Text(url_frame, height=10, width=50, yscrollcommand=url_scroll.set)
        self.url_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        url_scroll.config(command=self.url_text.yview)
        
        # URL buttons frame
        url_buttons_frame = tk.Frame(content_frame, bg="#f0f2f5")
        url_buttons_frame.pack(fill=tk.X, pady=10)
        
        # Button 1: Clear links
        self.clear_btn = tk.Button(url_buttons_frame, text="Clear Links", bg="#e4e6eb", 
                                 activebackground="#dfe3ee", width=15, command=self.clear_links)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Button 2: Paste Links
        self.paste_btn = tk.Button(url_buttons_frame, text="Paste Links", bg="#e4e6eb", 
                                 activebackground="#dfe3ee", width=15, command=self.paste_links)
        self.paste_btn.pack(side=tk.LEFT, padx=5)
        
        # Download path selection
        path_frame = tk.Frame(content_frame, bg="#f0f2f5", pady=10)
        path_frame.pack(fill=tk.X)
        
        path_label = tk.Label(path_frame, text="Save to:", bg="#f0f2f5")
        path_label.pack(side=tk.LEFT, padx=5)
        
        path_entry = tk.Entry(path_frame, textvariable=self.download_path, width=40)
        path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Button 3: Browse folder save path
        browse_btn = tk.Button(path_frame, text="Browse", bg="#e4e6eb", 
                              activebackground="#dfe3ee", command=self.browse_folder)
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = tk.LabelFrame(content_frame, text="Download Status", bg="#f0f2f5", padx=10, pady=10)
        status_frame.pack(fill=tk.X, pady=10)
        
        # Status counters
        counters_frame = tk.Frame(status_frame, bg="#f0f2f5")
        counters_frame.pack(fill=tk.X)
        
        # Total links
        tk.Label(counters_frame, text="Total Links:", bg="#f0f2f5").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        tk.Label(counters_frame, textvariable=self.total_links, bg="#f0f2f5", width=8).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Downloaded
        tk.Label(counters_frame, text="Downloaded:", bg="#f0f2f5").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        tk.Label(counters_frame, textvariable=self.downloaded, bg="#f0f2f5", width=8).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Failed
        tk.Label(counters_frame, text="Failed:", bg="#f0f2f5").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        tk.Label(counters_frame, textvariable=self.failed, bg="#f0f2f5", width=8).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Progress bar
        self.progress = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, pady=10)
        
        # Button Frame - Added bottom button row properly
        button_frame = tk.Frame(content_frame, bg="#f0f2f5")
        button_frame.pack(fill=tk.X, pady=10)
        
        # Button 1: Clear Links (duplicate at bottom)
        clear_bottom_btn = tk.Button(button_frame, text="Clear Links", bg="#ff7700", fg="white",
                                 activebackground="#e66700", activeforeground="white", 
                                 width=15, command=self.clear_links)
        clear_bottom_btn.pack(side=tk.LEFT, padx=5, expand=True)
        
        # Button 2: Paste Links (duplicate at bottom)
        paste_bottom_btn = tk.Button(button_frame, text="Paste Links", bg="#ffaa00", fg="white",
                                 activebackground="#e69900", activeforeground="white", 
                                 width=15, command=self.paste_links)
        paste_bottom_btn.pack(side=tk.LEFT, padx=5, expand=True)
        
        # Button 3: Browse folder (duplicate at bottom)
        browse_bottom_btn = tk.Button(button_frame, text="Browse Folder", bg="#00aaff", fg="white",
                              activebackground="#0099e6", activeforeground="white", 
                              width=15, command=self.browse_folder)
        browse_bottom_btn.pack(side=tk.LEFT, padx=5, expand=True)
        
        # Button 4: Download/Stop Download
        self.download_btn = tk.Button(button_frame, text="Download", bg="#1877f2", fg="white", 
                                    activebackground="#166fe5", activeforeground="white", 
                                    width=15, command=self.toggle_download)
        self.download_btn.pack(side=tk.LEFT, padx=5, expand=True)
        
        # Status message
        self.status_message = tk.Label(content_frame, text="Ready to download", bg="#f0f2f5", fg="#4267B2")
        self.status_message.pack(pady=5)
        
    def clear_links(self):
        self.url_text.delete('1.0', tk.END)
        self.update_total_links()
        
    def paste_links(self):
        clipboard = self.master.clipboard_get()
        if clipboard:
            if self.url_text.get('1.0', tk.END).strip():
                # If there's already text, add a newline
                self.url_text.insert(tk.END, "\n" + clipboard)
            else:
                self.url_text.insert(tk.END, clipboard)
            self.update_total_links()
        
    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.download_path.set(folder_path)
            
    def update_total_links(self):
        urls = self.get_urls()
        self.total_links.set(len(urls))
        
    def get_urls(self):
        urls_text = self.url_text.get('1.0', tk.END).strip()
        if not urls_text:
            return []
        
        # Split by newlines and filter out empty strings
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        return urls
        
    def toggle_download(self):
        if self.is_downloading:
            self.stop_download()
        else:
            self.start_download()
            
    def start_download(self):
        urls = self.get_urls()
        if not urls:
            messagebox.showwarning("No URLs", "Please enter Facebook photo URLs to download.")
            return
            
        save_path = self.download_path.get()
        if not os.path.exists(save_path):
            try:
                os.makedirs(save_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create download directory: {str(e)}")
                return
                
        self.is_downloading = True
        self.download_btn.config(text="Stop Download", bg="#e41e3f")
        self.status_message.config(text="Downloading...")
        
        # Reset counters
        self.downloaded.set(0)
        self.failed.set(0)
        self.progress['value'] = 0
        
        # Start download thread
        self.download_thread = Thread(target=self.download_photos, args=(urls, save_path))
        self.download_thread.daemon = True
        self.download_thread.start()
        
    def stop_download(self):
        if self.is_downloading:
            self.is_downloading = False
            self.download_btn.config(text="Download", bg="#1877f2")
            self.status_message.config(text="Download stopped")
            
    def download_photos(self, urls, save_path):
        total = len(urls)
        
        for i, url in enumerate(urls):
            if not self.is_downloading:
                break
                
            try:
                # Extract photo ID from URL
                photo_id = self.extract_photo_id(url)
                
                if not photo_id:
                    self.update_failed()
                    continue
                
                # Download photo
                image_url = f"https://graph.facebook.com/{photo_id}/picture?type=large"
                image_data = requests.get(image_url).content
                
                # Get caption
                caption = self.get_photo_caption(photo_id)
                
                # Save image
                image_path = os.path.join(save_path, f"{photo_id}.jpg")
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                # Save caption if available
                if caption:
                    caption_path = os.path.join(save_path, f"{photo_id}.txt")
                    with open(caption_path, 'w', encoding='utf-8') as f:
                        f.write(caption)
                
                self.update_downloaded()
            except Exception as e:
                self.update_failed()
                print(f"Error downloading {url}: {str(e)}")
            
            # Update progress
            progress_val = (i + 1) / total * 100
            self.master.after(0, lambda val=progress_val: self.progress.config(value=val))
            
        # Download complete
        self.master.after(0, self.download_complete)
            
    def download_complete(self):
        self.is_downloading = False
        self.download_btn.config(text="Download", bg="#1877f2")
        
        downloaded = self.downloaded.get()
        failed = self.failed.get()
        
        if downloaded > 0:
            self.status_message.config(text=f"Download complete! {downloaded} photos downloaded, {failed} failed")
            messagebox.showinfo("Download Complete", 
                               f"Successfully downloaded {downloaded} photos.\n{failed} photos failed.")
            # Open folder
            webbrowser.open(self.download_path.get())
        else:
            self.status_message.config(text="Download failed. No photos were downloaded.")
            
    def update_downloaded(self):
        self.master.after(0, lambda: self.downloaded.set(self.downloaded.get() + 1))
        
    def update_failed(self):
        self.master.after(0, lambda: self.failed.set(self.failed.get() + 1))
        
    def extract_photo_id(self, url):
        # Extract photo ID from URL
        # This is a simplified version and may need to be adjusted based on actual Facebook URL formats
        patterns = [
            r'facebook\.com/.*?/photos/(?:a\.\d+/)?(\d+)',
            r'facebook\.com/photo\.php\?fbid=(\d+)',
            r'facebook\.com/.*?/photos/\d+/(\d+)',
            r'facebook\.com/.*?/photos/pcb\.\d+/(\d+)',
            r'facebook\.com/photo/\?fbid=(\d+)',
            r'fbid=(\d+)',
            r'/(\d+)/?$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
        
    def get_photo_caption(self, photo_id):
        # In a real application, this would make an API call to get the caption
        # For this demo, we'll simulate it
        try:
            # This is a placeholder - in a real app, you would use Facebook Graph API
            # But that requires authentication and permissions
            return f"Caption for photo {photo_id}\nDownloaded on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        except Exception:
            return ""

if __name__ == "__main__":
    root = tk.Tk()
    app = FacebookPhotoDownloader(root)
    root.mainloop()