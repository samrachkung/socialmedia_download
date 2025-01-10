import os
import time
import requests
from rich.console import Console
from rich.progress import track
from rich.align import Align
from colorama import Fore

console = Console()

def fetch_user_videos(username):
    """Fetch all videos from a TikTok user's profile using TikWM API."""
    url = "https://www.tikwm.com/api/user/posts"
    querystring = {"unique_id": username, "count": "100", "cursor": "0"}
    s = requests.Session()
    headers = {"User-Agent": s.headers['User-Agent']}
    all_videos = []

    while True:
        try:
            response = requests.get(url, headers=headers, params=querystring)
            data = response.json()
            if "data" not in data or "videos" not in data["data"]:
                console.log("[cyan][Status]No More video in this user.[/cyan]")
                break

            videos = data["data"]["videos"]
            all_videos.extend(videos)
            console.log(f"[cyan]Fetched {len(videos)} videos (Total: {len(all_videos)}).[/cyan]")

            # Check for next page
            next_cursor = data["data"].get("cursor")
            if not next_cursor or next_cursor == "0":
                break
            querystring["cursor"] = next_cursor
        except Exception as e:
            console.log(f"[red]Error: {e}[/red]")
            break

    return all_videos


def download_videos(videos, username):
    """Download videos and save captions to local directory."""
    if not os.path.exists(f"./tiktok/{username}"):
        os.makedirs(f"./tiktok/{username}")

    console.log("[cyan][Status][/cyan] Already downloaded videos will be skipped.\n")

    for video in track(videos, description="Downloading videos..."):
        try:
            download_url = video["play"]
            video_id = video["video_id"]
            title = video.get("title", "Untitled").replace("/", "-").replace("\\", "-")
            caption = video["title"] 
            video_filepath = f"./tiktok/{username}/{video_id}.mp4"
            caption_filepath = f"./tiktok/{username}/{video_id}.txt"

            # Download video if not already downloaded
            if not os.path.exists(video_filepath):
                video_bytes = requests.get(download_url, stream=True)
                total_length = int(video_bytes.headers.get("Content-Length", 0))
                console.log(f"[green][Status][/green] File size: {total_length / 1024 / 1024:.2f} MB") 

                with open(video_filepath, 'wb') as out_file:
                    out_file.write(video_bytes.content)

                console.log(f"[cyan][File][/cyan] {video_filepath} downloaded.")
            else:
                console.log(f"[yellow][File][/yellow] {video_filepath} already exists. Skipping...\n")

            # Save caption
            with open(caption_filepath, 'w', encoding="utf-8") as caption_file:
                caption_file.write(caption)
                console.log(f"[cyan][Caption][/cyan] Saved caption to {caption_filepath}.")

            time.sleep(0.7)
        except Exception as e:
            console.log(f"[red]Error downloading video or saving caption: {e}[/red]")


def main():
    banner = f"""{Fore.MAGENTA} 
         ████████╗ ██╗ ██╗  ██╗████████╗ █████╗  ██╗  ██╗   ██████╗    █████╗   ██╗       ██╗  ███╗  ██╗   ██╗        █████╗    █████╗   ██████╗                                                         
         ╚══██╔══╝ ██║ ██║ ██╔╝╚══██╔══╝██╔══██╗ ██║ ██╔╝   ██╔══██╗  ██╔══██╗  ██║  ██╗  ██║  ████╗ ██║   ██║       ██╔══██╗  ██╔══██╗  ██╔══██╗                                                             
            ██║    ██║ █████═╝    ██║   ██║  ██║ █████═╝    ██║  ██║  ██║  ██║  ╚██╗████╗██╔╝  ██╔██╗██║   ██║       ██║  ██║  ███████║  ██║  ██║                                                         
            ██║    ██║ ██╔═██╗    ██║   ██║  ██║ ██╔═██╗    ██║  ██║  ██║  ██║   ████╔═████║   ██║╚████║   ██║       ██║  ██║  ██╔══██║  ██║  ██║                                                         
            ██║    ██║ ██║ ╚██╗   ██║   ╚█████╔╝ ██║ ╚██╗   ██████╔╝  ╚█████╔╝   ╚██╔╝ ╚██╔╝   ██║ ╚███║   ███████╗  ╚█████╔╝  ██║  ██║  ██████╔╝                                                                                                         
            ╚═╝    ╚═╝ ╚═╝  ╚═╝   ╚═╝    ╚════╝  ╚═╝  ╚═╝   ╚═════╝    ╚════╝     ╚═╝   ╚═╝    ╚═╝  ╚══╝   ╚══════╝   ╚════╝   ╚═╝  ╚═╝  ╚═════╝                                                  
                                Tool By Kungsamrach ==> Facebook : Samrach kung 
    """

    # Display the banner
    console.print(Align.center(banner))

    # Ask for the TikTok username
    username = input("Enter TikTok username (e.g., @username): ").strip()
    if not username.startswith("@"):
        console.log("[red]Error: Username must start with '@'.[/red]")
        return

    username = username[1:]  # Remove '@' for the API request
    videos = fetch_user_videos(username)

    if not videos:
        console.log("[red]No videos found or failed to fetch videos.[/red]")
        return

    console.log(f"[cyan][Status][/cyan] Found {len(videos)} videos for user {username}. Starting download...")
    download_videos(videos, username)


if __name__ == "__main__":
    main()
