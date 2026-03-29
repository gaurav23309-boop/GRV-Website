#!/usr/bin/env python3
"""
7sensor.com Product Scraper for GRV Automation
Scrapes product images, specs, and details from all categories.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
from urllib.parse import urljoin

BASE_URL = "https://www.7sensor.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
IMAGE_DIR = "/Users/gaurav/Desktop/upscale/7sensor"
OUTPUT_JSON = "/Users/gaurav/Desktop/EVERYTHING/GRV/product_data.json"

CATEGORIES = {
    "C3-C6 Load Cell": "/C3-C6-Load-Cell-pl49161686.html",
    "S Type Load Cells": "/S-Type-Load-Cells-pl40624157.html",
    "Capsule Type Load Cell": "/Capsule-Type-Load-Cell-pl49624157.html",
    "Spoke Type Load Cells": "/Spoke-Type-Load-Cells-pl48524157.html",
    "Shear Beam Load Cells": "/Shear-Beam-Load-Cells-pl47524157.html",
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
    """Fetch a page with retry logic."""
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
    """Get all product page links from a category page."""
    resp = fetch_page(BASE_URL + category_url)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    links = []

    # Look for product links in the product list
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Product detail pages have 'pd' followed by numbers in the URL
        if re.search(r'-pd\d+\.html', href):
            full_url = href if href.startswith("http") else BASE_URL + href
            if full_url not in links:
                links.append(full_url)

    return links

def extract_model_from_url(url):
    """Extract model number from product URL."""
    # URL format: /DYLY-101-description-pd123456.html
    path = url.split("/")[-1]
    # Try to get the model prefix (e.g., DYLY-101, DYN-200, etc.)
    match = re.match(r'((?:DY[A-Z]*-?\d*[A-Z]*\d*(?:-\d+[A-Z]*)?|[A-Z]+\d+[A-Z]*(?:-\d+)?|D\d+[A-Z]*))', path)
    if match:
        return match.group(1)
    # Fallback: take first segment before long description
    parts = path.split("-")
    if len(parts) >= 2:
        return "-".join(parts[:2])
    return parts[0]

def scrape_product(url):
    """Scrape a single product page for all details."""
    resp = fetch_page(url)
    if not resp:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    product = {"url": url, "images": [], "specs": {}, "features": [], "description": ""}

    # Extract product title
    title_tag = soup.find("h1") or soup.find("h2")
    if title_tag:
        product["full_title"] = title_tag.get_text(strip=True)

    # Extract model from URL
    product["model"] = extract_model_from_url(url)

    # Extract ALL images - look for high-res versions
    for img in soup.find_all("img"):
        src = img.get("data-src") or img.get("src") or ""
        if not src:
            continue
        # Fix protocol-relative URLs
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            src = BASE_URL + src

        # Filter for product images (from their CDN), skip logos/icons
        if "micyjz.com" in src and "logo" not in src.lower() and "icon" not in src.lower() and "banner" not in src.lower() and "flag" not in src.lower():
            # Try to get highest resolution version
            # Remove size suffixes like -100-100 or -800-800
            high_res = re.sub(r'-\d+-\d+\.', '.', src)
            if high_res not in product["images"]:
                product["images"].append(high_res)

    # Also check for background-image styles
    for div in soup.find_all(style=re.compile(r'background-image')):
        style = div.get("style", "")
        urls = re.findall(r'url\(["\']?(.*?)["\']?\)', style)
        for u in urls:
            if u.startswith("//"):
                u = "https:" + u
            if "micyjz.com" in u:
                high_res = re.sub(r'-\d+-\d+\.', '.', u)
                if high_res not in product["images"]:
                    product["images"].append(high_res)

    # Extract specs from tables
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                val = cells[-1].get_text(strip=True)
                if key and val and key != val:
                    product["specs"][key] = val

    # Extract features - look for bullet lists near "feature" text
    text = soup.get_text()
    feature_section = re.search(r'(?:Features?|FEATURES?)[:\s]*(.*?)(?:Specification|Application|Description|\n\n)', text, re.DOTALL)
    if feature_section:
        features_text = feature_section.group(1)
        for line in features_text.split("\n"):
            line = line.strip().strip("·•-")
            if line and len(line) > 3:
                product["features"].append(line)

    # Extract description
    desc_div = soup.find(class_=re.compile(r'description'))
    if desc_div:
        product["description"] = desc_div.get_text(strip=True)[:500]

    # Extract range/capacity from SKU params
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
    """Download an image to the specified path."""
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

def scrape_category(cat_name, cat_url):
    """Scrape all products in a category."""
    print(f"\n{'='*60}")
    print(f"Category: {cat_name}")
    print(f"{'='*60}")

    # Create image directory
    img_dir = os.path.join(IMAGE_DIR, cat_name)
    os.makedirs(img_dir, exist_ok=True)

    # Get product links
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

            # Download images
            for j, img_url in enumerate(product["images"][:3]):  # Max 3 images per product
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

        time.sleep(1.5)  # Be polite

    return products

def main():
    all_products = {}

    for cat_name, cat_url in CATEGORIES.items():
        products = scrape_category(cat_name, cat_url)
        all_products[cat_name] = products

        # Save progress after each category
        with open(OUTPUT_JSON, "w") as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)

        print(f"  Saved {len(products)} products. Progress saved to JSON.")
        time.sleep(2)  # Delay between categories

    # Final summary
    print(f"\n{'='*60}")
    print("SCRAPING COMPLETE!")
    print(f"{'='*60}")
    total = sum(len(v) for v in all_products.values())
    print(f"Total products scraped: {total}")
    print(f"Data saved to: {OUTPUT_JSON}")
    print(f"Images saved to: {IMAGE_DIR}/")

    for cat, prods in all_products.items():
        print(f"  {cat}: {len(prods)} products")

if __name__ == "__main__":
    main()
