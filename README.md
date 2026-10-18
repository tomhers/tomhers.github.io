# Portfolio site

## Adding photos

Drop image files into:

- `images/nature/` for nature/landscape shots
- `images/city/` for city shots

Name each file like this:

```
<location-slug>--<YYYY-MM>.jpg
```

Examples:

```
images/nature/mount-rainier--2026-07.jpg   -> "Mount Rainier", Jul 2026
images/city/tokyo-shibuya--2026-05.jpg     -> "Tokyo Shibuya", May 2026
images/nature/painted-hills.jpg            -> "Painted Hills" (no date shown)
```

- Words in the slug are separated by hyphens and get capitalized automatically (`big-sur` → "Big Sur").
- The `--YYYY-MM` part is optional — skip it if you don't want a date caption.
- Supported formats: `.jpg`, `.jpeg`, `.png`, `.webp`.

Commit and push. The GitHub Action (`.github/workflows/build-manifest.yml`)
creates display-sized WebP copies in `dist/`, generates the gallery manifest,
and deploys the optimized site. Your full-resolution originals stay untouched
in `images/` and are not included in the deployed site. Set GitHub Pages' build
source to **GitHub Actions** once in the repository's Pages settings.

## Testing locally

Browsers block `fetch()` of local files opened directly (`file://`), so
double-clicking `index.html` won't load your photos. Build the optimized site,
copy the page into its output folder, and serve that folder:

```
python -m pip install -r requirements.txt
python scripts/optimize_images.py
node scripts/build-manifest.js --optimized --output-dir dist
python -c "from pathlib import Path; Path('dist/index.html').write_bytes(Path('index.html').read_bytes())"
python -m http.server --directory dist
```

For Cloudflare Pages, use this build command and set the output directory to
`dist`:

```
python -m pip install -r requirements.txt && python scripts/optimize_images.py && node scripts/build-manifest.js --optimized --output-dir dist && cp index.html dist/index.html
```

Open the printed `localhost` URL for a local preview.

## Manually regenerating the manifest

To regenerate the source manifest with original image paths:

```
node scripts/build-manifest.js
```
