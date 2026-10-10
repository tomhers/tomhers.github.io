#!/usr/bin/env python3
"""
Interactive helper for adding photos to the portfolio site.

Walks through every image in a source folder, opens a preview in VS Code,
asks for category / location / date, then copies the file into
images/<category>/ using the <location-slug>--<YYYY-MM>.<ext> naming
convention that scripts/build-manifest.js expects.

Usage:
    python3 scripts/add_photos.py /path/to/new/photos
    python3 scripts/add_photos.py /path/to/new/photos --move
    python3 scripts/add_photos.py /path/to/new/photos --images-root images

Requires the VS Code 'code' command to be on your PATH. In VS Code, open
the Command Palette and run "Shell Command: Install 'code' command in PATH"
if `code --version` doesn't work in your terminal.
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VALID_CATEGORIES = {"nature", "city"}
DATE_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def prompt_category():
    while True:
        raw = input("  Category [nature/city] (s=skip, q=quit): ").strip().lower()
        if raw in VALID_CATEGORIES:
            return raw
        if raw in ("s", "skip"):
            return "skip"
        if raw in ("q", "quit"):
            return "quit"
        print("  Please enter 'nature', 'city', 's' to skip, or 'q' to quit.")


def prompt_location():
    while True:
        raw = input("  Location (e.g. 'Mount Rainier'): ").strip()
        slug = slugify(raw)
        if slug:
            return raw, slug
        print("  Location can't be empty.")


def prompt_date():
    while True:
        raw = input("  Date as YYYY-MM (leave blank to skip): ").strip()
        if raw == "":
            return ""
        if DATE_PATTERN.match(raw):
            return raw
        print("  Use the format YYYY-MM, e.g. 2026-07.")


def unique_destination(dest_dir, stem, ext):
    candidate = dest_dir / f"{stem}{ext}"
    counter = 2
    while candidate.exists():
        candidate = dest_dir / f"{stem}-{counter}{ext}"
        counter += 1
    return candidate


def show_preview(path):
    """Opens the image as a preview tab in VS Code. Uses -r to reuse the
    same window each time instead of piling up new ones. Never fatal —
    if the 'code' command isn't set up, just print how to fix that."""
    try:
        subprocess.run(["code", "-r", str(path)], check=True)
    except FileNotFoundError:
        print(
            "  (couldn't find the 'code' command — in VS Code, open the Command "
            "Palette and run \"Shell Command: Install 'code' command in PATH\")"
        )
    except subprocess.CalledProcessError as exc:
        print(f"  (couldn't open preview in VS Code: {exc})")


def main():
    parser = argparse.ArgumentParser(description="Add photos to the portfolio's images/ folders.")
    parser.add_argument("source", help="Folder of new photos to process")
    parser.add_argument(
        "--images-root",
        default=str(Path(__file__).resolve().parent.parent / "images"),
        help="Path to the site's images/ folder (default: ../images relative to this script)",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move the original file instead of copying it (default: copy, original stays put)",
    )
    args = parser.parse_args()

    source_dir = Path(args.source).expanduser().resolve()
    images_root = Path(args.images_root).expanduser().resolve()

    if not source_dir.is_dir():
        print(f"Not a directory: {source_dir}")
        sys.exit(1)

    files = sorted(
        p for p in source_dir.iterdir()
        if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS
    )

    if not files:
        print(f"No images found in {source_dir} (looked for {', '.join(sorted(VALID_EXTENSIONS))})")
        sys.exit(0)

    print(f"Found {len(files)} image(s) in {source_dir}\n")

    added, skipped = 0, 0

    for i, path in enumerate(files, start=1):
        print(f"[{i}/{len(files)}] {path.name}")
        show_preview(path)

        category = prompt_category()
        if category == "quit":
            print("\nStopping early.")
            break
        if category == "skip":
            print("  Skipped.\n")
            skipped += 1
            continue

        location, slug = prompt_location()
        date = prompt_date()

        stem = f"{slug}--{date}" if date else slug
        dest_dir = images_root / category
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = unique_destination(dest_dir, stem, path.suffix.lower())

        if args.move:
            shutil.move(str(path), str(dest_path))
        else:
            shutil.copy2(str(path), str(dest_path))

        print(f"  -> {dest_path.relative_to(images_root.parent)}  ({location})\n")
        added += 1

    print(f"Done. Added {added}, skipped {skipped}.")
    if added:
        print("Commit and push images/ — the GitHub Action will rebuild images.json automatically.")


if __name__ == "__main__":
    main()