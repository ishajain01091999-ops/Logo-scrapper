import streamlit as st
import requests
import os
import base64
from PIL import Image
import io
import zipfile
import time

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


# ==========================
# CONFIG
# ==========================

OUTPUT_FOLDER = "logos"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

SOCIAL_KEYWORDS = [
    "facebook","instagram","twitter","linkedin",
    "youtube","pinterest","whatsapp","telegram"
]

IGNORE_KEYWORDS = [
    "product","service","banner","slider",
    "hero","gallery","thumbnail"
]


# ==========================
# VALIDATE IMAGE
# ==========================

def valid_logo(src):

    if not src:
        return False

    s = src.lower()

    if any(x in s for x in SOCIAL_KEYWORDS):
        return False

    if any(x in s for x in IGNORE_KEYWORDS):
        return False

    return True


# ==========================
# SAVE IMAGE / SVG
# ==========================

def save_logo(url, site):

    try:

        filename = site.replace("https://","").replace("http://","").replace("/","_")

        # BASE64 IMAGE
        if url.startswith("data:image"):

            header, encoded = url.split(",",1)
            data = base64.b64decode(encoded)

            try:
                Image.open(io.BytesIO(data))
            except:
                return None

            path = os.path.join(OUTPUT_FOLDER, filename + ".png")

            with open(path,"wb") as f:
                f.write(data)

            return path


        # SVG URL
        if url.endswith(".svg"):

            r = requests.get(url,headers=HEADERS,timeout=10)

            if r.status_code == 200:

                path = os.path.join(OUTPUT_FOLDER, filename + ".svg")

                with open(path,"wb") as f:
                    f.write(r.content)

                return path


        # NORMAL IMAGE
        r = requests.get(url,headers=HEADERS,timeout=10)

        if r.status_code != 200:
            return None

        content_type = r.headers.get("content-type","")

        if "image" not in content_type:
            return None

        path = os.path.join(OUTPUT_FOLDER, filename + ".png")

        with open(path,"wb") as f:
            f.write(r.content)

        return path

    except:
        return None


# ==========================
# FAST HTML SCRAPER
# ==========================

def detect_logo(site):

    try:

        r = requests.get(site,headers=HEADERS,timeout=10)

        soup = BeautifulSoup(r.text,"html.parser")

        header = soup.find("header")

        if header:

            imgs = header.find_all("img")

            for img in imgs:

                src = img.get("src") or img.get("data-src") or img.get("data-lazy")

                if valid_logo(src):
                    return urljoin(site,src)


        imgs = soup.find_all("img",class_=lambda x:x and "logo" in x.lower())

        for img in imgs:

            src = img.get("src") or img.get("data-src")

            if valid_logo(src):
                return urljoin(site,src)


        imgs = soup.find_all("img",id=lambda x:x and "logo" in x.lower())

        for img in imgs:

            src = img.get("src") or img.get("data-src")

            if valid_logo(src):
                return urljoin(site,src)


        imgs = soup.find_all("img")

        for img in imgs:

            src = img.get("src")

            if src and src.startswith("data:image"):
                return src


        divs = soup.find_all(style=True)

        for div in divs:

            style = div.get("style")

            if "background-image" in style:

                start = style.find("url(")+4
                end = style.find(")")

                bg = style[start:end].replace('"',"").replace("'","")

                if valid_logo(bg):
                    return urljoin(site,bg)


        meta = soup.find("meta",property="og:image")

        if meta:
            return urljoin(site,meta["content"])


        icon = soup.find("link",rel=lambda x:x and "icon" in x.lower())

        if icon:
            return urljoin(site,icon["href"])


    except:
        pass

    return None


# ==========================
# SELENIUM FALLBACK
# ==========================

def selenium_logo(site):

    try:

        options = Options()

        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)

        driver.get(site)

        time.sleep(6)

        headers = driver.find_elements(By.TAG_NAME,"header")

        for header in headers:

            imgs = header.find_elements(By.TAG_NAME,"img")

            for img in imgs:

                src = img.get_attribute("src")

                if src and valid_logo(src):

                    driver.quit()
                    return src


            svgs = header.find_elements(By.TAG_NAME,"svg")

            if svgs:

                svg_html = svgs[0].get_attribute("outerHTML")

                driver.quit()

                filename = site.replace("https://","").replace("/","_")
                path = os.path.join(OUTPUT_FOLDER, filename + ".svg")

                with open(path,"w",encoding="utf-8") as f:
                    f.write(svg_html)

                return path


        imgs = driver.find_elements(By.TAG_NAME,"img")

        for img in imgs:

            src = img.get_attribute("src")

            if src and valid_logo(src):

                driver.quit()
                return src

        driver.quit()

    except:
        pass

    return None


# ==========================
# PROCESS SITE
# ==========================

def process_site(site):

    logo = detect_logo(site)

    if not logo:

        logo = selenium_logo(site)

        if logo and logo.endswith(".svg"):
            return site,logo

    if logo:

        path = save_logo(logo,site)

        return site,path

    return site,None


# ==========================
# ZIP DOWNLOAD
# ==========================

def create_zip():

    zip_path = "logos.zip"

    with zipfile.ZipFile(zip_path,"w") as zipf:

        for file in os.listdir(OUTPUT_FOLDER):

            zipf.write(os.path.join(OUTPUT_FOLDER,file),file)

    return zip_path


# ==========================
# STREAMLIT UI
# ==========================

st.title("Universal Website Logo Scraper")

urls = st.text_area(
"Paste Websites (one per line)",
height=200
)

if st.button("Scrape Logos"):

    sites = [x.strip() for x in urls.split("\n") if x.strip()]

    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:

        for r in executor.map(process_site,sites):
            results.append(r)

    st.success("Scraping Completed")

    for site,path in results:

        if path and os.path.exists(path):

            st.write(site)

            if path.endswith(".svg"):

                with open(path,"r",encoding="utf-8") as f:
                    st.markdown(f.read(),unsafe_allow_html=True)

            else:

                st.image(path,width=150)

        else:

            st.write(site,"❌ Logo not found")

    zip_file = create_zip()

    with open(zip_file,"rb") as f:

        st.download_button(
            "Download All Logos",
            f,
            file_name="logos.zip"
        )
