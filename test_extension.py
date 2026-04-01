import os
import time
import requests
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# =========================================================
# CONFIG
# =========================================================
OUTPUT_FOLDER = os.path.join(os.getcwd(), "logos")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

WEBSITES = [
  "https://raheels-cooking-catering.grexa.site/",
]

# =========================================================
# SELENIUM SETUP
# =========================================================
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def save_logo(logo_url, site):
    response = requests.get(logo_url, timeout=15)
    img = Image.open(BytesIO(response.content)).convert("RGBA")

    filename = site.replace("https://", "").replace("http://", "").replace("/", "_")
    path = os.path.join(OUTPUT_FOLDER, f"{filename}.png")

    img.save(path, "PNG")
    print(f"💾 Saved: {path}")

def is_valid_logo(src):
    return src.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))

# =========================================================
# MAIN LOGIC
# =========================================================
for site in WEBSITES:
    try:
        print(f"\n🔍 Opening: {site}")
        driver.get(site)

        # Allow Dukaan lazy loading
        time.sleep(6)

        logo_url = None

        # 1️⃣ Check HEADER first (Dukaan logo always here)
        headers = driver.find_elements(By.TAG_NAME, "header")
        for header in headers:
            imgs = header.find_elements(By.TAG_NAME, "img")
            for img in imgs:
                src = img.get_attribute("src")
                if src and is_valid_logo(src):
                    logo_url = src
                    break
            if logo_url:
                break

        # 2️⃣ Fallback: first image on page
        if not logo_url:
            imgs = driver.find_elements(By.TAG_NAME, "img")
            for img in imgs:
                src = img.get_attribute("src")
                if src and is_valid_logo(src):
                    logo_url = src
                    break

        if not logo_url:
            print("❌ No logo found")
            continue

        print(f"✅ Logo found: {logo_url}")
        save_logo(logo_url, site)

    except Exception as e:
        print(f"⚠️ Error on {site}: {e}")

driver.quit()

print("\n🎉 All logos processed successfully")
