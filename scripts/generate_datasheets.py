#!/usr/bin/env python3
"""Generate PDF datasheets for ALL products — GRV Automation. IFM-style layout.

Parses productDetails from index.html and generates one PDF per product.
"""

from fpdf import FPDF
import os
import re
import json

BASE_DIR   = os.path.expanduser("~/Desktop/EVERYTHING/GRV/html")
OUT_DIR    = os.path.join(BASE_DIR, "datasheets")
IMG_DIR    = os.path.join(BASE_DIR, "products")
INDEX_HTML = os.path.join(BASE_DIR, "index.html")
LOGO_PATH  = os.path.expanduser("~/Desktop/EVERYTHING/GRV/brochure_images/logo.png")
CE_PATH    = os.path.expanduser("~/Desktop/EVERYTHING/GRV/brochure_images/ce_mark.png")
UL_PATH    = os.path.expanduser("~/Desktop/EVERYTHING/GRV/brochure_images/ul_mark.png")
UKCA_PATH  = os.path.expanduser("~/Desktop/EVERYTHING/GRV/brochure_images/ukca_mark.png")
os.makedirs(OUT_DIR, exist_ok=True)

# Colours
TEAL    = (0, 191, 166)
NAVY    = (10, 22, 40)
TBL_HDR = (50, 60, 75)
TBL_ALT = (242, 244, 246)
BLACK   = (0, 0, 0)
LGRAY   = (190, 195, 200)
DGRAY   = (60, 65, 70)

# Contact
PHONE   = "+91 9008 300 172"
EMAIL   = "info@grvautomation.com"
WEBSITE = "www.grvautomation.com"
ADDRESS = "WeWork Latitude, Hebbal, Bengaluru - 560024, Karnataka, India"


def safe(text):
    """Convert Unicode chars to latin-1 safe equivalents."""
    if not isinstance(text, str):
        return str(text)
    rep = {
        '\u2013': '-', '\u2014': '-', '\u2022': '-',
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2265': '>=', '\u2264': '<=', '\u00b0': ' deg',
        '\u2126': 'Ohm', '\u03a9': 'Ohm', '\u00b1': '+/-', '\u2212': '-',
        '\u03a6': 'D', '\u00d8': 'D', '\u2248': '~',
        '\u00d7': 'x',   # multiplication sign
        '\u00b2': '2',   # superscript 2
        '\u00b3': '3',   # superscript 3
        '\u00b5': 'u',   # micro sign
        '\u2103': ' degC',  # degree celsius
        '\u2109': ' degF',  # degree fahrenheit
        '\u221e': 'inf',    # infinity
        '\u2260': '!=',     # not equal
        '\u00ae': '(R)',    # registered
        '\u2122': '(TM)',   # trademark
        '\u00a9': '(C)',    # copyright
    }
    for k, v in rep.items():
        text = text.replace(k, v)
    return text.encode('latin-1', errors='replace').decode('latin-1')


# ───────────────────────────── Parse productDetails from index.html ──────────
def parse_product_details():
    """Extract productDetails JS object from index.html and return as dict."""
    with open(INDEX_HTML, 'r', encoding='utf-8') as f:
        html = f.read()

    # Find the productDetails block
    match = re.search(r'const productDetails\s*=\s*\{', html)
    if not match:
        raise RuntimeError("Could not find productDetails in index.html")

    start = match.start()
    # Find matching closing brace by counting braces
    brace_count = 0
    idx = match.end() - 1  # position of the opening {
    for i in range(idx, len(html)):
        if html[i] == '{':
            brace_count += 1
        elif html[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end = i + 1
                break

    js_obj = html[idx:end]

    # Convert JS object syntax to valid JSON:
    # 1) Convert single-quoted keys/values to double-quoted
    # 2) Add quotes around unquoted keys
    # 3) Handle trailing commas

    # Replace single quotes with double quotes (carefully)
    # First, let's use a different approach: use regex to parse each product entry
    products = {}
    # Match each product entry: 'MODEL':{...}
    # We'll iterate through products using a pattern
    product_pattern = re.compile(r"'([^']+)'\s*:\s*\{", re.DOTALL)

    pos = 0
    entries = []
    for m in product_pattern.finditer(js_obj):
        model = m.group(1)
        obj_start = m.end() - 1  # the {
        # Find matching }
        bc = 0
        for i in range(obj_start, len(js_obj)):
            if js_obj[i] == '{':
                bc += 1
            elif js_obj[i] == '}':
                bc -= 1
                if bc == 0:
                    obj_end = i + 1
                    break
        obj_str = js_obj[obj_start:obj_end]
        entries.append((model, obj_str))

    for model, obj_str in entries:
        try:
            # Extract type
            type_match = re.search(r"type\s*:\s*'([^']*)'", obj_str)
            prod_type = type_match.group(1) if type_match else 'Load Cell'

            # Extract range
            range_match = re.search(r"range\s*:\s*'([^']*)'", obj_str)
            prod_range = range_match.group(1) if range_match else ''

            # Extract features array
            feat_match = re.search(r"features\s*:\s*\[([^\]]*)\]", obj_str)
            features = []
            if feat_match:
                feat_str = feat_match.group(1)
                features = re.findall(r"'([^']*)'", feat_str)

            # Extract specs array of arrays
            specs_match = re.search(r"specs\s*:\s*\[(.*)\]", obj_str, re.DOTALL)
            specs = []
            if specs_match:
                specs_str = specs_match.group(1)
                # Find each inner array [...]
                for row_match in re.finditer(r"\[([^\]]*)\]", specs_str):
                    row_str = row_match.group(1)
                    cells = re.findall(r"'([^']*)'", row_str)
                    if len(cells) == 3:
                        specs.append(cells)
                    elif len(cells) == 2:
                        specs.append([cells[0], '', cells[1]])
                    elif len(cells) == 1:
                        specs.append([cells[0], '', ''])

            products[model] = {
                'type': prod_type,
                'range': prod_range,
                'features': features,
                'specs': specs,
            }
        except Exception as e:
            print(f"  WARNING: Failed to parse {model}: {e}")

    return products


class DatasheetPDF(FPDF):
    def __init__(self, model, data):
        super().__init__()
        self.model = model
        self.data  = data
        self.set_auto_page_break(auto=False)
        self.set_margins(0, 0, 0)

    def build(self):
        self.add_page()
        d   = self.data
        PW  = 210
        PH  = 297
        MX  = 12   # left margin
        MR  = PW - 12  # right edge

        # ── Top header bar (thin navy line + model name) ──────────────────
        self.set_fill_color(*NAVY)
        self.rect(0, 0, PW, 1.5, 'F')

        # Model name (large, black)
        self.set_font('Helvetica', 'B', 22)
        self.set_text_color(*BLACK)
        self.set_xy(MX, 6)
        self.cell(130, 11, self.model)

        # GRV logo
        logo_w = 28
        if os.path.exists(LOGO_PATH):
            try:
                self.image(LOGO_PATH, PW - logo_w - 10, 4, logo_w, logo_w)
            except Exception:
                pass

        # Product type (bold, black)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*BLACK)
        self.set_xy(MX, 18)
        self.cell(0, 6, safe(d['type']))

        # Subtitle
        self.set_font('Helvetica', '', 7)
        self.set_text_color(*DGRAY)
        self.set_xy(MX, 25)
        self.cell(0, 5, 'GRV Automation  |  CE Certified  |  Custom Configurations Available on Request')

        # Separator
        self.set_draw_color(*LGRAY)
        self.set_line_width(0.35)
        self.line(MX, 31, MR, 31)

        # ── Product image (bordered box) ──────────────────────────────────
        img_x, img_y, img_w, img_h = MX, 34, 88, 52
        self.set_draw_color(*LGRAY)
        self.set_line_width(0.4)
        self.rect(img_x, img_y, img_w, img_h)
        self.set_fill_color(250, 250, 250)
        self.rect(img_x+0.4, img_y+0.4, img_w-0.8, img_h-0.8, 'F')

        img_path = None
        for ext in ['_nobg.png', '.png', '.jpg']:
            p = os.path.join(IMG_DIR, self.model + ext)
            if os.path.exists(p):
                img_path = p
                break
        if img_path:
            try:
                self.image(img_path, img_x+8, img_y+3, img_w-16, img_h-6)
            except Exception:
                pass

        # ── Features (right of image) ─────────────────────────────────────
        fx = img_x + img_w + 8
        self.set_xy(fx, img_y)
        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(*BLACK)
        self.cell(0, 5, 'Application / Features')
        self.ln(6.5)
        self.set_font('Helvetica', '', 7.5)
        self.set_text_color(*BLACK)

        features = d.get('features', [])
        for f in features:
            self.set_x(fx)
            self.set_text_color(*TEAL)
            self.cell(5, 5.2, '-')
            self.set_text_color(*BLACK)
            self.cell(MR - fx - 5, 5.2, safe(f))
            self.ln(5.5)

        # Rated range badge
        if d.get('range'):
            self.ln(3)
            self.set_x(fx)
            badge_text = safe('Rated range:  ' + d['range'])
            bw = self.get_string_width(badge_text) + 10
            by = self.get_y()
            # Don't let badge overflow past image area
            if by < img_y + img_h:
                self.set_fill_color(230, 248, 245)
                self.set_draw_color(*TEAL)
                self.set_line_width(0.5)
                self.rect(fx, by, bw, 7, 'DF')
                self.set_font('Helvetica', 'B', 7.5)
                self.set_text_color(*BLACK)
                self.set_xy(fx + 2, by)
                self.cell(bw - 4, 7, badge_text)

        # ── Certification marks (CE, UL, UKCA) ───────────────────────────
        cert_y = img_y + img_h + 5
        cert_h = 10
        x_cur  = MX

        if os.path.exists(CE_PATH):
            self.image(CE_PATH, x_cur, cert_y, 14, cert_h)
            x_cur += 16
        if os.path.exists(UL_PATH):
            self.image(UL_PATH, x_cur, cert_y, cert_h, cert_h)
            x_cur += 13
        if os.path.exists(UKCA_PATH):
            self.image(UKCA_PATH, x_cur, cert_y, 12, cert_h)

        # ── Specs table ───────────────────────────────────────────────────
        tbl_y  = cert_y + cert_h + 5
        tbl_w  = MR - MX
        col1   = tbl_w * 0.42
        col2   = tbl_w * 0.17
        col3   = tbl_w * 0.41
        row_h  = 5.4

        specs = d.get('specs', [])

        # Calculate if we need to shrink row height to fit all rows
        # Footer starts at PH - 12, notes take ~10mm, table bottom border ~3mm
        available_h = PH - 12 - 10 - 3 - tbl_y
        total_rows = len(specs)
        if total_rows > 0:
            needed_h = total_rows * row_h
            if needed_h > available_h:
                row_h = max(4.0, available_h / total_rows)

        self.set_y(tbl_y)

        data_row_idx = 0
        for row in specs:
            param = row[0] if len(row) > 0 else ''
            unit  = row[1] if len(row) > 1 else ''
            val   = row[2] if len(row) > 2 else ''

            is_hdr = (unit == '' and val == '' and param != '')

            if is_hdr:
                # Dark section header
                self.set_fill_color(*TBL_HDR)
                self.set_text_color(255, 255, 255)
                self.set_xy(MX, self.get_y())
                self.cell(tbl_w, row_h, '', fill=True)
                self.set_xy(MX + 2, self.get_y() - row_h)
                self.set_font('Helvetica', 'B', 7.5)
                self.cell(tbl_w - 4, row_h, safe(param))
                self.ln(row_h)
            else:
                # Data row — alternating background
                if data_row_idx % 2 == 0:
                    self.set_fill_color(*TBL_ALT)
                else:
                    self.set_fill_color(255, 255, 255)
                data_row_idx += 1
                self.set_draw_color(215, 218, 222)
                self.set_line_width(0.15)
                self.set_xy(MX, self.get_y())

                self.set_font('Helvetica', 'B', 7.5)
                self.set_text_color(*BLACK)
                self.cell(col1, row_h, '  ' + safe(param), border='B', fill=True)

                self.set_font('Helvetica', '', 7)
                self.set_text_color(*DGRAY)
                self.cell(col2, row_h, safe(unit) if unit else '', border='B', fill=True, align='C')

                self.set_font('Helvetica', 'B', 7.5)
                self.set_text_color(*BLACK)
                self.cell(col3, row_h, '  ' + safe(val) if val else '', border='B', fill=True)
                self.ln(row_h)

            # Safety check: don't overrun the footer
            if self.get_y() > PH - 22:
                break

        # Table bottom border
        self.set_draw_color(*LGRAY)
        self.set_line_width(0.35)
        self.line(MX, self.get_y(), MR, self.get_y())

        # Notes
        self.ln(2.5)
        self.set_x(MX)
        self.set_font('Helvetica', 'I', 6)
        self.set_text_color(*DGRAY)
        self.multi_cell(tbl_w, 4,
            '1) High temperature sensors available (max. 150 deg C).   '
            '2) High impedance option (1000 Ohm) on request.   '
            '3) Specifications subject to change without prior notice.'
        )

        # ── FOOTER ────────────────────────────────────────────────────────
        footer_y = PH - 12
        self.set_fill_color(*TEAL)
        self.rect(0, footer_y, PW, 0.8, 'F')

        self.set_fill_color(*NAVY)
        self.rect(0, footer_y + 0.8, PW, 11.2, 'F')

        self.set_font('Helvetica', 'B', 6.5)
        self.set_text_color(255, 255, 255)
        self.set_xy(MX, footer_y + 1.8)
        self.cell(PW - MX*2, 4.5, 'GRV Automation  |  ' + ADDRESS)

        self.set_font('Helvetica', '', 6.5)
        self.set_text_color(180, 220, 215)
        self.set_xy(MX, footer_y + 6)
        self.cell(PW - MX*2, 4,
            'Tel: ' + PHONE + '   |   ' + EMAIL + '   |   ' + WEBSITE +
            '   |   We reserve the right to make technical alterations without prior notice.'
        )


# ───────────────────────────── Main ──────────────────────────────────────────
if __name__ == '__main__':
    print("Parsing productDetails from index.html...")
    products = parse_product_details()
    print(f"Found {len(products)} products.\n")

    errors = []
    generated = 0

    for model, data in products.items():
        try:
            pdf = DatasheetPDF(model, data)
            pdf.build()
            # Sanitize filename (replace / and other unsafe chars)
            safe_name = model.replace('/', '-').replace('\\', '-')
            out_path = os.path.join(OUT_DIR, f"{safe_name}.pdf")
            pdf.output(out_path)
            print(f"  {safe_name}.pdf")
            generated += 1
        except Exception as e:
            errors.append((model, str(e)))
            print(f"  ERROR [{model}]: {e}")

    print(f"\nDone — {generated} datasheets generated in {OUT_DIR}")
    if errors:
        print(f"\n{len(errors)} errors:")
        for model, err in errors:
            print(f"  {model}: {err}")
