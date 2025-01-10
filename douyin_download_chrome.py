import os
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from colorama import Fore, init
from rich.console import Console
import requests
# Initialize colorama and rich
init(autoreset=True)
console = Console()

class DownDouyin:
    def __init__(self):
        self.sec_uid = None
        self.save_dir = './videos'
        self.driver = self._init_driver()

    def _init_driver(self):
        # Set up Selenium WebDriver
        options = Options()
        options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--log-level=3')
        driver_path = "path_to_chromedriver"  # Update this with the path to chromedriver

        return webdriver.Chrome(service=Service(driver_path), options=options)

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
            self.driver.get(user_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "script"))
            )

            # Extract JSON data from the page
            script_tag = self.driver.find_element(By.XPATH, "//script[@id='RENDER_DATA']")
            raw_data = script_tag.get_attribute("innerHTML")
            json_data = requests.utils.unquote(raw_data)
            video_data = eval(json_data)  # Convert raw JSON data to dictionary

            videos = self._extract_videos(video_data)

            if not videos:
                console.print("[yellow]No videos found.[/yellow]")
                return

            user_dir = os.path.join(self.save_dir, self.sec_uid)
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)

            self._download_videos(videos, user_dir)

        except Exception as e:
            console.print(f"[red][Error][/red] Failed to fetch user page: {e}")
        finally:
            self.driver.quit()

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
            with requests.get(url, stream=True) as response:
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
