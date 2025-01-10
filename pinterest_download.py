import os
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import track

console = Console()

def fetch_pinterest_images(username):
    """Fetch all image URLs from a Pinterest user's profile."""
    base_url = f"https://www.pinterest.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(base_url, headers=headers)
        if response.status_code != 200:
            console.log(f"[red]Failed to fetch Pinterest profile: {response.status_code}[/red]")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        # Extract all image URLs
        images = soup.find_all("img")
        image_urls = [img["src"] for img in images if "src" in img.attrs]

        console.log(f"[green]Found {len(image_urls)} images on the profile.[/green]")
        return image_urls
    except Exception as e:
        console.log(f"[red]Error fetching images: {e}[/red]")
        return []


def download_images(image_urls, username):
    """Download all images from the URLs."""
    if not os.path.exists(f"./pinterest/{username}"):
        os.makedirs(f"./pinterest/{username}")

    console.log("[cyan][Status][/cyan] Starting download...")

    for idx, url in track(enumerate(image_urls), description="Downloading images..."):
        try:
            image_data = requests.get(url, stream=True).content
            filepath = f"./pinterest/{username}/image_{idx+1}.jpg"

            with open(filepath, "wb") as file:
                file.write(image_data)

            console.log(f"[green][File][/green] {filepath} downloaded.")
        except Exception as e:
            console.log(f"[red]Error downloading image: {e}[/red]")


def main():
    username = input("Enter Pinterest username: ").strip()
    if not username:
        console.log("[red]Error: Username cannot be empty.[/red]")
        return

    image_urls = fetch_pinterest_images(username)

    if not image_urls:
        console.log("[red]No images found or failed to fetch images.[/red]")
        return

    download_images(image_urls, username)


if __name__ == "__main__":
    main()
