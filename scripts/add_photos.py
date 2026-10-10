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
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VALID_CATEGORIES = {"nature", "city"}
DATE_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def find_vscode_cli():
    """Return the VS Code CLI path for the current environment.

    Some launchers start Python without the same PATH the user sees in their
    terminal, especially on Windows. Fall back to common VS Code install
    locations when `code` is not on PATH.
    """
    candidates = []

    explicit = os.environ.get("VSCODE_CLI_PATH")
    if explicit:
        candidates.append(explicit)

    path_cmd = shutil.which("code")
    if path_cmd:
        candidates.append(path_cmd)

    if sys.platform.startswith("win"):
        appdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        candidates.extend([
            appdata / "Programs" / "Microsoft VS Code" / "bin" / "code.cmd",
            appdata / "Programs" / "Microsoft VS Code" / "bin" / "code.exe",
            Path("C:/Program Files/Microsoft VS Code/bin/code.cmd"),
            Path("C:/Program Files (x86)/Microsoft VS Code/bin/code.cmd"),
        ])
    else:
        home = Path.home()
        candidates.extend([
            Path("/usr/local/bin/code"),
            Path("/usr/bin/code"),
            home / ".local" / "bin" / "code",
            Path("/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"),
        ])

    for candidate in candidates:
        path = Path(candidate)
        if path.exists() and path.is_file():
            return str(path)

    return "code"


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


def show_preview(path, previewer="default"):
    """Open the image using the best available non-blocking previewer.

    Prefer imgcat when installed because it renders in the terminal without
    stealing focus. Fall back to the OS default viewer or VS Code only when
    necessary.
    """
    if previewer in ("default", "imgcat", "chafa"):
        terminal_previewers = []

        if previewer in ("default", "imgcat"):
            imgcat = shutil.which("imgcat")
            if imgcat:
                terminal_previewers.append(imgcat)

            if sys.platform.startswith("win"):
                local_scripts = Path(
                    os.environ.get(
                        "LOCALAPPDATA",
                        str(Path.home() / "AppData" / "Local"),
                    )
                ) / "Packages" / "PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0" / "LocalCache" / "local-packages" / "Python313" / "Scripts"
                terminal_previewers.extend([
                    str(local_scripts / "imgcat.exe"),
                    str(local_scripts / "imgcat.cmd"),
                ])

        if previewer in ("default", "chafa"):
            chafa = shutil.which("chafa")
            if chafa:
                terminal_previewers.append(chafa)

            if sys.platform.startswith("win"):
                explicit_chafa = Path(
                    r"C:\Users\tomhe\AppData\Local\Microsoft\WinGet\Packages\hpjansson.Chafa_Microsoft.Winget.Source_8wekyb3d8bbwe\chafa-1.18.3-1-x86_64-win\Chafa.exe"
                )
                if explicit_chafa.exists():
                    terminal_previewers.append(str(explicit_chafa))

                local_scripts = Path(
                    os.environ.get(
                        "LOCALAPPDATA",
                        str(Path.home() / "AppData" / "Local"),
                    )
                ) / "Packages" / "PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0" / "LocalCache" / "local-packages" / "Python313" / "Scripts"
                terminal_previewers.extend([
                    str(local_scripts / "chafa.exe"),
                    str(local_scripts / "chafa.cmd"),
                ])

        for candidate in terminal_previewers:
            if candidate and Path(candidate).exists():
                try:
                    subprocess.run([candidate, str(path)], check=False)
                    return
                except OSError:
                    continue

    if previewer == "vscode":
        vscode_cli = find_vscode_cli()
        try:
            popen_kwargs = {
                "stdin": subprocess.DEVNULL,
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
            }
            if sys.platform.startswith("win"):
                subprocess.Popen(
                    ["cmd", "/c", "start", "", "/min", "/b", vscode_cli, "--reuse-window", str(path)],
                    **popen_kwargs,
                )
            else:
                popen_kwargs["start_new_session"] = True
                subprocess.Popen([vscode_cli, "--reuse-window", str(path)], **popen_kwargs)
        except FileNotFoundError:
            print(
                "  (couldn't find the VS Code CLI — in VS Code, open the Command "
                "Palette and run \"Shell Command: Install 'code' command in PATH\")"
            )
        except OSError as exc:
            print(f"  (couldn't open preview in VS Code: {exc})")
        return

    if previewer == "paint" and sys.platform.startswith("win"):
        try:
            subprocess.Popen(["cmd", "/c", "start", "", "/min", "/b", "mspaint.exe", str(path)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return
        except OSError as exc:
            print(f"  (couldn't open the image in Paint: {exc})")
            return

    try:
        if sys.platform.startswith("win"):
            subprocess.Popen(
                ["cmd", "/c", "start", "", "/min", "/b", str(path)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        print(f"  (couldn't open the image preview: {exc})")


def load_seen_photos(path):
    """Return a set of original filenames already processed in a prior run."""
    if not path.exists():
        return set()

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return set()

    if isinstance(data, list):
        return {str(item) for item in data}
    if isinstance(data, dict):
        return {str(item) for item in data.get("seen", [])}
    return set()


def save_seen_photos(path, seen_names):
    """Persist the set of original filenames that have already been reviewed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(seen_names)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(ordered, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


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
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Open each image as you process it; default is to print the path and keep the terminal focused",
    )
    parser.add_argument(
        "--preview-app",
        choices=["default", "imgcat", "chafa", "vscode", "paint"],
        default="default",
        help="Which app to use for the preview: default image viewer, imgcat, chafa, VS Code, or Paint (Windows only)",
    )
    parser.add_argument(
        "--reset-seen",
        action="store_true",
        help="Clear the remembered original filenames and start fresh",
    )
    parser.add_argument(
        "--seen-file",
        default=str(Path(__file__).resolve().parent.parent / ".seen_photos.json"),
        help="Path to the JSON file tracking original filenames already seen",
    )
    args = parser.parse_args()

    source_dir = Path(args.source).expanduser().resolve()
    images_root = Path(args.images_root).expanduser().resolve()
    seen_path = Path(args.seen_file).expanduser().resolve()

    if args.reset_seen and seen_path.exists():
        seen_path.unlink()
        print(f"Cleared seen-photo list at {seen_path}")

    seen_names = load_seen_photos(seen_path)

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

    total_files = len(files)
    files = [p for p in files if p.name not in seen_names]
    if not files:
        print(f"All {total_files} image(s) in {source_dir} were already seen; nothing to do.\n")
        sys.exit(0)

    print(f"Found {len(files)} new image(s) in {source_dir}\n")

    added, skipped = 0, 0

    for i, path in enumerate(files, start=1):
        print(f"[{i}/{len(files)}] {path.name}")
        if args.preview:
            show_preview(path, previewer=args.preview_app)
        else:
            print(f"  Preview path: {path}")

        category = prompt_category()
        if category == "quit":
            print("\nStopping early.")
            save_seen_photos(seen_path, seen_names)
            break
        if category == "skip":
            seen_names.add(path.name)
            save_seen_photos(seen_path, seen_names)
            print("  Skipped and remembered.\n")
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

        seen_names.add(path.name)
        save_seen_photos(seen_path, seen_names)

        print(f"  -> {dest_path.relative_to(images_root.parent)}  ({location})\n")
        added += 1

    print(f"Done. Added {added}, skipped {skipped}.")
    if added:
        print("Commit and push images/ — the GitHub Action will rebuild images.json automatically.")


if __name__ == "__main__":
    main()