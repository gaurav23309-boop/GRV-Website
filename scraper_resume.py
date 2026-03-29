#!/usr/bin/env python3
"""Resume scraping from where we left off (Tension Sensor onward)."""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re

BASE_URL = "https://www.7sensor.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
IMAGE_DIR = "/Users/gaurav/Desktop/upscale/7sensor"
OUTPUT_JSON = "/Users/gaurav/Desktop/EVERYTHING/GRV/product_data.json"

# Only remaining categories
CATEGORIES = {
    "Tension Sensor": "/Tension-Sensor-pl46524157.html",
    "Miniature Load Cell": "/Miniature-Load-Cell-pl45524157.html",
    "Column Type Load Cells": "/Column-Type-Load-Cells-pl44524157.html",
    "Multi-Axial Force Sensor": "/Multi-Axial-Force-Sensor-pl43524157.html",
    "Weighing Modules": "/Weighing-Modules-pl42524157.html",
    "Dynamic Torque Sensor": "/Dynamic-Torque-Sensor-pl41524157.html",
    "Strain Torque Sensor": "/Strain-Torque-Sensor-pl40524157.html",
    "Dynamometer": "/Dynamometer-pl49524157.html",
    "Motor Test Bench": "/Motor-Test-Bench-pl48424157.html",
    "Indicator": "/Indicator-pl47424157.html",
    "Junction Box": "/Junction-Box-pl46424157.html",
    "Load Cell Transmitters": "/Load-Cell-Transmitters-pl45424157.html",
}

def fetch_page(url):
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return resp
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return None

def get_product_links(category_url):
    resp = fetch_page(BASE_URL + category_url)
    if not resp:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.search(r'-pd\d+\.html', href):
            full_url = href if href.startswith("http") else BASE_URL + href
            if full_url not in links:
                links.append(full_url)
    return links

def extract_model_from_url(url):
    path = url.split("/")[-1]
    match = re.match(r'((?:DY[A-Z]*-?\d*[A-Z]*\d*(?:-\d+[A-Z]*)?|[A-Z]+\d+[A-Z]*(?:-\d+)?|D\d+[A-Z]*))', path)
    if match:
        return match.group(1)
    parts = path.split("-")
    if len(parts) >= 2:
        return "-".join(parts[:2])
    return parts[0]

def scrape_product(url):
    resp = fetch_page(url)
    if not resp:
        return None
    soup = BeautifulSoup(resp.text, "html.parser")
    product = {"url": url, "images": [], "specs": {}, "features": [], "description": ""}

    title_tag = soup.find("h1") or soup.find("h2")
    if title_tag:
        product["full_title"] = title_tag.get_text(strip=True)

    product["model"] = extract_model_from_url(url)

    for img in soup.find_all("img"):
        src = img.get("data-src") or img.get("src") or ""
        if not src:
            continue
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            src = BASE_URL + src
        if "micyjz.com" in src and "logo" not in src.lower() and "icon" not in src.lower() and "banner" not in src.lower() and "flag" not in src.lower():
            high_res = re.sub(r'-\d+-\d+\.', '.', src)
            if high_res not in product["images"]:
                product["images"].append(high_res)

    for div in soup.find_all(style=re.compile(r'background-image')):
        style = div.get("style", "")
        urls = re.findall(r'url["\']?(.*?)["\']?\)', style)
        for u in urls:
            if u.startswith("//"):
                u = "https:" + u
            if "micyjz.com" in u:
                high_res = re.sub(r'-\d+-\d+\.', '.', u)
                if high_res not in product["images"]:
                    product["images"].append(high_res)

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                val = cells[-1].get_text(strip=True)
                if key and val and key != val:
                    product["specs"][key] = val

    text = soup.get_text()
    feature_section = re.search(r'(?:Features?|FEATURES?)[:\s]*(.*?)(?:Specification|Application|Description|\n\n)', text, re.DOTALL)
    if feature_section:
        features_text = feature_section.group(1)
        for line in features_text.split("\n"):
            line = line.strip().strip("·•-")
            if line and len(line) > 3:
                product["features"].append(line)

    desc_div = soup.find(class_=re.compile(r'description'))
    if desc_div:
        product["description"] = desc_div.get_text(strip=True)[:500]

    sku_items = soup.find_all(class_=re.compile(r'radio-choose'))
    ranges = []
    for item in sku_items:
        r = item.get_text(strip=True)
        if r:
            ranges.append(r)
    if ranges:
        product["ranges"] = ranges

    return product

def download_image(url, save_path):
    if os.path.exists(save_path):
        return True
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"    Failed to download {url}: {e}")
        return False

def main():
    # Load existing data
    with open(OUTPUT_JSON, "r") as f:
        all_products = json.load(f)

    for cat_name, cat_url in CATEGORIES.items():
        if cat_name in all_products:
            print(f"Skipping {cat_name} (already done)")
            continue

        print(f"\n{'='*60}")
        print(f"Category: {cat_name}")
        print(f"{'='*60}")

        img_dir = os.path.join(IMAGE_DIR, cat_name)
        os.makedirs(img_dir, exist_ok=True)

        print(f"  Fetching product links...")
        links = get_product_links(cat_url)
        print(f"  Found {len(links)} products")

        products = []
        for i, link in enumerate(links):
            model = extract_model_from_url(link)
            print(f"  [{i+1}/{len(links)}] Scraping {model}...")

            product = scrape_product(link)
            if product:
                product["category"] = cat_name
                for j, img_url in enumerate(product["images"][:3]):
                    ext = os.path.splitext(img_url.split("?")[0])[-1] or ".jpg"
                    if j == 0:
                        fname = f"{product['model']}{ext}"
                    else:
                        fname = f"{product['model']}_{j+1}{ext}"
                    save_path = os.path.join(img_dir, fname)
                    if download_image(img_url, save_path):
                        product[f"local_image_{j}"] = save_path
                        print(f"    Downloaded: {fname}")
                products.append(product)
            time.sleep(1.5)

        all_products[cat_name] = products
        with open(OUTPUT_JSON, "w") as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)
        print(f"  Saved {len(products)} products. Progress saved.")
        time.sleep(2)

    print(f"\n{'='*60}")
    print("SCRAPING COMPLETE!")
    print(f"{'='*60}")
    total = sum(len(v) for v in all_products.values())
    print(f"Total products scraped: {total}")
    for cat, prods in all_products.items():
        print(f"  {cat}: {len(prods)} products")

if __name__ == "__main__":
    main()
