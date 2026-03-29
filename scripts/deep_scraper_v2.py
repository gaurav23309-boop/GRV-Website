#!/usr/bin/env python3
"""
Deep scraper v2 — finds images for 93 remaining missing GRV products.
Downloads images + removes backgrounds. Does NOT update website (review first).
"""

import requests
from bs4 import BeautifulSoup
import os, re, time, subprocess
from urllib.parse import urljoin

BASE_URL = "https://www.7sensor.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

OUTPUT_DIR = "/Users/gaurav/Desktop/EVERYTHING/GRV/html/products"
REMBG = "/opt/homebrew/bin/rembg"
TEMP_DIR = "/tmp/grv_scraper_v2"
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

# 93 products still missing
STILL_MISSING = [
    "DYWL-001", "DYZL-104", "DYZL-108", "DYHW-112", "DYMH-108D", "DYMH-109",
    "DYPB-001", "DYPB-002", "DYPB-003", "DYZ-104", "DYZ-105", "DYZ-106",
    "DYZ-107", "DYZ-108", "DYZ-109", "D620", "DYZ-016", "DYZ-018", "DYZ-13E",
    "DYHX-002", "DYHX-002M", "DYHX-003M", "DYHX-004", "DYDW-002", "DYDW-005",
    "DYDW-006", "DYDW-007", "DYDW-008", "DYDW-009", "DYDW-y25", "DYDW-y45",
    "DYDW-y80", "DYDW-y82", "DYDW-y125", "DYDW-y200", "DYFW", "DYFWC",
    "DYMK-008", "DYZY-001", "DYDC-001", "DXJN-101", "DXJN-102", "DXJN-103",
    "DXJN-104", "DXJN-105", "DXJN-106", "DXJN-107", "DXJN-108", "DXJN-110",
    "DXJN-111", "Inclination Detection System", "DYN-202", "DYN-203", "DYN-206",
    "DYN-208", "DYN-209", "DYN-210MU", "DYN-212", "DYN-TA8", "DYTX-101",
    "BSQ-001", "Four-Channel Weighing Transmitter", "D530", "DYFV12", "X503",
    "DR304", "X508A", "X508B", "D740 Touch Screen", "DY054W", "DY054N",
    "DY055", "XS05", "DY220", "DY220B", "DY300", "DY300A", "DYN-303",
    "DY6001", "DY300 MFC", "DY310", "DY320", "DY330", "DYHB", "DYCHB",
    "LN96A", "SSR21", "XSB2", "CH6", "700WC", "DY2025", "DY3190", "R305",
]

# Alternate search names
ALTERNATE_NAMES = {
    "Four-Channel Weighing Transmitter": ["FCWT", "four channel", "4-channel weighing", "4 channel"],
    "D740 Touch Screen": ["D740", "D740Touch"],
    "DY300 MFC": ["DY300MFC", "DY300 Multi", "multi function controller"],
    "Inclination Detection System": ["Inclination", "inclinometer"],
    "DYMH-108D": ["DYMH-108D", "DYMH108D"],
    "DYZ-13E": ["DYZ-13E", "DYZ13E"],
    "DYHX-002M": ["DYHX-002M", "DYHX002M"],
    "DYHX-003M": ["DYHX-003M", "DYHX003M"],
    "DYN-210MU": ["DYN-210MU", "DYN210MU"],
    "BSQ-001": ["BSQ-001", "BSQ001"],
    "DYTX-101": ["DYTX-101", "DYTX101"],
    "DYFV12": ["DYFV12", "DY-FV12"],
    "700WC": ["700WC", "700-WC"],
    "DY2025": ["DY2025", "DY-2025"],
    "DY3190": ["DY3190", "DY-3190"],
}

def log(msg):
    print(msg, flush=True)

def fetch(url, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r
        except Exception as e:
            if i < retries - 1:
                time.sleep(2)
    return None

def normalize(s):
    return re.sub(r'[\s\-_]', '', s).upper()

def match_model(text, remaining):
    norm = normalize(text)
    for model in remaining:
        if normalize(model) in norm:
            return model
        for alt in ALTERNATE_NAMES.get(model, []):
            if normalize(alt) in norm:
                return model
    return None

def get_product_links_from_category(cat_path):
    links, seen = [], set()
    pages_to_check = [BASE_URL + cat_path]
    checked = set()

    while pages_to_check:
        page_url = pages_to_check.pop(0)
        if page_url in checked:
            continue
        checked.add(page_url)

        resp = fetch(page_url)
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

        # Pagination
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if (text.isdigit() and int(text) > 1) or text.lower() in ["next", "»", ">"]:
                full = href if href.startswith("http") else BASE_URL + href
                if full not in checked and "7sensor.com" in full:
                    pages_to_check.append(full)
            if re.search(r'[?&]p=\d+|page[=/]\d+', href):
                full = href if href.startswith("http") else BASE_URL + href
                if full not in checked:
                    pages_to_check.append(full)

        time.sleep(0.5)

    log(f"    {len(checked)} page(s) checked, {len(links)} product links found")
    return links

def extract_all_images(soup):
    images = []
    for img in soup.find_all("img"):
        for attr in ["data-zoom-image", "data-original", "data-src", "src"]:
            src = img.get(attr, "")
            if src:
                if src.startswith("//"): src = "https:" + src
                elif src.startswith("/"): src = BASE_URL + src
                if "micyjz.com" in src and not any(x in src.lower() for x in ["logo", "icon", "banner", "flag", "arrow", "btn", "facebook", "twitter", "whatsapp"]):
                    clean = re.sub(r'-\d{2,4}-\d{2,4}(?=\.\w{3,4})', '', src)
                    images.append(clean)
                break
    # background-image
    for el in soup.find_all(style=re.compile(r'background-image', re.I)):
        for u in re.findall(r'url\(["\']?(.*?)["\']?\)', el.get("style", "")):
            if u.startswith("//"): u = "https:" + u
            if "micyjz.com" in u:
                images.append(re.sub(r'-\d{2,4}-\d{2,4}(?=\.\w{3,4})', '', u))
    seen = set()
    return [x for x in images if not (x in seen or seen.add(x))]

def download(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 100:
        return True
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return os.path.getsize(path) > 100
    except:
        return False

def run_rembg(inp, out):
    if os.path.exists(out) and os.path.getsize(out) > 100:
        return True
    try:
        r = subprocess.run([REMBG, "i", inp, out], capture_output=True, timeout=120)
        return r.returncode == 0 and os.path.exists(out)
    except:
        return False

# ─── MAIN ───

remaining = set(STILL_MISSING)
already_done = set()
for m in STILL_MISSING:
    out = os.path.join(OUTPUT_DIR, f"{m}_nobg.png")
    if os.path.exists(out) and os.path.getsize(out) > 100:
        already_done.add(m)
remaining -= already_done
log(f"Starting. {len(already_done)} already done, {len(remaining)} to find.\n")

found = {}

for cat_name, cat_path in CATEGORIES.items():
    if not remaining:
        log("All products found!")
        break

    log(f"\n{'='*60}")
    log(f"CATEGORY: {cat_name}  ({len(remaining)} needed)")
    log(f"{'='*60}")

    links = get_product_links_from_category(cat_path)

    for link in links:
        if not remaining:
            break

        resp = fetch(link)
        if not resp:
            time.sleep(1)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        title = ""
        h1 = soup.find("h1")
        if h1: title = h1.get_text(strip=True)

        model_field = ""
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).lower()
                if "model" in key:
                    model_field = cells[1].get_text(strip=True)
                    break

        # Also get all text content for broader matching
        page_text = soup.get_text(" ", strip=True)[:2000]

        matched = None
        url_part = link.split("/")[-1]
        for text in [title, model_field, url_part, page_text]:
            if text:
                m = match_model(text, remaining)
                if m:
                    matched = m
                    break

        if not matched:
            time.sleep(0.5)
            continue

        log(f"\n  MATCH: {matched}")
        log(f"    Title: {title[:80]}")

        images = extract_all_images(soup)
        if not images:
            log(f"    NO IMAGES on page")
            time.sleep(0.5)
            continue

        log(f"    {len(images)} image(s) found, downloading best...")
        img_url = images[0]

        safe = re.sub(r'[^\w\-.]', '_', matched)
        raw = os.path.join(TEMP_DIR, f"{safe}.jpg")
        out = os.path.join(OUTPUT_DIR, f"{matched}_nobg.png")

        if download(img_url, raw):
            if run_rembg(raw, out):
                log(f"    ✓ {matched}_nobg.png")
                found[matched] = out
                remaining.discard(matched)
            else:
                log(f"    ✗ rembg failed")
        else:
            log(f"    ✗ download failed")

        time.sleep(0.8)

# ─── REPORT ───
log(f"\n{'='*60}")
log(f"FINAL REPORT")
log(f"{'='*60}")
log(f"Already had:     {len(already_done)}")
log(f"Newly found:     {len(found)}")
log(f"Still missing:   {len(remaining)}")
log(f"Total coverage:  {len(already_done) + len(found)}/{len(STILL_MISSING)}")

if found:
    log(f"\n✓ Newly found:")
    for m in sorted(found): log(f"  {m}_nobg.png")

if remaining:
    log(f"\n✗ Still missing:")
    for m in sorted(remaining): log(f"  {m}")
