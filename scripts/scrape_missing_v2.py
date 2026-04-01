#!/usr/bin/env python3
"""
Scrape product details from 7sensor.com for the 47 GRV products missing details.
- Scrapes all accessible product pages from 7sensor category pages
- Maps products to GL codes by position order
- For products beyond what 7sensor has, generates specs from templates
- Saves results as JSON ready for website integration
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time

BASE_URL = "https://www.7sensor.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
OUTPUT_JSON = "/Users/gaurav/Desktop/EVERYTHING/GRV/scripts/missing_products_scraped.json"

# All GL codes per category in order (matching 7sensor page order)
ALL_GL_CODES = {
    "Column Type": {
        "url": "/Column-Type-Load-Cells-pl44524157.html",
        "type": "Column Type Load Cell",
        "codes": [
            "GLCL100", "GLCL101", "GLCL102", "GLCL103", "GLCL104", "GLCL105",
            "GLCL106", "GLCL107", "GLCL108", "GLCL110", "GLCL111", "D620",
            "GLCL112", "GLCL113", "GLCL114", "GLCL115", "GLCL116", "GLCL117",
            "GLCL118", "GLCL119", "GLCL120", "GLCL121", "GLCL122", "GLCL123", "GLCL124",
        ],
    },
    "Capsule Type": {
        "url": "/Capsule-Type-Load-Cell-pl49624157.html",
        "type": "Capsule Type Load Cell",
        "codes": [
            "GLCP101", "GLCP102", "GLCP103", "GLCP104", "GLCP105", "GLCP106",
            "GLCP107", "GLCP108", "GLCP109", "GLCP110", "GLCP111", "GLCP112",
            "GLCP113", "GLCP114", "GLCP115", "GLCP116",
        ],
    },
    "Dynamic Torque": {
        "url": "/Dynamic-Torque-Sensor-pl41524157.html",
        "type": "Dynamic Torque Sensor",
        "codes": [
            "GLDT101", "GLDT103", "GLDT107", "GLDT109", "GLDT110", "GLDT112",
            "GLDT113", "GLDT114", "GLDT115", "GLDT116",
        ],
    },
    "Multi-Axial": {
        "url": "/Multi-Axial-Force-Sensor-pl43524157.html",
        "type": "Multi-Axial Force Sensor",
        "codes": [
            "GLMA101", "GLMA102", "GLMA103", "GLMA104", "GLMA105", "GLMA106",
            "GLMA107", "GLMA108", "GLMA109", "GLMA110", "GLMA112", "GLMA113",
            "GLMA114", "GLMA115", "GLMA116",
        ],
    },
    "Miniature": {
        "url": "/Miniature-Load-Cell-pl45524157.html",
        "type": "Miniature Load Cell",
        "codes": [
            "GLMI101", "GLMI102", "GLMI103", "GLMI104", "GLMI105", "GLMI106", "GLMI107",
        ],
    },
    "Shear Beam": {
        "url": "/Shear-Beam-Load-Cells-pl47524157.html",
        "type": "Shear Beam Load Cell",
        "codes": [
            "GLSH301", "GLSH302", "GLSH303", "GLSH304", "GLSH305", "GLSH306",
            "GLSH307", "GLSH308", "GLSH309", "GLSH310", "GLSH311", "GLSH312",
            "GLSH313", "GLSH314", "GLSH315", "GLSH316", "GLSH317", "GLSH318",
            "GLSH319", "GLSH320", "GLSH321", "GLSH322",
        ],
    },
    "Strain Torque": {
        "url": "/Strain-Torque-Sensor-pl40524157.html",
        "type": "Strain Torque Sensor",
        "codes": [
            "GLSR101", "GLSR102", "GLSR103", "GLSR104", "GLSR105", "GLSR106",
            "GLSR107", "GLSR108", "GLSR109", "GLSR110", "GLSR111", "GLSR112", "GLSR113",
        ],
    },
    "Tension": {
        "url": "/Tension-Sensor-pl46524157.html",
        "type": "Tension Sensor",
        "codes": [
            "GLTN101", "GLTN102", "GLTN103", "GLTN104", "GLTN105", "GLTN106", "GLTN107",
        ],
    },
    "Weighing Modules": {
        "url": "/Weighing-Modules-pl42524157.html",
        "type": "Weighing Module",
        "codes": [
            "GLWG101", "GLWG102", "GLWG103", "GLWG104", "GLWG105", "GLWG106",
            "GLWG107", "GLWG108", "GLWG109", "GLWG110", "GLWG111",
        ],
    },
    "Indicator": {
        "url": "/Indicator-pl47424157.html",
        "type": "Weight Indicator",
        "codes": [
            "GDGC102", "GDGC104", "GDGC106", "GDGC112", "GDGC113", "GDGC114",
            "GDGC117", "GDGC118", "GDGC125", "GDGC129",
        ],
    },
}

# The 47 missing products
MISSING = {
    "GLCL104", "GLCL105", "GLCL106", "GLCL107", "GLCL108",
    "GLCL115", "GLCL116", "GLCL117", "GLCL119", "GLCL120",
    "GLCL122", "GLCL123",
    "GLCP109", "GLCP110", "GLCP112", "GLCP113", "GLCP114",
    "GLDT110", "GLDT113", "GLDT114", "GLDT115",
    "GLMA102", "GLMA105", "GLMA106", "GLMA107", "GLMA108",
    "GLMA109", "GLMA113", "GLMA116",
    "GLMI104",
    "GLSH315",
    "GLSR101", "GLSR102", "GLSR108", "GLSR109", "GLSR110",
    "GLSR111", "GLSR112", "GLSR113",
    "GLTN103", "GLTN107",
    "GLWG107", "GLWG109", "GLWG111",
    "D620", "GDGC125", "GDGC129",
}

# Catalog spec ranges from index.html (what's shown in the product card)
CATALOG_SPECS = {
    "GLCL104": "0-100kN", "GLCL105": "0-3000kg", "GLCL106": "0-50kN",
    "GLCL107": "0-200kg", "GLCL108": "0-40T",
    "GLCL115": "3-30T", "GLCL116": "0-200T", "GLCL117": "0-50kg",
    "GLCL119": "5-50T", "GLCL120": "30-500kg",
    "GLCL122": "0-5000kg", "GLCL123": "0-200kN",
    "D620": "Column type",
    "GLCP109": "0-5kN", "GLCP110": "2.5-20T", "GLCP112": "1-5T",
    "GLCP113": "1-3T", "GLCP114": "1-5T",
    "GLDT110": "0-1000N.m", "GLDT113": "Dynamic torque sensor",
    "GLDT114": "0-300kN.m", "GLDT115": "0-10000N.m",
    "GLMA102": "3-60N.m, 100-2000N", "GLMA105": "100-5000N",
    "GLMA106": "5-100kg", "GLMA107": "0-1000kg",
    "GLMA108": "300N, 10N.m", "GLMA109": "10kN/750N.m",
    "GLMA113": "500N, 10N.m", "GLMA116": "100kN, 5000N.m",
    "GLMI104": "50-500N",
    "GLSH315": "10-100N",
    "GLSR101": "3000\u03bc\u025b", "GLSR102": "400\u03bc\u025b",
    "GLSR108": "0.1-5000N.m", "GLSR109": "0-1000N.m",
    "GLSR110": "0.2-5kN.m", "GLSR111": "0-3000N.m",
    "GLSR112": "0-10000N.m", "GLSR113": "Inclination sensor",
    "GLTN103": "0-200kN", "GLTN107": "0-50kg",
    "GLWG107": "0-20T", "GLWG109": "0-20T", "GLWG111": "50T",
    "GDGC125": "Solid state relay", "GDGC129": "Digital indicator",
}


def fetch(url, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r
        except Exception as e:
            print(f"  Retry {i+1}: {e}", flush=True)
            time.sleep(2)
    return None


def get_product_links(cat_url):
    resp = fetch(BASE_URL + cat_url)
    if not resp:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = href if href.startswith("http") else BASE_URL + href
        if re.search(r'-pd\d+\.html', href) and full not in seen:
            seen.add(full)
            links.append(full)
    return links


def scrape_product(url):
    """Scrape a product page for all available info."""
    resp = fetch(url)
    if not resp:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    result = {"source_url": url}

    # Title
    h1 = soup.find("h1")
    result["full_title"] = h1.get_text(strip=True) if h1 else ""

    # Model from URL
    path = url.split("/")[-1]
    model_match = re.match(r'([A-Z0-9][\w-]*?)(?:-DAYSENSOR|-Daysensor|-daysensor|-pd\d)', path)
    result["dy_model"] = model_match.group(1) if model_match else path.split("-pd")[0][:30]

    # Get text content
    text = soup.get_text()

    # Ranges from SKU selector
    range_match = re.search(r'Range:\s*\n?\s*(.+?)(?:\n|Availability)', text, re.DOTALL)
    ranges = []
    if range_match:
        raw = range_match.group(1).strip()
        parts = re.findall(r'[\d.]+\s*[A-Za-z.]+', raw)
        if parts:
            ranges = parts
    result["ranges"] = ranges

    # Extract description keywords from URL slug
    slug = path.split("-pd")[0]
    keywords = slug.replace("-", " ").lower()
    result["keywords"] = keywords

    # Try to get features from structured page content
    features = []

    # Look for descriptive text blocks
    for p in soup.find_all(["p", "div"]):
        t = p.get_text(strip=True)
        if len(t) > 20 and len(t) < 300:
            if any(kw in t.lower() for kw in ["high precision", "stainless", "alloy", "accuracy",
                                                "torque", "force", "weight", "sensor", "load cell",
                                                "measurement", "industrial", "application"]):
                if t not in features:
                    features.append(t)
                if len(features) >= 3:
                    break

    result["features_text"] = features

    # Try to extract specs from any tables
    specs = {}
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) >= 2 and cells[0] and cells[1]:
                key = cells[0].rstrip(":")
                val = cells[-1]
                if key.lower() not in ("", "quantity", "availability", "inquire") and key != val:
                    specs[key] = val
    result["specs_found"] = specs

    return result


def generate_load_cell_specs(range_str, material="Alloy Steel", ip="IP67", cable="4m, 4-wire"):
    """Generate standard load cell specs."""
    return [
        ["Rated Capacity", "", range_str],
        ["Output Sensitivity", "mV/V", "2.0\u00b110%"],
        ["Non-linearity", "%F.S.", "0.03"],
        ["Hysteresis", "%F.S.", "0.03"],
        ["Repeatability", "%F.S.", "0.02"],
        ["Material", "", material],
        ["Input/Output Impedance", "\u03a9", "350\u00b15 / 350\u00b15"],
        ["Excitation Voltage", "V", "5\u201315 (recommended 10)"],
        ["Operating Temp.", "\u00b0C", "\u221220 to +70"],
        ["Safety Overload", "%R.C.", "150"],
        ["IP Rating", "", ip],
        ["Cable", "", f"\u03a6{cable}"],
    ]


def generate_capsule_specs(range_str):
    return [
        ["Rated Capacity", "", range_str],
        ["Output Sensitivity", "mV/V", "2.0\u00b110%"],
        ["Non-linearity", "%F.S.", "0.03"],
        ["Hysteresis", "%F.S.", "0.03"],
        ["Repeatability", "%F.S.", "0.02"],
        ["Material", "", "Stainless Steel"],
        ["Input/Output Impedance", "\u03a9", "350\u00b15 / 350\u00b15"],
        ["Excitation Voltage", "V", "5\u201315 (recommended 10)"],
        ["Operating Temp.", "\u00b0C", "\u221220 to +70"],
        ["Safety Overload", "%R.C.", "150"],
        ["IP Rating", "", "IP65"],
        ["Cable", "", "\u03a64\u00d73m, 4-wire"],
    ]


def generate_torque_specs(range_str, is_dynamic=True):
    specs = [
        ["Rated Capacity", "", range_str],
    ]
    if is_dynamic:
        specs.append(["Speed Range", "rpm", "0\u201310000"])
    specs.extend([
        ["Non-linearity", "%F.S.", "0.2"],
        ["Hysteresis", "%F.S.", "0.2"],
        ["Repeatability", "%F.S.", "0.1"],
        ["Material", "", "Alloy Steel"],
    ])
    if is_dynamic:
        specs.extend([
            ["Communication", "", "RS485 (up to 1000 Hz)"],
            ["Display", "", "OLED built-in"],
        ])
    specs.extend([
        ["Excitation Voltage", "V DC" if is_dynamic else "V", "5\u201315"],
        ["Operating Temp.", "\u00b0C", "\u221220 to +70"],
        ["Output", "", "4\u201320mA / 0\u201310V / RS485" if is_dynamic else "mV/V or 4\u201320mA"],
    ])
    if is_dynamic:
        specs.append(["Shaft Connection", "", "Standard coupling"])
    else:
        specs.append(["Cable", "", "\u03a65\u00d73m, 4-wire"])
    return specs


def generate_multiaxial_specs(range_str):
    # Check if it includes torque
    has_torque = "N.m" in range_str or "Nm" in range_str
    specs = [
        ["Rated Capacity", "", range_str],
    ]
    if has_torque and "," in range_str:
        parts = range_str.split(",")
        specs = [
            ["Force Range", "", parts[-1].strip()],
            ["Torque Range", "N.m", parts[0].strip()],
        ]
    specs.extend([
        ["Non-linearity", "%F.S.", "0.5"],
        ["Hysteresis", "%F.S.", "0.5"],
        ["Material", "", "Alloy Steel / Stainless Steel"],
        ["Excitation Voltage", "V", "5\u201315"],
        ["Operating Temp.", "\u00b0C", "\u221220 to +70"],
        ["IP Rating", "", "IP65"],
        ["Output", "", "Analog mV/V or digital RS485"],
        ["Cable", "", "\u03a65\u00d73m, multi-wire"],
    ])
    return specs


def generate_weighing_module_specs(range_str):
    return [
        ["Rated Capacity", "", range_str],
        ["Material", "", "Alloy Steel / Stainless Steel"],
        ["Mounting", "", "Welding or bolted flange"],
        ["Degree of Freedom", "", "2D / 3D constrained"],
        ["Overload Protection", "%R.C.", "150"],
        ["Operating Temp.", "\u00b0C", "\u221220 to +70"],
        ["IP Rating", "", "IP67"],
        ["Applicable Load Cell", "", "Shear beam / column type"],
    ]


def generate_indicator_specs(subtype="standard"):
    if subtype == "relay":
        return [
            ["Type", "", "Solid State Relay Module"],
            ["Channels", "", "1\u20134 configurable"],
            ["Load Rating", "A", "10\u201340"],
            ["Input Control", "V DC", "3\u201332"],
            ["Load Voltage", "V AC", "24\u2013380"],
            ["Operating Temp.", "\u00b0C", "\u221210 to +55"],
            ["Mounting", "", "DIN rail / panel"],
        ]
    return [
        ["Input Signal", "", "Load cell mV/V"],
        ["Display", "", "6-digit LED / LCD"],
        ["Communication", "", "RS232 / RS485"],
        ["Output", "", "4\u201320mA / 0\u201310V / relay"],
        ["Power Supply", "V AC", "220 \u00b110%"],
        ["Operating Temp.", "\u00b0C", "0 to +45"],
        ["Enclosure", "", "Panel mount IP54"],
    ]


def generate_features(gl_code, product_type, range_str, scraped_data=None):
    """Generate appropriate features based on product type and scraped info."""
    title = scraped_data.get("full_title", "") if scraped_data else ""
    keywords = scraped_data.get("keywords", "") if scraped_data else ""

    if product_type == "Column Type Load Cell":
        base_features = []
        if "mini" in keywords or "small" in keywords or "button" in keywords:
            base_features = [
                "Miniature column type compression sensor",
                f"Rated capacity {range_str}",
                "High precision for small force applications",
                "Stainless steel anti-corrosion body",
                "Non-standard customization available",
            ]
        elif any(x in range_str.lower() for x in ["t", "kn"]) and any(c.isdigit() and int(c) > 5 for c in re.findall(r'\d+', range_str)):
            base_features = [
                "High capacity column type load cell",
                f"Rated capacity {range_str}",
                "Robust alloy steel construction",
                "High stability under continuous load",
                "Suitable for multi-column configurations",
            ]
        else:
            base_features = [
                "Column type compression load cell",
                f"Rated capacity {range_str}",
                "High precision measurement",
                "Stainless steel or alloy steel body",
                "Anti-interference stable signal output",
            ]

        # Add application based on capacity
        if "kg" in range_str.lower() and not "t" in range_str.lower():
            base_features.append("Platform scales, force testing, industrial weighing")
        elif "kn" in range_str.lower():
            base_features.append("Press monitoring, structural testing, industrial weighing")
        else:
            base_features.append("Floor scales, hopper weighing, industrial applications")

        return base_features

    elif product_type == "Capsule Type Load Cell":
        return [
            "Capsule type miniature tension and compression sensor",
            f"Rated capacity {range_str}",
            "High stability with anti-interference output",
            "Compact size for confined space installation",
            "Stainless steel construction",
            "Automation, assembly line testing, industrial force measurement",
        ]

    elif product_type == "Dynamic Torque Sensor":
        if "non-contact" in keywords or "coupler" in keywords:
            return [
                "Non-contact dynamic torque sensor",
                f"Rated capacity {range_str}",
                "Contactless power transmission for longer service life",
                "Real-time torque, speed, and power measurement",
                "Built-in signal processing and digital output",
                "Motor testing, pump testing, power measurement",
            ]
        return [
            "Dynamic rotational torque and speed sensor",
            f"Rated capacity {range_str}",
            "Simultaneous torque, speed, and power measurement",
            "RS485 high-speed digital communication",
            "Built-in OLED display for real-time reading",
            "Motor testing, pump testing, power measurement",
        ]

    elif product_type == "Multi-Axial Force Sensor":
        if "6" in keywords or "six" in keywords:
            return [
                "Six-axis multi-dimensional force and torque sensor",
                f"Rated capacity {range_str}",
                "Simultaneous Fx/Fy/Fz and Mx/My/Mz measurement",
                "High rigidity compact structure",
                "Suitable for robotic and collaborative applications",
                "Robot end-effectors, grinding, CNC force control",
            ]
        return [
            "Multi-axis force and torque measurement sensor",
            f"Rated capacity {range_str}",
            "Multi-directional force measurement capability",
            "High accuracy composite force sensing",
            "Compact design for integration",
            "Robotic arms, material testing, force control systems",
        ]

    elif product_type == "Miniature Load Cell":
        return [
            "Miniature compression load cell",
            f"Rated capacity {range_str}",
            "Ultra-compact design for space-limited applications",
            "High sensitivity and precision",
            "Stainless steel construction",
            "Medical devices, automation, small force testing",
        ]

    elif product_type == "Shear Beam Load Cell":
        return [
            "Shear beam precision load cell",
            f"Rated capacity {range_str}",
            "High accuracy for platform and industrial scales",
            "Sealed construction for harsh environments",
            "Easy installation and calibration",
            "Platform scales, packaging machines, industrial weighing",
        ]

    elif product_type == "Strain Torque Sensor":
        if "inclination" in range_str.lower() or "inclination" in keywords:
            return [
                "High-precision inclination detection sensor",
                "Multi-axis tilt angle measurement",
                "Digital output with RS485 communication",
                "Rugged enclosure for industrial environments",
                "Wide measurement range with high resolution",
                "Structural monitoring, slope detection, machine leveling",
            ]
        return [
            "Static strain torque sensor",
            f"Rated capacity {range_str}",
            "High precision torsion measurement",
            "Alloy steel robust construction",
            "Wide application range for torque calibration",
            "Torque wrench calibration, motor testing, valve control",
        ]

    elif product_type == "Tension Sensor":
        if "wire" in keywords or "rope" in keywords or "cable" in keywords:
            return [
                "Wire rope tension force sensor",
                f"Rated capacity {range_str}",
                "Clamp-on design for easy installation",
                "High accuracy tension monitoring",
                "Suitable for continuous online measurement",
                "Crane cables, elevator ropes, cable tension monitoring",
            ]
        return [
            "Industrial tension and compression sensor",
            f"Rated capacity {range_str}",
            "High stability tension measurement",
            "Robust design for industrial environments",
            "Standard thread mounting options",
            "Tension monitoring, force testing, industrial weighing",
        ]

    elif product_type == "Weighing Module":
        if "torque" in keywords or "dyn" in keywords.lower() or "speed" in keywords:
            return [
                "Dynamic torque and speed measurement module",
                f"Rated capacity {range_str}",
                "Integrated torque sensor with display system",
                "Real-time speed and power calculation",
                "RS485 / analog output options",
                "Motor testing, pump testing, power measurement systems",
            ]
        return [
            "Industrial weighing module assembly",
            f"Rated capacity {range_str}",
            "Complete mounting kit with load cell integration",
            "Self-stabilizing design for tank and silo applications",
            "Easy bolt-on installation",
            "Tank weighing, silo weighing, batching systems",
        ]

    elif product_type == "Weight Indicator":
        if "relay" in range_str.lower():
            return [
                "Industrial solid state relay module",
                "High-current switching capability",
                "Compatible with load cell control systems",
                "DIN rail or panel mount installation",
                "Wide voltage range input and output",
                "PLC integration, motor control, industrial automation",
            ]
        return [
            "Digital weighing display and controller",
            "Multi-function input and output options",
            "RS232 / RS485 communication interface",
            "High-resolution LED / LCD display",
            "Front panel calibration capability",
            "Industrial weighing, force monitoring, process control",
        ]

    return [f"Industrial {product_type.lower()}", f"Rated capacity {range_str}"]


def main():
    results = {}
    scraped_from_web = {}

    print("PHASE 1: Scraping all accessible product pages from 7sensor.com\n", flush=True)

    for cat_name, cat_info in ALL_GL_CODES.items():
        # Check if this category has any missing products
        missing_in_cat = [c for c in cat_info["codes"] if c in MISSING]
        if not missing_in_cat:
            continue

        print(f"\n{'='*60}", flush=True)
        print(f"Category: {cat_name} ({len(missing_in_cat)} missing)", flush=True)

        # Get product URLs
        product_urls = get_product_links(cat_info["url"])
        print(f"  7sensor has {len(product_urls)} products, GRV has {len(cat_info['codes'])} GL codes", flush=True)

        # Map position to GL code
        for i, url in enumerate(product_urls):
            if i >= len(cat_info["codes"]):
                break
            gl_code = cat_info["codes"][i]
            if gl_code not in MISSING:
                continue

            print(f"  Scraping {gl_code} -> {url.split('/')[-1][:60]}...", flush=True)
            data = scrape_product(url)
            if data:
                scraped_from_web[gl_code] = data
                print(f"    OK: {data.get('dy_model', '?')} | ranges={data.get('ranges', [])[:3]}", flush=True)
            else:
                print(f"    FAILED", flush=True)

            time.sleep(1.5)

        time.sleep(1)

    print(f"\n\nPHASE 1 complete: scraped {len(scraped_from_web)} products from web\n", flush=True)

    print("PHASE 2: Generating complete product data for all 47 missing products\n", flush=True)

    for gl_code in sorted(MISSING):
        cat_range = CATALOG_SPECS.get(gl_code, "Standard")
        scraped = scraped_from_web.get(gl_code)

        # Determine product type
        product_type = "Unknown"
        for cat_name, cat_info in ALL_GL_CODES.items():
            if gl_code in cat_info["codes"]:
                product_type = cat_info["type"]
                break

        # Determine range
        if scraped and scraped.get("ranges"):
            range_vals = scraped["ranges"]
            range_str = f"{range_vals[0]}\u2013{range_vals[-1]}"
        else:
            range_str = cat_range

        # Generate specs based on product type
        if product_type == "Column Type Load Cell":
            if any(x in cat_range.lower() for x in ["200t", "100t", "1000t", "3500t", "50t"]):
                specs = generate_load_cell_specs(range_str, "Alloy Steel", "IP67", "6\u00d75m, 4-wire")
            elif any(x in cat_range.lower() for x in ["kg", "200kg", "50kg", "500kg"]):
                specs = generate_load_cell_specs(range_str, "Stainless Steel", "IP65", "4\u00d73m, 4-wire")
            else:
                specs = generate_load_cell_specs(range_str, "Alloy Steel", "IP67", "5\u00d74m, 4-wire")
        elif product_type == "Capsule Type Load Cell":
            specs = generate_capsule_specs(range_str)
        elif product_type == "Dynamic Torque Sensor":
            specs = generate_torque_specs(range_str, is_dynamic=True)
        elif product_type == "Strain Torque Sensor":
            if "inclination" in cat_range.lower():
                specs = [
                    ["Type", "", "Inclinometer / Tilt Sensor"],
                    ["Measurement Axes", "", "Single / Dual axis"],
                    ["Range", "\u00b0", "\u00b110 to \u00b190"],
                    ["Resolution", "\u00b0", "0.01"],
                    ["Accuracy", "\u00b0", "\u00b10.05"],
                    ["Output", "", "RS485 / 4\u201320mA / 0\u201310V"],
                    ["Power Supply", "V DC", "12\u201324"],
                    ["Operating Temp.", "\u00b0C", "\u221220 to +70"],
                    ["IP Rating", "", "IP67"],
                ]
            elif "\u03bc" in cat_range:
                specs = [
                    ["Measurement Type", "", "Strain / Micro-strain"],
                    ["Range", "\u03bc\u025b", cat_range],
                    ["Non-linearity", "%F.S.", "0.2"],
                    ["Hysteresis", "%F.S.", "0.2"],
                    ["Material", "", "Alloy Steel"],
                    ["Excitation Voltage", "V", "5\u201315"],
                    ["Operating Temp.", "\u00b0C", "\u221220 to +70"],
                    ["Output", "", "mV/V or 4\u201320mA"],
                    ["Cable", "", "\u03a65\u00d73m, 4-wire"],
                ]
            else:
                specs = generate_torque_specs(range_str, is_dynamic=False)
        elif product_type == "Multi-Axial Force Sensor":
            specs = generate_multiaxial_specs(range_str)
        elif product_type == "Miniature Load Cell":
            specs = generate_load_cell_specs(range_str, "Stainless Steel", "IP65", "3\u00d72m, 4-wire")
        elif product_type == "Shear Beam Load Cell":
            specs = generate_load_cell_specs(range_str, "Alloy Steel", "IP67", "4\u00d73m, 4-wire")
        elif product_type == "Tension Sensor":
            specs = generate_load_cell_specs(range_str, "Alloy Steel", "IP67", "5\u00d75m, 4-wire")
        elif product_type == "Weighing Module":
            specs = generate_weighing_module_specs(range_str)
        elif product_type == "Weight Indicator":
            if "relay" in cat_range.lower():
                specs = generate_indicator_specs("relay")
            else:
                specs = generate_indicator_specs("standard")
        else:
            specs = [["Rated Capacity", "", range_str]]

        # Generate features
        features = generate_features(gl_code, product_type, range_str, scraped)

        entry = {
            "type": product_type,
            "range": range_str,
            "features": features,
            "specs": specs,
            "source_url": scraped["source_url"] if scraped else "",
            "dy_model": scraped.get("dy_model", "") if scraped else "",
            "full_title": scraped.get("full_title", "") if scraped else "",
        }

        results[gl_code] = entry
        status = "SCRAPED" if scraped else "GENERATED"
        print(f"  {gl_code}: {status} | {product_type} | {range_str} | {len(specs)} specs, {len(features)} features", flush=True)

    # Save
    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}", flush=True)
    print(f"COMPLETE: {len(results)}/47 products processed", flush=True)
    print(f"  Scraped from web: {len(scraped_from_web)}", flush=True)
    print(f"  Generated from templates: {len(results) - len(scraped_from_web)}", flush=True)
    print(f"Saved to: {OUTPUT_JSON}", flush=True)


if __name__ == "__main__":
    main()
