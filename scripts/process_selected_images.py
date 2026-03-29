#!/usr/bin/env python3
"""
Download selected product images, remove backgrounds, save to html/products/.
Reads grv_selections.txt (format: category|MODEL|URL)
"""
import os, sys, subprocess, urllib.request, urllib.error

SELECTIONS = "/Users/gaurav/Downloads/grv_selections.txt"
OUT_DIR    = "/Users/gaurav/Desktop/EVERYTHING/GRV/html/products"
REMBG      = "/opt/homebrew/bin/rembg"

os.makedirs(OUT_DIR, exist_ok=True)

with open(SELECTIONS) as f:
    lines = [l.strip() for l in f if l.strip()]

done, failed = [], []

for i, line in enumerate(lines, 1):
    parts = line.split("|")
    if len(parts) != 3:
        print(f"[SKIP] bad line: {line}")
        continue
    cat, model, url = parts
    out_path = os.path.join(OUT_DIR, f"{model}_nobg.png")

    if os.path.exists(out_path):
        print(f"[{i}/{len(lines)}] EXISTS  {model}")
        done.append(model)
        continue

    # Download
    tmp = f"/tmp/grv_{model}.jpg"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r, open(tmp, "wb") as f:
            f.write(r.read())
        print(f"[{i}/{len(lines)}] DOWNLOADED  {model}")
    except Exception as e:
        print(f"[{i}/{len(lines)}] DOWNLOAD FAIL  {model}: {e}")
        failed.append((model, "download", str(e)))
        continue

    # Remove background
    try:
        result = subprocess.run(
            [REMBG, "i", tmp, out_path],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0 and os.path.exists(out_path):
            print(f"[{i}/{len(lines)}] BG REMOVED  {model} → {model}_nobg.png")
            done.append(model)
        else:
            print(f"[{i}/{len(lines)}] REMBG FAIL  {model}: {result.stderr[:200]}")
            failed.append((model, "rembg", result.stderr[:200]))
    except Exception as e:
        print(f"[{i}/{len(lines)}] REMBG ERROR  {model}: {e}")
        failed.append((model, "rembg", str(e)))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

print(f"\n✓ Done: {len(done)}/{len(lines)}  |  ✗ Failed: {len(failed)}")
if failed:
    print("\nFailed products:")
    for m, stage, err in failed:
        print(f"  {m} [{stage}] {err}")
