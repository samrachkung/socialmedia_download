import os
import re
import time
import requests
from bs4 import BeautifulSoup
from colorama import Fore, init
from rich.console import Console

# Initialize colorama and rich
init(autoreset=True)
console = Console()

class DownDouyin:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.sec_uid = None
        self.nickname = ''
        self.save_dir = './videos'

    def set_parameters(self, uid, save_dir, count, mode):
        if not uid:
            console.print("[red][Error][/red] User ID cannot be empty.")
            return False

        self.uid = uid
        self.save_dir = save_dir if save_dir else './videos'
        self.count = count if count else 10
        self.mode = mode if mode else 'post'

        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        return self._process_user_link()

    def _process_user_link(self):
        if self.uid.startswith("http"):
            self.sec_uid = self.uid.split("user/")[1].split("?")[0]
        else:
            self.sec_uid = self.uid

        console.print(f"[green][Success][/green] User sec_uid: {self.sec_uid}")
        return True

    def fetch_videos(self):
        user_url = f'https://www.douyin.com/user/{self.sec_uid}'
        console.print(f"[cyan]Fetching videos from URL: {user_url}[/cyan]")

        try:
            response = requests.get(user_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract JSON data embedded in the webpage
            script_tag = soup.find('script', id='RENDER_DATA')
            if not script_tag:
                console.print("[red][Error][/red] Failed to find video data on the page.")
                return

            # Decode and load JSON from script tag
            raw_data = script_tag.string
            data = requests.utils.unquote(raw_data)
            json_data = eval(data)  # Convert raw data to dictionary
            videos = self._extract_videos(json_data)

            if not videos:
                console.print("[yellow]No videos found.[/yellow]")
                return

            user_dir = os.path.join(self.save_dir, self.sec_uid)
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)

            self._download_videos(videos, user_dir)

        except requests.RequestException as e:
            console.print(f"[red][Error][/red] Failed to fetch user page: {e}")
        except Exception as e:
            console.print(f"[red][Error][/red] Unexpected error: {e}")

    def _extract_videos(self, json_data):
        """Extract video URLs and descriptions from the JSON data."""
        try:
            videos = []
            aweme_list = json_data.get('aweme', {}).get('post', {}).get('list', [])
            for video in aweme_list[:self.count]:
                video_url = video['video']['play_addr']['url_list'][0]
                desc = video.get('desc', 'Untitled')
                videos.append({'url': video_url, 'desc': desc})
            return videos
        except KeyError:
            console.print("[red][Error][/red] Unexpected data format.")
            return []

    def _download_videos(self, videos, user_dir):
        for video in videos:
            try:
                desc = self._sanitize_filename(video['desc'])
                video_url = video['url']
                creation_time = time.strftime("%Y-%m-%d %H.%M.%S", time.localtime())
                filename = f"{creation_time} - {desc[:50]}.mp4"
                file_path = os.path.join(user_dir, filename)

                if os.path.exists(file_path):
                    console.print(f"[yellow]Skipped:[/yellow] {filename} (Already downloaded)")
                    continue

                self._download_video(video_url, file_path)
            except Exception as e:
                console.print(f"[red][Error][/red] Failed to process video: {e}")

    def _download_video(self, url, file_path):
        try:
            with requests.get(url, headers=self.headers, stream=True) as response:
                response.raise_for_status()
                with open(file_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=1024):
                        file.write(chunk)

            console.print(f"[green][Downloaded][/green] {file_path}")
        except requests.RequestException as e:
            console.print(f"[red][Error][/red] Failed to download video: {e}")

    @staticmethod
    def _sanitize_filename(name):
        return re.sub(r'[\\/:*?"<>|\r\n]+', '_', name)

# Example Usage
if __name__ == "__main__":
    douyin = DownDouyin()
    uid = input("Enter Douyin user URL or User ID: ").strip()
    save_dir = input("Enter directory to save videos (default: ./videos): ").strip() or './videos'
    count = input("Enter number of videos to download (default: 10): ").strip()
    mode = input("Enter mode (post, like, or all, default: post): ").strip() or 'post'

    try:
        count = int(count) if count else 10
    except ValueError:
        count = 10

    if douyin.set_parameters(uid=uid, save_dir=save_dir, count=count, mode=mode):
        douyin.fetch_videos()
