import os
import time
import requests
import threading
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox

# Fetch user videos
def fetch_user_videos(username, callback):
    def worker():
        url = "https://www.tikwm.com/api/user/posts"
        querystring = {"unique_id": username, "count": "100", "cursor": "0"}
        headers = {"User-Agent": "Mozilla/5.0"}
        all_videos = []

        while True:
            try:
                response = requests.get(url, headers=headers, params=querystring)
                data = response.json()
                if "data" not in data or "videos" not in data["data"]:
                    break
                
                videos = data["data"]["videos"]
                all_videos.extend(videos)
                next_cursor = data["data"].get("cursor")
                if not next_cursor or next_cursor == "0":
                    break
                querystring["cursor"] = next_cursor
            except:
                break
        callback(all_videos)
    
    threading.Thread(target=worker, daemon=True).start()

# Download videos
def download_videos(videos, username, save_path, progress_var, progress_label):
    user_folder = os.path.join(save_path, username)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    
    total_videos = len(videos)
    
    def worker():
        for idx, video in enumerate(videos, start=1):
            try:
                video_filepath = os.path.join(user_folder, f"{video['video_id']}.mp4")
                caption_filepath = os.path.join(user_folder, f"{video['video_id']}.txt")
                
                if not os.path.exists(video_filepath):
                    video_bytes = requests.get(video["play"], stream=True)
                    with open(video_filepath, 'wb') as out_file:
                        for chunk in video_bytes.iter_content(chunk_size=1024):
                            if chunk:
                                out_file.write(chunk)
                
                with open(caption_filepath, 'w', encoding="utf-8") as caption_file:
                    caption_file.write(video.get("title", "Untitled"))
                
                progress_var.set((idx / total_videos) * 100)
                progress_label.config(text=f"Downloading: {idx}/{total_videos} videos")
            except:
                pass
        messagebox.showinfo("Download Complete", "All videos have been downloaded successfully!")
    
    threading.Thread(target=worker, daemon=True).start()

# Choose save folder
def choose_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_path.set(folder_selected)

# Start download process
def start_download():
    username = username_entry.get().strip()
    save_path = folder_path.get()
    
    if not username.startswith("@"): 
        messagebox.showerror("Error", "Username must start with '@'")
        return
    
    if not save_path:
        messagebox.showerror("Error", "Please select a folder to save the videos.")
        return
    
    username = username[1:]
    progress_label.config(text="Fetching videos Please Wait...")
    
    fetch_user_videos(username, lambda videos: on_videos_fetched(videos, username, save_path))

def on_videos_fetched(videos, username, save_path):
    if not videos:
        messagebox.showerror("Error", "No videos found or failed to fetch videos.")
        return
    
    progress_var.set(0)
    progress_label.config(text=f"Downloading {len(videos)} videos...")
    download_videos(videos, username, save_path, progress_var, progress_label)

# Create UI
root = tb.Window(themename="superhero")
root.title("TikTok Downloader by Kungsamrach V1.0")
root.geometry("780x450")
root.resizable(False, False)

frame = tb.Frame(root, padding=20)
frame.pack(fill="both", expand=True)

title_label = tb.Label(frame, text="TikTok Video Downloader ", font=("Arial", 18, "bold"))
title_label.pack(pady=10)

username_label = tb.Label(frame, text="Enter TikTok Username (@username):")
username_label.pack()

username_entry = tb.Entry(frame, width=40)
username_entry.pack(pady=5)

folder_label = tb.Label(frame, text="Select Folder to Save Videos:")
folder_label.pack()

folder_path = tb.StringVar()
folder_entry = tb.Entry(frame, textvariable=folder_path, width=40)
folder_entry.pack(pady=5)

browse_button = tb.Button(frame, text="Browse", command=choose_folder, bootstyle="primary")
browse_button.pack(pady=5)

start_button = tb.Button(frame, text="Download Videos", command=start_download, bootstyle="success")
start_button.pack(pady=10)

progress_var = tb.DoubleVar()
progress_bar = tb.Progressbar(frame, orient="horizontal", length=350, mode="determinate", variable=progress_var, bootstyle="success-striped")
progress_bar.pack(pady=5)

progress_label = tb.Label(frame, text="", font=("Arial", 10))
progress_label.pack()

# Run UI
root.mainloop()
