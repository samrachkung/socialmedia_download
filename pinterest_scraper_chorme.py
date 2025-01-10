import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from rich.console import Console
from rich.progress import track
import requests

console = Console()

def initialize_driver():
    """Initialize a Selenium WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def fetch_pinterest_images_and_captions(username, driver):
    """Fetch all image URLs and captions using Selenium."""
    url = f"https://www.pinterest.com/{username}/"
    console.log(f"[cyan]Fetching data from {url}...[/cyan]")

    driver.get(url)
    time.sleep(3)  # Allow the page to load

    # Scroll down multiple times to load more content
    for _ in range(10):
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(2)

    # Locate all pins
    pins = driver.find_elements(By.CSS_SELECTOR, 'div[data-test-id="pin"]')

    image_data = []
    for pin in pins:
        try:
            # Extract image URL
            img_tag = pin.find_element(By.CSS_SELECTOR, "img")
            image_url = img_tag.get_attribute("src")

            # Extract caption
            caption = pin.get_attribute("aria-label") or "No caption available."

            image_data.append({"url": image_url, "caption": caption})
        except Exception as e:
            console.log(f"[red]Error extracting data from a pin: {e}[/red]")

    console.log(f"[green]Found {len(image_data)} images with captions.[/green]")
    return image_data


def download_images_and_captions(image_data, username):
    """Download images and save captions."""
    if not os.path.exists(f"./pinterest/{username}"):
        os.makedirs(f"./pinterest/{username}")

    console.log("[cyan][Status][/cyan] Starting download...")

    for idx, data in track(enumerate(image_data, start=1), description="Downloading images..."):
        try:
            image_url = data["url"]
            caption = data["caption"]
            filename = f"image_{idx}"
            image_path = f"./pinterest/{username}/{filename}.jpg"
            caption_path = f"./pinterest/{username}/{filename}.txt"

            # Download the image
            if not os.path.exists(image_path):
                image_bytes = requests.get(image_url, stream=True).content
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)
                console.log(f"[green][File][/green] {image_path} downloaded.")

            # Save the caption
            with open(caption_path, "w", encoding="utf-8") as txt_file:
                txt_file.write(caption)
            console.log(f"[blue][Caption][/blue] {caption_path} saved.")
        except Exception as e:
            console.log(f"[red]Error downloading image or saving caption: {e}[/red]")


def main():
    username = input("Enter Pinterest username: ").strip()
    if not username:
        console.log("[red]Error: Username cannot be empty.[/red]")
        return

    driver = initialize_driver()

    try:
        image_data = fetch_pinterest_images_and_captions(username, driver)

        if not image_data:
            console.log("[red]No images found or failed to fetch images.[/red]")
            return

        download_images_and_captions(image_data, username)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
