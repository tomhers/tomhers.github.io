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

Commit and push. A GitHub Action (`.github/workflows/build-manifest.yml`)
automatically regenerates `images.json` and commits it — you never touch
that file by hand, and you never touch `index.html` to add a photo.

## Testing locally

Browsers block `fetch()` of local files opened directly (`file://`), so
double-clicking `index.html` won't load your photos. Run a tiny local
server from this folder instead:

```
npx serve .
```

or

```
python3 -m http.server
```

then open the printed `localhost` URL. This isn't needed on GitHub Pages —
it only matters for previewing on your own machine.

## Manually regenerating the manifest

Normally the GitHub Action handles this, but if you ever want to run it
yourself:

```
node scripts/build-manifest.js
```
