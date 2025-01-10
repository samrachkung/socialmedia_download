import os
import re
import time
import json
import requests
from colorama import Fore, init
from rich.console import Console

# Initialize colorama and rich
init(autoreset=True)
console = Console()

class DownDouyin:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36 Edg/87.0.664.66'
        }
        self.sec_uid = None
        self.nickname = ''
        self.is_end = False
        self.like_counts = 0

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
        try:
            # Check if the input is a URL or a User ID
            if self.uid.startswith("http"):
                user_url = self._find_url(self.uid)
                response = requests.get(user_url, headers=self.headers)

                # Extract sec_uid from the redirected URL
                match = re.search(r'user/([\w\-]+)', response.url)
                if match:
                    self.sec_uid = match.group(1)
                else:
                    console.print("[red][Error][/red] Failed to extract sec_uid from URL.")
                    return False
            else:
                # Treat input as direct sec_uid
                self.sec_uid = self.uid

            console.print(f"[green][Success][/green] User sec_uid: {self.sec_uid}")
            return True
        except Exception as e:
            console.print(f"[red][Error][/red] Failed to process user link: {e}")
            return False

    @staticmethod
    def _find_url(string):
        url = re.findall(r'http[s]?://\S+', string)
        return url[0] if url else ''

    @staticmethod
    def _sanitize_filename(name):
        return re.sub(r'[\\/:*?"<>|\r\n]+', '_', name)

    def fetch_videos(self):
        api_url = f'https://www.iesdouyin.com/web/api/v2/aweme/{self.mode}/?sec_uid={self.sec_uid}&count={self.count}&max_cursor=0&aid=1128'
        
        console.print(f"[cyan]Fetching videos from API: {api_url}")

        try:
            response = requests.get(api_url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            self.nickname = self._sanitize_filename(data['aweme_list'][0]['author']['nickname'])
            user_dir = os.path.join(self.save_dir, self.nickname)
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)

            self._process_video_data(data)

        except requests.RequestException as e:
            console.print(f"[red][Error][/red] Failed to fetch videos: {e}")
        except KeyError:
            console.print("[red][Error][/red] Unexpected response format from the API.")

    def _process_video_data(self, data):
        aweme_list = data.get('aweme_list', [])
        if not aweme_list:
            console.print("[yellow]No videos found.[/yellow]")
            return

        for video in aweme_list:
            try:
                desc = self._sanitize_filename(video['desc'])
                video_url = video['video']['play_addr']['url_list'][0]
                creation_time = time.strftime("%Y-%m-%d %H.%M.%S", time.localtime(video['create_time']))

                filename = f"{creation_time} - {desc[:50]}.mp4"
                file_path = os.path.join(self.save_dir, self.nickname, filename)

                if os.path.exists(file_path):
                    console.print(f"[yellow]Skipped:[/yellow] {filename} (Already downloaded)")
                    continue

                self._download_video(video_url, file_path)

            except KeyError:
                console.print("[red][Error][/red] Missing data for a video. Skipping.")

    def _download_video(self, url, file_path):
        try:
            with requests.get(url, headers=self.headers, stream=True) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                chunk_size = 1024
                
                with open(file_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        file.write(chunk)

            console.print(f"[green][Downloaded][/green] {file_path}")
        except requests.RequestException as e:
            console.print(f"[red][Error][/red] Failed to download video: {e}")

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
