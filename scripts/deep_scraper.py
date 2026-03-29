#!/usr/bin/env python3
"""
Deep scraper for 7sensor.com — finds images for 113 missing GRV products.
Downloads images, removes backgrounds with rembg, updates index.html.
"""

import requests
from bs4 import BeautifulSoup
import os
import re
import time
import subprocess
import shutil
import json
from urllib.parse import urljoin

BASE_URL = "https://www.7sensor.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

OUTPUT_DIR = "/Users/gaurav/Desktop/EVERYTHING/GRV/html/products"
INDEX_HTML = "/Users/gaurav/Desktop/EVERYTHING/GRV/html/index.html"
REMBG = "/opt/homebrew/bin/rembg"
TEMP_DIR = "/tmp/grv_scraper_temp"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

CATEGORIES = {
    "C3-C6 Load Cell":          "/C3-C6-Load-Cell-pl49161686.html",
    "S Type Load Cells":         "/S-Type-Load-Cells-pl40624157.html",
    "Capsule Type Load Cell":    "/Capsule-Type-Load-Cell-pl49624157.html",
    "Spoke Type Load Cells":     "/Spoke-Type-Load-Cells-pl48524157.html",
    "Shear Beam Load Cells":     "/Shear-Beam-Load-Cells-pl47524157.html",
    "Tension Sensor":            "/Tension-Sensor-pl46524157.html",
    "Miniature Load Cell":       "/Miniature-Load-Cell-pl45524157.html",
    "Column Type Load Cells":    "/Column-Type-Load-Cells-pl44524157.html",
    "Multi-Axial Force Sensor":  "/Multi-Axial-Force-Sensor-pl43524157.html",
    "Weighing Modules":          "/Weighing-Modules-pl42524157.html",
    "Dynamic Torque Sensor":     "/Dynamic-Torque-Sensor-pl41524157.html",
    "Strain Torque Sensor":      "/Strain-Torque-Sensor-pl40524157.html",
    "Dynamometer":               "/Dynamometer-pl49524157.html",
    "Motor Test Bench":          "/Motor-Test-Bench-pl48424157.html",
    "Indicator":                 "/Indicator-pl47424157.html",
    "Junction Box":              "/Junction-Box-pl46424157.html",
    "Load Cell Transmitters":    "/Load-Cell-Transmitters-pl45424157.html",
}

# 113 missing products: model → output filename (without extension)
# The img path in index.html is the value after the last /
MISSING_PRODUCTS = {
    "DYHLJ":            "DYHLJ",
    "DYX-306B":         "DYX-306B",
    "DYX-306C":         "DYX-306C",
    "DYX-306D":         "DYX-306D",
    "DYX-307":          "DYX-307",
    "DYX-309":          "DYX-309",
    "DYWL-001":         "DYWL-001",
    "DYQ-101":          "DYQ-101",
    "DYYB-002":         "DYYB-002",
    "DYZC-055":         "DYZC-055",
    "DYZHL":            "DYZHL",
    "DYZL-104":         "DYZL-104",
    "DYZL-108":         "DYZL-108",
    "DYHW-112":         "DYHW-112",
    "DYHW-120":         "DYHW-120",
    "DYMH-108":         "DYMH-108",
    "DYMH-108D":        "DYMH-108D",
    "DYMH-109":         "DYMH-109",
    "DYMH-113":         "DYMH-113",
    "DYPB-001":         "DYPB-001",
    "DYPB-002":         "DYPB-002",
    "DYPB-003":         "DYPB-003",
    "DYTB-002":         "DYTB-002",
    "DYZ-104":          "DYZ-104",
    "DYZ-105":          "DYZ-105",
    "DYZ-106":          "DYZ-106",
    "DYZ-107":          "DYZ-107",
    "DYZ-108":          "DYZ-108",
    "DYZ-109":          "DYZ-109",
    "D620":             "D620",
    "DYZ-016":          "DYZ-016",
    "DYZ-018":          "DYZ-018",
    "DYZ-13E":          "DYZ-13E",
    "DYHX-002":         "DYHX-002",
    "DYHX-002M":        "DYHX-002M",
    "DYHX-003":         "DYHX-003",
    "DYHX-003M":        "DYHX-003M",
    "DYHX-004":         "DYHX-004",
    "DYDW-002":         "DYDW-002",
    "DYDW-004":         "DYDW-004",
    "DYDW-005":         "DYDW-005",
    "DYDW-006":         "DYDW-006",
    "DYDW-007":         "DYDW-007",
    "DYDW-008":         "DYDW-008",
    "DYDW-009":         "DYDW-009",
    "DYDW-y25":         "DYDW-y25",
    "DYDW-y45":         "DYDW-y45",
    "DYDW-y80":         "DYDW-y80",
    "DYDW-y82":         "DYDW-y82",
    "DYDW-y125":        "DYDW-y125",
    "DYDW-y200":        "DYDW-y200",
    "DYFW":             "DYFW",
    "DYFWC":            "DYFWC",
    "DYMK-007":         "DYMK-007",
    "DYMK-008":         "DYMK-008",
    "DYZY-001":         "DYZY-001",
    "DYDC-001":         "DYDC-001",
    "DXJN-101":         "DXJN-101",
    "DXJN-102":         "DXJN-102",
    "DXJN-103":         "DXJN-103",
    "DXJN-104":         "DXJN-104",
    "DXJN-105":         "DXJN-105",
    "DXJN-106":         "DXJN-106",
    "DXJN-107":         "DXJN-107",
    "DXJN-108":         "DXJN-108",
    "DXJN-110":         "DXJN-110",
    "DXJN-111":         "DXJN-111",
    "Inclination Detection System": "Inclination Detection System",
    "DYN-202":          "DYN-202",
    "DYN-203":          "DYN-203",
    "DYN-204":          "DYN-204",
    "DYN-206":          "DYN-206",
    "DYN-208":          "DYN-208",
    "DYN-209":          "DYN-209",
    "DYN-210MU":        "DYN-210MU",
    "DYN-212":          "DYN-212",
    "DYN-TA8":          "DYN-TA8",
    "DYJXH-S4":         "DYJXH-S4",
    "DYTX-101":         "DYTX-101",
    "BSQ-001":          "BSQ-001",
    "Four-Channel Weighing Transmitter": "Four-Channel Weighing Transmitter",
    "D530":             "D530",
    "DYFV12":           "DYFV12",
    "X503":             "X503",
    "DR304":            "DR304",
    "X508A":            "X508A",
    "X508B":            "X508B",
    "D740 Touch Screen": "D740 Touch Screen",
    "DY054W":           "DY054W",
    "DY054N":           "DY054N",
    "DY055":            "DY055",
    "XS05":             "XS05",
    "DY220":            "DY220",
    "DY220B":           "DY220B",
    "DY300":            "DY300",
    "DY300A":           "DY300A",
    "DYN-303":          "DYN-303",
    "DY6001":           "DY6001",
    "DYCSM":            "DYCSM",
    "DY300 MFC":        "DY300 MFC",
    "DY310":            "DY310",
    "DY320":            "DY320",
    "DY330":            "DY330",
    "DYHB":             "DYHB",
    "DYCHB":            "DYCHB",
    "LN96A":            "LN96A",
    "SSR21":            "SSR21",
    "XSB2":             "XSB2",
    "CH6":              "CH6",
    "700WC":            "700WC",
    "DY2025":           "DY2025",
    "DY3190":           "DY3190",
    "R305":             "R305",
}

# Map: model → img path key in index.html (what the img: field currently says, filename only)
# Some have _nobg.png already, some have .jpg — we detect this from HTML
HTML_IMG_MAP = {
    "DYHLJ": "DYHLJ.jpg",
    "DYX-306B": "DYX-306B.jpg",
    "DYX-306C": "DYX-306C.jpg",
    "DYX-306D": "DYX-306D.jpg",
    "DYX-307": "DYX-307.jpg",
    "DYX-309": "DYX-309.jpg",
    "DYWL-001": "DYWL-001.jpg",
    "DYQ-101": "DYQ-101.jpg",
    "DYYB-002": "DYYB-002.jpg",
    "DYZC-055": "DYZC-055.jpg",
    "DYZHL": "DYZHL.jpg",
    "DYZL-104": "DYZL-104.jpg",
    "DYZL-108": "DYZL-108.jpg",
    "DYHW-112": "DYHW-112.jpg",
    "DYHW-120": "DYHW-120.jpg",
    "DYMH-108": "DYMH-108.jpg",
    "DYMH-108D": "DYMH-108D.jpg",
    "DYMH-109": "DYMH-109.jpg",
    "DYMH-113": "DYMH-113.jpg",
    "DYPB-001": "DYPB-001.jpg",
    "DYPB-002": "DYPB-002.jpg",
    "DYPB-003": "DYPB-003.jpg",
    "DYTB-002": "DYTB-002.jpg",
    "DYZ-104": "DYZ-104_nobg.png",
    "DYZ-105": "DYZ-105_nobg.png",
    "DYZ-106": "DYZ-106_nobg.png",
    "DYZ-107": "DYZ-107_nobg.png",
    "DYZ-108": "DYZ-108_nobg.png",
    "DYZ-109": "DYZ-109_nobg.png",
    "D620": "D620_nobg.png",
    "DYZ-016": "DYZ-016_nobg.png",
    "DYZ-018": "DYZ-018_nobg.png",
    "DYZ-13E": "DYZ-13E_nobg.png",
    "DYHX-002": "DYHX-002_nobg.png",
    "DYHX-002M": "DYHX-002M_nobg.png",
    "DYHX-003": "DYHX-003_nobg.png",
    "DYHX-003M": "DYHX-003M_nobg.png",
    "DYHX-004": "DYHX-004_nobg.png",
    "DYDW-002": "DYDW-002_nobg.png",
    "DYDW-004": "DYDW-004_nobg.png",
    "DYDW-005": "DYDW-005_nobg.png",
    "DYDW-006": "DYDW-006_nobg.png",
    "DYDW-007": "DYDW-007_nobg.png",
    "DYDW-008": "DYDW-008_nobg.png",
    "DYDW-009": "DYDW-009_nobg.png",
    "DYDW-y25": "DYDW-y25_nobg.png",
    "DYDW-y45": "DYDW-y45_nobg.png",
    "DYDW-y80": "DYDW-y80_nobg.png",
    "DYDW-y82": "DYDW-y82_nobg.png",
    "DYDW-y125": "DYDW-y125_nobg.png",
    "DYDW-y200": "DYDW-y200_nobg.png",
    "DYFW": "DYFW_nobg.png",
    "DYFWC": "DYFWC_nobg.png",
    "DYMK-007": "DYMK-007_nobg.png",
    "DYMK-008": "DYMK-008_nobg.png",
    "DYZY-001": "DYZY-001_nobg.png",
    "DYDC-001": "DYDC-001_nobg.png",
    "DXJN-101": "DXJN-101_nobg.png",
    "DXJN-102": "DXJN-102_nobg.png",
    "DXJN-103": "DXJN-103_nobg.png",
    "DXJN-104": "DXJN-104_nobg.png",
    "DXJN-105": "DXJN-105_nobg.png",
    "DXJN-106": "DXJN-106_nobg.png",
    "DXJN-107": "DXJN-107_nobg.png",
    "DXJN-108": "DXJN-108_nobg.png",
    "DXJN-110": "DXJN-110_nobg.png",
    "DXJN-111": "DXJN-111_nobg.png",
    "Inclination Detection System": "Inclination Detection System_nobg.png",
    "DYN-202": "DYN-202_nobg.png",
    "DYN-203": "DYN-203_nobg.png",
    "DYN-204": "DYN-204_nobg.png",
    "DYN-206": "DYN-206_nobg.png",
    "DYN-208": "DYN-208_nobg.png",
    "DYN-209": "DYN-209_nobg.png",
    "DYN-210MU": "DYN-210MU_nobg.png",
    "DYN-212": "DYN-212_nobg.png",
    "DYN-TA8": "DYN-TA8_nobg.png",
    "DYJXH-S4": "DYJXH-S4_nobg.png",
    "DYTX-101": "DYTX-101_nobg.png",
    "BSQ-001": "BSQ-001_nobg.png",
    "Four-Channel Weighing Transmitter": "FCWT_nobg.png",
    "D530": "D530_nobg.png",
    "DYFV12": "DYFV12_nobg.png",
    "X503": "X503_nobg.png",
    "DR304": "DR304_nobg.png",
    "X508A": "X508A_nobg.png",
    "X508B": "X508B_nobg.png",
    "D740 Touch Screen": "D740 Touch Screen_nobg.png",
    "DY054W": "DY054W_nobg.png",
    "DY054N": "DY054N_nobg.png",
    "DY055": "DY055_nobg.png",
    "XS05": "XS05_nobg.png",
    "DY220": "DY220_nobg.png",
    "DY220B": "DY220B_nobg.png",
    "DY300": "DY300_nobg.png",
    "DY300A": "DY300A_nobg.png",
    "DYN-303": "DYN-303_nobg.png",
    "DY6001": "DY6001_nobg.png",
    "DYCSM": "DYCSM_nobg.png",
    "DY300 MFC": "DY300 MFC_nobg.png",
    "DY310": "DY310_nobg.png",
    "DY320": "DY320_nobg.png",
    "DY330": "DY330_nobg.png",
    "DYHB": "DYHB_nobg.png",
    "DYCHB": "DYCHB_nobg.png",
    "LN96A": "LN96A_nobg.png",
    "SSR21": "SSR21_nobg.png",
    "XSB2": "XSB2_nobg.png",
    "CH6": "CH6_nobg.png",
    "700WC": "700WC_nobg.png",
    "DY2025": "DY2025_nobg.png",
    "DY3190": "DY3190_nobg.png",
    "R305": "R305_nobg.png",
}

# ─────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────

def log(msg):
    print(msg, flush=True)

def fetch_page(url, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return resp
        except Exception as e:
            log(f"    [attempt {attempt+1}] {url} -> {e}")
            if attempt < retries - 1:
                time.sleep(2)
    return None

def normalize(s):
    """Normalize model string for fuzzy matching."""
    return re.sub(r'[\s\-_]', '', s).upper()

def match_model(title_or_url, missing_set):
    """
    Given a product title or URL, return the matching model key from missing_set,
    or None. Uses fuzzy normalization.
    """
    norm_title = normalize(title_or_url)
    # Direct model code search: try each missing model
    for model in missing_set:
        norm_model = normalize(model)
        if norm_model in norm_title:
            return model
    return None

def get_all_pages(category_url):
    """Return list of all paginated page URLs for a category."""
    pages = [BASE_URL + category_url]
    resp = fetch_page(BASE_URL + category_url)
    if not resp:
        return pages

    soup = BeautifulSoup(resp.text, "html.parser")

    # Look for pagination: <a> tags with page numbers or next arrows
    seen_pages = set(pages)
    page_links = []

    # Common pagination patterns on Alibaba-style sites
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Pagination often uses ?p=2 or /page/2 or -2.html suffix on category
        if re.search(r'[?&]p=\d+|/page/\d+|-(\d+)\.html', href):
            full = href if href.startswith("http") else BASE_URL + href
            if full not in seen_pages:
                seen_pages.add(full)
                page_links.append(full)

    # Also look for page number text in anchors
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if text.isdigit() and int(text) > 1:
            full = href if href.startswith("http") else BASE_URL + href
            if full not in seen_pages and BASE_URL in full:
                seen_pages.add(full)
                page_links.append(full)

    pages.extend(page_links)
    log(f"    Category has {len(pages)} page(s)")
    return pages

def get_product_links(category_url):
    """Get all product page links from all pages of a category."""
    all_pages = get_all_pages(category_url)
    links = []
    seen = set()

    for page_url in all_pages:
        resp = fetch_page(page_url)
        if not resp:
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.search(r'-pd\d+\.html', href):
                full = href if href.startswith("http") else BASE_URL + href
                if full not in seen:
                    seen.add(full)
                    links.append(full)
        time.sleep(0.5)

    return links

def extract_best_image(soup):
    """Extract the highest-quality product image URL from a product page."""
    candidates = []

    # Strategy 1: look for main product image container
    # Common class patterns on 7sensor/Alibaba-style sites
    for selector in [
        {"class": re.compile(r'main.?img|product.?img|big.?img|detail.?img', re.I)},
        {"id": re.compile(r'main.?img|product.?img|big.?img', re.I)},
    ]:
        el = soup.find(["img", "div"], attrs=selector)
        if el:
            src = (el.get("data-src") or el.get("src") or
                   el.get("data-zoom-image") or el.get("data-original") or "")
            if src and "micyjz.com" in src:
                candidates.append(src)

    # Strategy 2: all img tags from micyjz CDN, prefer largest
    for img in soup.find_all("img"):
        src = (img.get("data-src") or img.get("src") or
               img.get("data-zoom-image") or img.get("data-original") or "")
        if not src:
            continue
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/") and not src.startswith("//"):
            src = BASE_URL + src
        if "micyjz.com" in src and not any(x in src.lower() for x in ["logo", "icon", "banner", "flag", "arrow", "btn"]):
            candidates.append(src)

    # Strategy 3: background-image styles
    for el in soup.find_all(style=re.compile(r'background-image', re.I)):
        style = el.get("style", "")
        for u in re.findall(r'url\(["\']?(.*?)["\']?\)', style):
            if u.startswith("//"):
                u = "https:" + u
            if "micyjz.com" in u:
                candidates.append(u)

    if not candidates:
        return None

    # De-duplicate and get highest res: strip size suffixes, prefer no -NxN
    seen_base = {}
    for src in candidates:
        if src.startswith("//"):
            src = "https:" + src
        # Remove size suffix like -100-100. or -800-600.
        base = re.sub(r'-\d{2,4}-\d{2,4}(?=\.\w{3,4})', '', src)
        # Skip tiny thumbnails explicitly
        if re.search(r'-[1-9]\d{0,1}-[1-9]\d{0,1}\.', src):
            continue
        if base not in seen_base:
            seen_base[base] = src

    if not seen_base:
        # fallback: just take the first candidate, deduped
        best = candidates[0]
        if best.startswith("//"):
            best = "https:" + best
        return re.sub(r'-\d+-\d+\.', '.', best)

    # Pick the one most likely to be large (no size suffix = original)
    for base, src in seen_base.items():
        if not re.search(r'-\d{2,4}-\d{2,4}\.', src):
            return base

    # else return first
    return list(seen_base.keys())[0]

def download_image(url, save_path):
    if os.path.exists(save_path):
        log(f"    Already exists: {save_path}")
        return True
    try:
        resp = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        log(f"    Downloaded: {os.path.basename(save_path)}")
        return True
    except Exception as e:
        log(f"    Download failed {url}: {e}")
        return False

def remove_background(input_path, output_path):
    if os.path.exists(output_path):
        log(f"    rembg already done: {os.path.basename(output_path)}")
        return True
    log(f"    Running rembg on {os.path.basename(input_path)} ...")
    try:
        result = subprocess.run(
            [REMBG, "i", input_path, output_path],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0 and os.path.exists(output_path):
            log(f"    Background removed: {os.path.basename(output_path)}")
            return True
        else:
            log(f"    rembg failed: {result.stderr}")
            return False
    except Exception as e:
        log(f"    rembg exception: {e}")
        return False

# ─────────────────────────────────────────────
# Main scraping logic
# ─────────────────────────────────────────────

def scrape_all_categories(remaining_models):
    """
    Scrape all categories, match products against remaining_models.
    Returns dict: model → image_url
    """
    found = {}  # model → downloaded raw image path

    for cat_name, cat_path in CATEGORIES.items():
        if not remaining_models:
            log("All products found! Stopping early.")
            break

        log(f"\n{'='*60}")
        log(f"Category: {cat_name}  ({len(remaining_models)} still needed)")
        log(f"{'='*60}")

        links = get_product_links(cat_path)
        log(f"  Found {len(links)} product links")

        for link in links:
            if not remaining_models:
                break

            # Quick check: does URL contain any of our model codes?
            url_lower = link.lower()
            url_path = link.split("/")[-1]

            resp = fetch_page(link)
            if not resp:
                time.sleep(1)
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # Get product title from h1
            title_tag = soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else ""

            # Also get model field from specs table if present
            model_from_page = ""
            for row in soup.find_all("tr"):
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True).lower()
                    val = cells[1].get_text(strip=True)
                    if "model" in key:
                        model_from_page = val
                        break

            # Try matching against all search strings
            search_strings = [title, url_path, model_from_page]
            matched_model = None
            for s in search_strings:
                if s:
                    m = match_model(s, remaining_models)
                    if m:
                        matched_model = m
                        break

            if not matched_model:
                time.sleep(0.8)
                continue

            log(f"  MATCH: '{matched_model}' <- title='{title}' url='{url_path}'")

            # Extract best image
            img_url = extract_best_image(soup)
            if not img_url:
                log(f"    No image found on page for {matched_model}")
                time.sleep(0.8)
                continue

            if img_url.startswith("//"):
                img_url = "https:" + img_url

            # Download raw image to temp
            ext = os.path.splitext(img_url.split("?")[0])[-1]
            if not ext or len(ext) > 5:
                ext = ".jpg"
            safe_model = re.sub(r'[^\w\-.]', '_', matched_model)
            raw_path = os.path.join(TEMP_DIR, f"{safe_model}{ext}")

            if download_image(img_url, raw_path):
                found[matched_model] = raw_path
                remaining_models.discard(matched_model)
                log(f"    Remaining: {len(remaining_models)}")

            time.sleep(1.0)

        time.sleep(1.5)

    return found

def process_images(found_map):
    """
    For each found raw image, run rembg and save to OUTPUT_DIR.
    Returns dict: model → final output path
    """
    results = {}
    total = len(found_map)
    for i, (model, raw_path) in enumerate(found_map.items(), 1):
        log(f"\n[{i}/{total}] Processing: {model}")

        # Determine output filename — always _nobg.png
        safe_model = re.sub(r'[^\w\-. ]', '_', model)
        out_filename = f"{safe_model}_nobg.png"
        out_path = os.path.join(OUTPUT_DIR, out_filename)

        if remove_background(raw_path, out_path):
            results[model] = out_path
        else:
            # If rembg fails, just copy the raw file as fallback
            fallback = os.path.join(OUTPUT_DIR, f"{safe_model}{os.path.splitext(raw_path)[-1]}")
            try:
                shutil.copy2(raw_path, fallback)
                results[model] = fallback
                log(f"    rembg failed, copied raw as fallback: {os.path.basename(fallback)}")
            except Exception as e:
                log(f"    Could not save fallback: {e}")

    return results

def update_html(results):
    """
    Update index.html img: references for all successfully processed products.
    results: model → final local path (full path)
    """
    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    updated_count = 0

    for model, final_path in results.items():
        out_filename = os.path.basename(final_path)
        html_img_value = f"products/{out_filename}"

        # The HTML entry looks like: img:'products/SOMETHING.ext'
        # We need to find the entry for this model and replace its img value.
        # Pattern: name:'MODEL' or name:'...' with img:'products/CURRENT_FILENAME'

        # Look up what the current img value should be
        current_img = HTML_IMG_MAP.get(model)
        if not current_img:
            log(f"  HTML update: no current img mapping for '{model}', skipping")
            continue

        current_html_path = f"products/{current_img}"
        old_pattern = f"img:'{current_html_path}'"
        new_value = f"img:'{html_img_value}'"

        if old_pattern in content:
            content = content.replace(old_pattern, new_value)
            updated_count += 1
            log(f"  HTML: {model}: '{current_html_path}' -> '{html_img_value}'")
        else:
            # Try double quotes
            old_pattern_dq = f'img:"{current_html_path}"'
            new_value_dq = f'img:"{html_img_value}"'
            if old_pattern_dq in content:
                content = content.replace(old_pattern_dq, new_value_dq)
                updated_count += 1
                log(f"  HTML (dq): {model}: '{current_html_path}' -> '{html_img_value}'")
            else:
                log(f"  HTML: pattern not found for '{model}' (looking for: {old_pattern})")

    if content != original:
        # Backup original
        backup = INDEX_HTML + ".bak"
        shutil.copy2(INDEX_HTML, backup)
        log(f"\n  Backed up index.html to {backup}")
        with open(INDEX_HTML, "w", encoding="utf-8") as f:
            f.write(content)
        log(f"  Updated index.html: {updated_count} img references changed")
    else:
        log("  No changes needed in index.html")

    return updated_count

# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

def main():
    log("=" * 60)
    log("GRV Deep Scraper — 7sensor.com")
    log(f"Looking for {len(MISSING_PRODUCTS)} products")
    log("=" * 60)

    remaining = set(MISSING_PRODUCTS.keys())

    # ── Phase 1: Scrape ──
    found_raw = scrape_all_categories(remaining)

    log(f"\n{'='*60}")
    log(f"SCRAPING DONE: Found images for {len(found_raw)}/{len(MISSING_PRODUCTS)} products")
    still_missing = set(MISSING_PRODUCTS.keys()) - set(found_raw.keys())
    if still_missing:
        log(f"Still missing ({len(still_missing)}):")
        for m in sorted(still_missing):
            log(f"  - {m}")

    # ── Phase 2: Remove backgrounds ──
    log(f"\n{'='*60}")
    log("PHASE 2: Removing backgrounds")
    log("=" * 60)
    processed = process_images(found_raw)

    # ── Phase 3: Update HTML ──
    log(f"\n{'='*60}")
    log("PHASE 3: Updating index.html")
    log("=" * 60)
    html_updates = update_html(processed)

    # ── Final report ──
    log(f"\n{'='*60}")
    log("FINAL REPORT")
    log("=" * 60)
    log(f"  Products found:    {len(found_raw)}/{len(MISSING_PRODUCTS)}")
    log(f"  Images processed:  {len(processed)}/{len(found_raw)}")
    log(f"  HTML entries updated: {html_updates}")

    final_missing = set(MISSING_PRODUCTS.keys()) - set(processed.keys())
    if final_missing:
        log(f"\n  STILL MISSING ({len(final_missing)}):")
        for m in sorted(final_missing):
            log(f"    - {m}")
    else:
        log("  All products have images!")

    # Save report JSON
    report = {
        "total_target": len(MISSING_PRODUCTS),
        "found": len(found_raw),
        "processed": len(processed),
        "html_updated": html_updates,
        "found_models": sorted(found_raw.keys()),
        "missing_models": sorted(final_missing),
    }
    report_path = "/Users/gaurav/Desktop/EVERYTHING/GRV/scripts/deep_scraper_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    log(f"\n  Report saved to: {report_path}")

if __name__ == "__main__":
    main()
