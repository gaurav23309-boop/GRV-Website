#!/usr/bin/env python3
"""
Update index.html to use new _nobg.png images for all selected products.
Replaces old img paths with products/{MODEL}_nobg.png
"""

HTML = "/Users/gaurav/Desktop/EVERYTHING/GRV/html/index.html"

# Map of model name → new image path
# These are the 79 products that now have _nobg.png files
UPDATES = {
    # Spoke type (was all sharing spoke-type.jpg)
    'DYLF-101': 'products/DYLF-101_nobg.png',
    'DYLF-102': 'products/DYLF-102_nobg.png',
    'DYLF-104': 'products/DYLF-104_nobg.png',
    'DYLF-105': 'products/DYLF-105_nobg.png',
    'DYLF-106': 'products/DYLF-106_nobg.png',
    # Shear beam
    'DYX-301':  'products/DYX-301_nobg.png',
    'DYX-302':  'products/DYX-302_nobg.png',
    'DYSBS':    'products/DYSBS_nobg.png',
    'DYX-305':  'products/DYX-305_nobg.png',
    'DYX-306A': 'products/DYX-306A_nobg.png',
    'DYBW-106': 'products/DYBW-106_nobg.png',
    'DYZX-001': 'products/DYZX-001_nobg.png',
    'DYZX-002': 'products/DYZX-002_nobg.png',
    'DYBH-102': 'products/DYBH-102_nobg.png',
    'DYBH-103': 'products/DYBH-103_nobg.png',
    'DYBH-101': 'products/DYBH-101_nobg.png',
    'DYYB-001': 'products/DYYB-001_nobg.png',
    # Tension
    'DYZL-101': 'products/DYZL-101_nobg.png',
    'DYZL-105': 'products/DYZL-105_nobg.png',
    'DYZL-106': 'products/DYZL-106_nobg.png',
    'DYZL-107': 'products/DYZL-107_nobg.png',
    # Miniature
    'DYHW-106': 'products/DYHW-106_nobg.png',
    'DYHW-108': 'products/DYHW-108_nobg.png',
    'DYHW-110': 'products/DYHW-110_nobg.png',
    'DYHW-113': 'products/DYHW-113_nobg.png',
    'DYHW-116': 'products/DYHW-116_nobg.png',
    # Capsule
    'DYMH-101': 'products/DYMH-101_nobg.png',
    'DYMH-102': 'products/DYMH-102_nobg.png',
    'DYMH-103': 'products/DYMH-103_nobg.png',
    'DYMH-104': 'products/DYMH-104_nobg.png',
    'DYMH-105': 'products/DYMH-105_nobg.png',
    'DYMH-106': 'products/DYMH-106_nobg.png',
    'DYMH-107': 'products/DYMH-107_nobg.png',
    'DYTB-001': 'products/DYTB-001_nobg.png',
    # Column type (was all sharing column-type.jpg)
    'DYZ-100':  'products/DYZ-100_nobg.png',
    'DYZ-101':  'products/DYZ-101_nobg.png',
    'DYZ-102':  'products/DYZ-102_nobg.png',
    'DYZ-103':  'products/DYZ-103_nobg.png',
    'DYZ-011':  'products/DYZ-011_nobg.png',
    'DYZ-012':  'products/DYZ-012_nobg.png',
    'DYZ-013':  'products/DYZ-013_nobg.png',
    'DYZ-014':  'products/DYZ-014_nobg.png',
    'DYZ-015':  'products/DYZ-015_nobg.png',
    'DYHX-001': 'products/DYHX-001_nobg.png',
    'DYRTN':    'products/DYRTN_nobg.png',
    # Multi-axial
    'DYDW-001': 'products/DYDW-001_nobg.png',
    'DYDW-003': 'products/DYDW-003_nobg.png',
    'DYDW-y74': 'products/DYDW-y74_nobg.png',
    # Weighing module
    'DYMK-001': 'products/DYMK-001_nobg.png',
    'DYMK-002': 'products/DYMK-002_nobg.png',
    'DYMK-003': 'products/DYMK-003_nobg.png',
    'DYMK-004': 'products/DYMK-004_nobg.png',
    'DYMK-005': 'products/DYMK-005_nobg.png',
    'DYMK-006': 'products/DYMK-006_nobg.png',
    'DYCW':     'products/DYCW_nobg.png',
    # Dynamic torque
    'DYN-200':     'products/DYN-200_nobg.png',
    'DYN-200 Pro': 'products/DYN-200 Pro_nobg.png',
    'DYN-201D':    'products/DYN-201D_nobg.png',
    'DYN-205':     'products/DYN-205_nobg.png',
    'DYN-207':     'products/DYN-207_nobg.png',
    'DYN-210':     'products/DYN-210_nobg.png',
    'DYN-502':     'products/DYN-502_nobg.png',
    # Junction
    'DY500': 'products/DY500_nobg.png',
    'DY510': 'products/DY510_nobg.png',
    'X501':  'products/X501_nobg.png',
    'DY094': 'products/DY094_nobg.png',
    # Indicators
    'DY054': 'products/DY054_nobg.png',
    'DY056': 'products/DY056_nobg.png',
    'DY800': 'products/DY800_nobg.png',
    'DY810': 'products/DY810_nobg.png',
    'DY920': 'products/DY920_nobg.png',
}

import re

with open(HTML, 'r', encoding='utf-8') as f:
    content = f.read()

changed = 0
for model, new_img in UPDATES.items():
    # Match: {name:'MODEL',...,img:'products/anything'}
    # Replace only the img value for that exact model
    pattern = r"(\{name:'" + re.escape(model) + r"',[^}]*img:')[^']+(')"
    replacement = r"\g<1>" + new_img + r"\g<2>"
    new_content, n = re.subn(pattern, replacement, content)
    if n:
        content = new_content
        changed += n
        print(f"  ✓ {model} → {new_img}")
    else:
        print(f"  ✗ NOT FOUND: {model}")

with open(HTML, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nUpdated {changed} product image references in index.html")
