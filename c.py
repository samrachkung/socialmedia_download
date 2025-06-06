import os
import re
import time
import requests
import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

def download_process(self, urls, save_path):
    driver = None
    try:
        # Initialize browser
        self.update_status(message="Initializing browser...")
        firefox_options = Options()
        firefox_options.set_preference("dom.webnotifications.enabled", False)
        firefox_options.set_preference("media.volume_scale", "0.0")
        firefox_options.set_preference("general.useragent.override", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")

        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=firefox_options)

        # Facebook login
        self.update_status(message="Logging in to Facebook...")
        driver.get("https://www.facebook.com/login")
        
        try:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(self.fb_email.get())
            driver.find_element(By.NAME, "pass").send_keys(self.fb_password.get())
            driver.find_element(By.NAME, "login").click()
            WebDriverWait(driver, 30).until(lambda d: "facebook.com/login" not in d.current_url)
        except Exception as e:
            messagebox.showerror("Login Failed", f"Failed to authenticate with Facebook: {str(e)}")
            return

        # Process URLs
        for url in urls:
            if self.stop_download:
                break
            
            try:
                clean_url = re.sub(r'\?.*', '', url).replace("//web.", "//www.")
                profile_id = self.extract_profile_id(clean_url)
                profile_path = os.path.join(save_path, profile_id)
                os.makedirs(profile_path, exist_ok=True)
                
                photos_url = f"{clean_url}/photos" if "/photos" not in clean_url.lower() else clean_url
                driver.get(photos_url)
                time.sleep(3)
                
                self.update_status(message="Loading photos...")
                prev_height = -1
                for _ in range(15):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == prev_height:
                        break
                    prev_height = new_height
                
                photo_links = driver.execute_script("""
                    return Array.from(document.querySelectorAll(
                        'a[href*="/photo/"], a[href*="fbid="], div[data-pagelet="MediaViewerPhoto"] a'
                    )).map(a => a.href);
                """)
                
                self.update_status(message=f"Found {len(photo_links)} photos. Downloading...")
                for photo_url in photo_links:
                    if self.stop_download:
                        break
                    
                    try:
                        driver.get(photo_url)
                        time.sleep(2)

                        img_element = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.XPATH, "//img[contains(@src, 'scontent') and contains(@src, 'fbcdn.net')]")
                        ))
                        img_url = img_element.get_attribute('src')
                        
                        response = requests.get(img_url, headers={
                            'User-Agent': 'Mozilla/5.0',
                            'Referer': driver.current_url
                        }, stream=True, timeout=30)
                        
                        if response.status_code == 200:
                            photo_id_match = re.search(r'\d{10,}', img_url.split('/')[-1])
                            photo_id = photo_id_match[0] if photo_id_match else "unknown"
                            filename = f"{profile_id}_{photo_id}.jpg"
                            
                            with open(os.path.join(profile_path, filename), 'wb') as f:
                                for chunk in response.iter_content(8192):
                                    f.write(chunk)
                            
                            # Auto-enter character code text
                            with open(os.path.join(profile_path, f"{photo_id}.txt"), 'w', encoding='utf-8') as f:
                                f.write("Downloaded from Facebook\n")
                            
                            self.downloaded_photos += 1
                            self.update_status(downloaded=self.downloaded_photos, message=f"Downloaded {filename}")
                    except Exception as e:
                        self.failed_downloads += 1
                        self.update_status(message=f"Photo error: {str(e)}")
                
                self.processed_urls += 1
                self.update_status(processed=self.processed_urls)
            except Exception as e:
                self.failed_downloads += 1
                self.update_status(message=f"Profile error: {str(e)}")
    
    except Exception as e:
        messagebox.showerror("Critical Error", f"Application failed: {str(e)}")
    
    finally:
        if driver:
            driver.quit()
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_status(message="Download completed" if not self.stop_download else "Download stopped")
