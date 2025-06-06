import os
import time
import requests
from rich.console import Console
from rich.progress import track
from rich.align import Align
from colorama import Fore

console = Console()

def fetch_user_photos(username):
    """Fetch all photos from a TikTok user's profile using TikWM API."""
    url = "https://www.tikwm.com/api/user/posts"
    querystring = {"unique_id": username, "count": "100", "cursor": "0"}
    s = requests.Session()
    headers = {"User-Agent": s.headers['User-Agent']}
    all_photos = []

    while True:
        try:
            response = requests.get(url, headers=headers, params=querystring)
            data = response.json()

            if "data" not in data or "videos" not in data["data"]:
                console.log("[cyan][+][Status] No more photos in this user.[/cyan]")
                break

            media_items = data["data"]["videos"]
            
            # Filter only items with photos
            photo_items = [item for item in media_items if "images" in item and item["images"]]
            all_photos.extend(photo_items)
            
            console.log(f"[cyan][+] Fetched {len(photo_items)} photos (Total: {len(all_photos)}).[/cyan]")

            next_cursor = data["data"].get("cursor")
            if not next_cursor or next_cursor == "0":
                break
            querystring["cursor"] = next_cursor

        except Exception as e:
            console.log(f"[red]Error: {e}[/red]")
            break

    return all_photos


def download_photos(photo_items, username):
    """Download photos and save captions and like counts to local directory."""
    save_path = f"./tiktok/{username}"
    os.makedirs(save_path, exist_ok=True)

    console.log("[cyan][+] [Note][/cyan] Already downloaded photos will be skipped.\n")

    for item in track(photo_items, description="Downloading photos..."):
        try:
            media_id = item.get("video_id", "unknown")
            title = item.get("title", "Untitled").replace("/", "-").replace("\\", "-")
            caption = item.get("title", "")
            like_count = item.get("digg_count", "N/A")

            # Get first photo URL
            first_image = item["images"][0]
            if isinstance(first_image, dict):
                download_url = first_image.get("url")
            elif isinstance(first_image, str):
                download_url = first_image
            
            if not download_url:
                console.log(f"[yellow][+] Skipping photo ID {media_id}: no valid URL found.[/yellow]")
                continue

            photo_filepath = os.path.join(save_path, f"{media_id}_HaveLike_{like_count}.jpg")
            caption_filepath = os.path.join(save_path, f"{media_id}_HaveLike_{like_count}.txt")

            # Download if not already exists
            if not os.path.exists(photo_filepath):
                photo_response = requests.get(download_url, stream=True)
                photo_response.raise_for_status()

                total_length = int(photo_response.headers.get("Content-Length", 0))
                console.log(f"[green][Status][/green] Photo size: {total_length / 1024 / 1024:.2f} MB")

                with open(photo_filepath, 'wb') as f:
                    for chunk in photo_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                console.log(f"[cyan][+][File][/cyan] {photo_filepath} downloaded.")
            else:
                console.log(f"[yellow][+][File][/yellow] {photo_filepath} already exists. Skipping...\n")

            # Save caption
            with open(caption_filepath, 'w', encoding="utf-8") as caption_file:
                caption_file.write(caption)
                console.log(f"[cyan][+][Caption][/cyan] Saved caption to {caption_filepath}.")

            time.sleep(2)

        except Exception as e:
            console.log(f"[red][+] Error downloading photo or saving caption: {e}[/red]")


def main():
    banner = f"""{Fore.MAGENTA}                                                 
                              TIkDownL V1.5.0  Tool By Kungsamrach ==> Facebook : Samrach kung 
    """

    console.print(Align.center(banner))

    username = input("[+] Enter TikTok username (e.g., @username): ").strip()
    if not username.startswith("@"):
        console.log("[red][+] Error: Username must start with '@'.[/red]")
        return

    username = username[1:]
    photo_items = fetch_user_photos(username)

    if not photo_items:
        console.log("[red][+] No photos found or failed to fetch photos.[/red]")
        return

    console.log(f"[cyan][+] [Status][/cyan] Found {len(photo_items)} photos for user {username}. Starting download...")
    download_photos(photo_items, username)


if __name__ == "__main__":
    main()