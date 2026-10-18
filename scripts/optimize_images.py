#!/usr/bin/env python3
"""Build display-sized WebP copies while preserving the source photographs."""

import shutil
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = ROOT / "images"
OUTPUT_ROOT = ROOT / "dist"
CATEGORIES = ("nature", "city")
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_DIMENSION = 2400
WEBP_QUALITY = 82


def main():
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)

    original_bytes = 0
    optimized_bytes = 0
    image_count = 0

    for category in CATEGORIES:
        source_dir = SOURCE_ROOT / category
        output_dir = OUTPUT_ROOT / "images" / category
        if not source_dir.is_dir():
            continue

        for source_path in sorted(source_dir.iterdir()):
            if not source_path.is_file() or source_path.suffix.lower() not in EXTENSIONS:
                continue

            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{source_path.name}.webp"

            with Image.open(source_path) as source_image:
                image = ImageOps.exif_transpose(source_image)
                mode = "RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB"
                if image.mode != mode:
                    image = image.convert(mode)
                image.thumbnail(
                    (MAX_DIMENSION, MAX_DIMENSION),
                    Image.Resampling.LANCZOS,
                )
                image.save(output_path, "WEBP", quality=WEBP_QUALITY, method=6)

            original_bytes += source_path.stat().st_size
            optimized_bytes += output_path.stat().st_size
            image_count += 1

    print(
        f"Optimized {image_count} photo(s): "
        f"{original_bytes / 1024**2:.1f} MiB -> "
        f"{optimized_bytes / 1024**2:.1f} MiB"
    )


if __name__ == "__main__":
    main()