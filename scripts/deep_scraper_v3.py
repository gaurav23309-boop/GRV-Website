#!/usr/bin/env python3
"""
Deep scraper v3 — smarter matching with known naming corrections.
Collects ALL product URLs first, then matches & downloads.
Does NOT update website — for review only.
"""

import requests
from bs4 import BeautifulSoup
import os, re, time, subprocess

BASE_URL = "https://www.7sensor.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

OUTPUT_DIR = "/Users/gaurav/Desktop/EVERYTHING/GRV/html/products"
REMBG = "/opt/homebrew/bin/rembg"
TEMP_DIR = "/tmp/grv_scraper_v3"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

CATEGORIES = {
    "C3-C6 Load Cell":          "/C3-C6-Load-Cell-pl49161686.html",
    "S Type":                    "/S-Type-Load-Cells-pl40624157.html",
    "Capsule Type":              "/Capsule-Type-Load-Cell-pl49624157.html",
    "Spoke Type":                "/Spoke-Type-Load-Cells-pl48524157.html",
    "Shear Beam":                "/Shear-Beam-Load-Cells-pl47524157.html",
    "Tension Sensor":            "/Tension-Sensor-pl46524157.html",
    "Miniature":                 "/Miniature-Load-Cell-pl45524157.html",
    "Column Type":               "/Column-Type-Load-Cells-pl44524157.html",
    "Multi-Axial":               "/Multi-Axial-Force-Sensor-pl43524157.html",
    "Weighing Modules":          "/Weighing-Modules-pl42524157.html",
    "Dynamic Torque":            "/Dynamic-Torque-Sensor-pl41524157.html",
    "Strain Torque":             "/Strain-Torque-Sensor-pl40524157.html",
    "Dynamometer":               "/Dynamometer-pl49524157.html",
    "Motor Test Bench":          "/Motor-Test-Bench-pl48424157.html",
    "Indicator":                 "/Indicator-pl47424157.html",
    "Junction Box":              "/Junction-Box-pl46424157.html",
    "Transmitters":              "/Load-Cell-Transmitters-pl45424157.html",
}

# GRV model → alternate search patterns in URLs/titles
# Key insight: some GRV names differ from 7sensor names
SEARCH_MAP = {
    # Shear beam extras
    "DYWL-001": ["DYWL-001", "DYWL001"],
    # Tension
    "DYZL-104": ["DYZL-104", "DYZL104"],
    "DYZL-108": ["DYZL-108", "DYZL108"],
    # Miniature
    "DYHW-112": ["DYHW-112", "DYHW112"],
    # Capsule extras
    "DYMH-108D": ["DYMH-108D", "DYMH108D"],
    "DYMH-109": ["DYMH-109", "DYMH109"],
    "DYPB-001": ["DYPB-001", "DYPB001"],
    "DYPB-002": ["DYPB-002", "DYPB002"],
    "DYPB-003": ["DYPB-003", "DYPB003"],
    # Column extras
    "DYZ-104": ["DYZ-104", "DYZ104"],
    "DYZ-105": ["DYZ-105", "DYZ105"],
    "DYZ-106": ["DYZ-106", "DYZ106"],
    "DYZ-107": ["DYZ-107", "DYZ107"],
    "DYZ-108": ["DYZ-108", "DYZ108"],
    "DYZ-109": ["DYZ-109", "DYZ109"],
    "D620": ["D620", "D-620"],
    "DYZ-016": ["DYZ-016", "DYZ016"],
    "DYZ-018": ["DYZ-018", "DYZ018"],
    "DYZ-13E": ["DYZ-13E", "DYZ13E"],
    "DYHX-002": ["DYHX-002", "DYHX002"],
    "DYHX-002M": ["DYHX-002M", "DYHX002M"],
    "DYHX-003M": ["DYHX-003M", "DYHX003M"],
    "DYHX-004": ["DYHX-004", "DYHX004"],
    # Multi-axial — KEY: website uses DYDW-25 not DYDW-y25
    "DYDW-002": ["DYDW-002", "DYDW002"],
    "DYDW-005": ["DYDW-005", "DYDW005"],
    "DYDW-006": ["DYDW-006", "DYDW006"],
    "DYDW-007": ["DYDW-007", "DYDW007"],
    "DYDW-008": ["DYDW-008", "DYDW008"],
    "DYDW-009": ["DYDW-009", "DYDW009"],
    "DYDW-y25": ["DYDW-y25", "DYDW-25", "DYDW25"],
    "DYDW-y45": ["DYDW-y45", "DYDW-45", "DYDW45"],
    "DYDW-y80": ["DYDW-y80", "DYDW-80", "DYDW80"],
    "DYDW-y82": ["DYDW-y82", "DYDW-82", "DYDW82"],
    "DYDW-y125": ["DYDW-y125", "DYDW-125", "DYDW125"],
    "DYDW-y200": ["DYDW-y200", "DYDW-200", "DYDW200"],
    # Weighing
    "DYFW": ["DYFW"],
    "DYFWC": ["DYFWC"],
    "DYMK-008": ["DYMK-008", "DYMK008"],
    # Strain torque — KEY: website uses DYJN not DXJN
    "DYZY-001": ["DYZY-001", "DYZY001"],
    "DYDC-001": ["DYDC-001", "DYDC001"],
    "DXJN-101": ["DXJN-101", "DYJN-101", "DYJN101"],
    "DXJN-102": ["DXJN-102", "DYJN-102", "DYJN102"],
    "DXJN-103": ["DXJN-103", "DYJN-103", "DYJN103"],
    "DXJN-104": ["DXJN-104", "DYJN-104", "DYJN104"],
    "DXJN-105": ["DXJN-105", "DYJN-105", "DYJN105"],
    "DXJN-106": ["DXJN-106", "DYJN-106", "DYJN106"],
    "DXJN-107": ["DXJN-107", "DYJN-107", "DYJN107"],
    "DXJN-108": ["DXJN-108", "DYJN-108", "DYJN108"],
    "DXJN-110": ["DXJN-110", "DYJN-110", "DYJN110"],
    "DXJN-111": ["DXJN-111", "DYJN-111", "DYJN111"],
    "Inclination Detection System": ["Inclination", "inclinometer"],
    # Dynamic torque
    "DYN-202": ["DYN-202", "DYN202"],
    "DYN-203": ["DYN-203", "DYN203"],
    "DYN-206": ["DYN-206", "DYN206"],
    "DYN-208": ["DYN-208", "DYN208"],
    "DYN-209": ["DYN-209", "DYN209"],
    "DYN-210MU": ["DYN-210MU", "DYN210MU"],
    "DYN-212": ["DYN-212", "DYN212"],
    "DYN-TA8": ["DYN-TA8", "DYNTA8"],
    # Junction & transmitters
    "DYTX-101": ["DYTX-101", "DYTX101"],
    "BSQ-001": ["BSQ-001", "BSQ001"],
    "Four-Channel Weighing Transmitter": ["four-channel", "4-channel", "FCWT"],
    "D530": ["D530", "D-530"],
    "DYFV12": ["DYFV12", "DY-FV12"],
    "X503": ["X503"],
    "DR304": ["DR304", "DR-304"],
    "X508A": ["X508A"],
    "X508B": ["X508B"],
    # Indicators
    "D740 Touch Screen": ["D740"],
    "DY054W": ["DY054W", "D054W"],
    "DY054N": ["DY054N", "D054N"],
    "DY055": ["DY055", "D055"],
    "XS05": ["XS05"],
    "DY220": ["DY220"],
    "DY220B": ["DY220B"],
    "DY300": ["DY300"],
    "DY300A": ["DY300A"],
    "DYN-303": ["DYN-303", "DYN303"],
    "DY6001": ["DY6001"],
    "DY300 MFC": ["DY300-MFC", "DY300MFC", "multi-function"],
    "DY310": ["DY310"],
    "DY320": ["DY320"],
    "DY330": ["DY330"],
    "DYHB": ["DYHB"],
    "DYCHB": ["DYCHB"],
    "LN96A": ["LN96A"],
    "SSR21": ["SSR21"],
    "XSB2": ["XSB2"],
    "CH6": ["CH6"],
    "700WC": ["700WC", "700-WC"],
    "DY2025": ["DY2025"],
    "DY3190": ["DY3190"],
    "R305": ["R305"],
}

def log(msg):
    print(msg, flush=True)

def fetch(url, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r
        except:
            if i < retries - 1: time.sleep(2)
    return None

def normalize(s):
    return re.sub(r'[\s\-_]', '', s).upper()

def match_url(url_slug, remaining):
    """Match a URL slug against remaining models using SEARCH_MAP."""
    norm = normalize(url_slug)
    for model in list(remaining):
        patterns = SEARCH_MAP.get(model, [model])
        for p in patterns:
            if normalize(p) in norm:
                return model
    return None

def extract_best_image(soup):
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
            for chunk in r.iter_content(8192): f.write(chunk)
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

# ─── PHASE 1: Collect ALL product URLs from ALL categories ───

log("PHASE 1: Collecting all product URLs from 7sensor.com...\n")
all_product_urls = []
seen_urls = set()

for cat_name, cat_path in CATEGORIES.items():
    pages_to_check = [BASE_URL + cat_path]
    checked = set()

    while pages_to_check:
        page_url = pages_to_check.pop(0)
        if page_url in checked: continue
        checked.add(page_url)

        resp = fetch(page_url)
        if not resp: continue
        soup = BeautifulSoup(resp.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            full = href if href.startswith("http") else BASE_URL + href
            if re.search(r'-pd\d+\.html', href) and full not in seen_urls:
                seen_urls.add(full)
                all_product_urls.append((full, cat_name))
            # Pagination
            text = a.get_text(strip=True)
            if (text.isdigit() and int(text) > 1) or text.lower() in ["next", "»", ">"]:
                if "7sensor.com" in full and full not in checked:
                    pages_to_check.append(full)
            if re.search(r'[?&]p=\d+|page[=/]\d+', href):
                full2 = href if href.startswith("http") else BASE_URL + href
                if full2 not in checked: pages_to_check.append(full2)

        time.sleep(0.3)

    log(f"  {cat_name}: {len(checked)} page(s)")

log(f"\nTotal product URLs collected: {len(all_product_urls)}")

# ─── PHASE 2: Pre-filter URLs by slug matching ───

remaining = set(SEARCH_MAP.keys())
# Remove already-done
already_done = set()
for m in list(remaining):
    if os.path.exists(os.path.join(OUTPUT_DIR, f"{m}_nobg.png")):
        if os.path.getsize(os.path.join(OUTPUT_DIR, f"{m}_nobg.png")) > 100:
            already_done.add(m)
remaining -= already_done
log(f"\nAlready done: {len(already_done)}, Still need: {len(remaining)}")

log("\nPHASE 2: Matching URLs to missing products...\n")
matched_urls = []  # (url, matched_model, category)

for url, cat in all_product_urls:
    slug = url.split("/")[-1]
    m = match_url(slug, remaining)
    if m:
        matched_urls.append((url, m, cat))
        log(f"  URL MATCH: {m:30s} ← {slug[:60]}")

log(f"\nMatched {len(matched_urls)} URLs to products")

# ─── PHASE 3: Download & process matched products ───

log("\nPHASE 3: Downloading images and removing backgrounds...\n")
found = {}
failed = []

for url, model, cat in matched_urls:
    if model not in remaining:
        continue  # Already found by an earlier match

    resp = fetch(url)
    if not resp:
        time.sleep(1)
        continue

    soup = BeautifulSoup(resp.text, "html.parser")
    images = extract_best_image(soup)

    if not images:
        log(f"  {model}: NO IMAGES on page")
        failed.append(model)
        time.sleep(0.5)
        continue

    img_url = images[0]
    safe = re.sub(r'[^\w\-.]', '_', model)
    raw = os.path.join(TEMP_DIR, f"{safe}.jpg")
    out = os.path.join(OUTPUT_DIR, f"{model}_nobg.png")

    if download(img_url, raw):
        if run_rembg(raw, out):
            log(f"  ✓ {model}_nobg.png")
            found[model] = out
            remaining.discard(model)
        else:
            log(f"  ✗ rembg fail: {model}")
            failed.append(model)
    else:
        log(f"  ✗ download fail: {model}")
        failed.append(model)

    time.sleep(0.8)

# ─── PHASE 4: Search page text for remaining products ───

if remaining:
    log(f"\nPHASE 4: Deep page-text search for {len(remaining)} remaining...\n")
    # Visit ALL unvisited product pages and search page text
    visited = set(url for url, _, _ in matched_urls)
    for url, cat in all_product_urls:
        if url in visited or not remaining:
            continue
        visited.add(url)

        resp = fetch(url)
        if not resp:
            time.sleep(0.5)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        # Check h1 title
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else ""
        # Check model field in specs
        model_field = ""
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).lower()
                if "model" in key:
                    model_field = cells[1].get_text(strip=True)
                    break

        matched = None
        for text in [title, model_field]:
            if text:
                m = match_url(text, remaining)
                if m:
                    matched = m
                    break

        if not matched:
            time.sleep(0.3)
            continue

        log(f"  TEXT MATCH: {matched} ← '{title[:50]}'")

        images = extract_best_image(soup)
        if not images:
            log(f"    NO IMAGES")
            time.sleep(0.3)
            continue

        safe = re.sub(r'[^\w\-.]', '_', matched)
        raw = os.path.join(TEMP_DIR, f"{safe}.jpg")
        out = os.path.join(OUTPUT_DIR, f"{matched}_nobg.png")

        if download(images[0], raw):
            if run_rembg(raw, out):
                log(f"    ✓ {matched}_nobg.png")
                found[matched] = out
                remaining.discard(matched)
            else:
                log(f"    ✗ rembg fail")
        time.sleep(0.5)

# ─── REPORT ───
log(f"\n{'='*60}")
log(f"FINAL REPORT")
log(f"{'='*60}")
log(f"Already had:     {len(already_done)}")
log(f"Newly found:     {len(found)}")
log(f"Still missing:   {len(remaining)}")

if found:
    log(f"\n✓ Newly found ({len(found)}):")
    for m in sorted(found): log(f"  {m}_nobg.png")

if remaining:
    log(f"\n✗ Still missing ({len(remaining)}):")
    for m in sorted(remaining): log(f"  {m}")
