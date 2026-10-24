#!/usr/bin/env python3
"""Rate the portfolio's existing photos using Chafa previews."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
CATEGORIES = ("nature", "city")
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_ratings(path):
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as fh:
            ratings = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Could not read ratings from {path}: {exc}") from exc

    if not isinstance(ratings, dict):
        raise ValueError(f"Ratings file must contain a JSON object: {path}")

    for photo, rating in ratings.items():
        if not isinstance(photo, str) or type(rating) is not int or not 0 <= rating <= 5:
            raise ValueError(f"Invalid rating entry in {path}: {photo!r}: {rating!r}")
    return ratings


def save_ratings(path, ratings):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with temporary_path.open("w", encoding="utf-8", newline="\n") as fh:
            json.dump(ratings, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        temporary_path.replace(path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def prompt_rating(current_rating):
    current = str(current_rating) if current_rating is not None else "unrated"
    while True:
        raw = input(f"  Rating 0-5 [current: {current}] (q=quit): ").strip().lower()
        if raw in ("q", "quit"):
            return None
        if raw in {"0", "1", "2", "3", "4", "5"}:
            return int(raw)
        print("  Please enter a rating from 0 to 5, or 'q' to quit.")


def main():
    parser = argparse.ArgumentParser(
        description="Preview and rate photos already in the portfolio."
    )
    parser.add_argument(
        "--images-root",
        default=str(PROJECT_ROOT / "images"),
        help="Path to the site's images/ folder (default: ../images relative to this script)",
    )
    parser.add_argument(
        "--ratings-file",
        default=str(PROJECT_ROOT / "ratings.json"),
        help="Path to the JSON file storing photo ratings (default: ../ratings.json)",
    )
    args = parser.parse_args()

    chafa = shutil.which("chafa")
    if not chafa:
        parser.error("Chafa is required for previews; install it and make sure it is on PATH.")

    images_root = Path(args.images_root).expanduser().resolve()
    ratings_path = Path(args.ratings_file).expanduser().resolve()
    if not images_root.is_dir():
        parser.error(f"Images directory does not exist: {images_root}")

    photos = [
        (category, photo)
        for category in CATEGORIES
        if (images_root / category).is_dir()
        for photo in sorted((images_root / category).iterdir())
        if photo.is_file() and photo.suffix.lower() in VALID_EXTENSIONS
    ]
    if not photos:
        print(f"No photos found in {images_root}.")
        return

    try:
        ratings = load_ratings(ratings_path)
    except ValueError as exc:
        parser.error(str(exc))

    print(f"Found {len(photos)} photo(s). Enter a rating from 0 to 5 for each.\n")
    for index, (category, photo) in enumerate(photos, start=1):
        key = f"images/{category}/{photo.name}"
        print(f"[{index}/{len(photos)}] {key}")
        try:
            result = subprocess.run([chafa, str(photo)], check=False)
        except OSError as exc:
            print(f"Could not run Chafa for {photo}: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        if result.returncode != 0:
            print(
                f"Chafa exited with status {result.returncode} for {photo}.",
                file=sys.stderr,
            )
            raise SystemExit(result.returncode)

        rating = prompt_rating(ratings.get(key))
        if rating is None:
            print("\nStopping early; saved ratings are up to date.")
            break
        ratings[key] = rating
        try:
            save_ratings(ratings_path, ratings)
        except OSError as exc:
            print(f"Could not save ratings to {ratings_path}: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        print(f"  Saved rating: {rating}\n")

    print(f"Ratings saved to {ratings_path}.")


if __name__ == "__main__":
    main()
