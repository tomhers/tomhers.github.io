// Scans images/nature and images/city and writes images.json, which the
// site fetches at load time to build the gallery. Run automatically by
// .github/workflows/build-manifest.yml on every push — no manual step.
//
// Filename convention: <location-slug>--<YYYY-MM>.<ext>
// e.g. images/nature/mount-rainier--2026-07.jpg
//      -> location: "Mount Rainier", date: "Jul 2026"
//
// If you skip the "--YYYY-MM" part, the photo still shows up with just a
// location, no date.

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const IMAGES_ROOT = path.join(ROOT, 'images');
const RATINGS_FILE = path.join(ROOT, 'ratings.json');
const args = process.argv.slice(2);
const optimized = args.includes('--optimized');
const outputDirIndex = args.indexOf('--output-dir');
const OUTPUT_ROOT = outputDirIndex === -1
  ? ROOT
  : path.resolve(args[outputDirIndex + 1]);
const CATEGORIES = ['nature', 'city'];
const EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp'];
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

if (optimized && outputDirIndex === -1) {
  throw new Error('--optimized requires --output-dir so the manifest matches the built site.');
}

function loadRatings() {
  if (!fs.existsSync(RATINGS_FILE)) return {};

  const ratings = JSON.parse(fs.readFileSync(RATINGS_FILE, 'utf8'));
  if (!ratings || typeof ratings !== 'object' || Array.isArray(ratings)) {
    throw new Error(`${RATINGS_FILE} must contain a JSON object.`);
  }
  for (const [photo, rating] of Object.entries(ratings)) {
    if (!Number.isInteger(rating) || rating < 0 || rating > 5) {
      throw new Error(`Invalid rating for ${photo}: expected an integer from 0 to 5.`);
    }
  }
  return ratings;
}

function humanize(slug) {
  return slug
    .split('-')
    .filter(Boolean)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function formatDate(yyyyMm) {
  const match = /^(\d{4})-(\d{2})$/.exec(yyyyMm || '');
  if (!match) return '';
  const [, year, month] = match;
  const monthIndex = Number(month) - 1;
  if (monthIndex < 0 || monthIndex > 11) return '';
  return `${MONTHS[monthIndex]} ${year}`;
}

const ratings = loadRatings();
const manifest = [];

for (const category of CATEGORIES) {
  const dir = path.join(IMAGES_ROOT, category);
  if (!fs.existsSync(dir)) continue;

  const files = fs.readdirSync(dir)
    .filter(file => EXTENSIONS.includes(path.extname(file).toLowerCase()))
    .sort();

  for (const file of files) {
    const base = path.basename(file, path.extname(file));
    const [slugPart, datePart] = base.split('--');
    const optimizedFile = `${file}.webp`;
    const rating = ratings[`images/${category}/${file}`];

    if (rating === 0) continue;

    if (optimized && !fs.existsSync(path.join(OUTPUT_ROOT, 'images', category, optimizedFile))) {
      throw new Error(`Optimized image not found: ${path.join(OUTPUT_ROOT, 'images', category, optimizedFile)}`);
    }

    manifest.push({
      category,
      src: `images/${category}/${optimized ? optimizedFile : file}`,
      location: humanize(slugPart || base),
      date: formatDate(datePart),
      rating,
    });
  }
}

fs.mkdirSync(OUTPUT_ROOT, { recursive: true });
fs.writeFileSync(
  path.join(OUTPUT_ROOT, 'images.json'),
  JSON.stringify(manifest, null, 2) + '\n'
);

console.log(`images.json written with ${manifest.length} photo(s) to ${OUTPUT_ROOT}.`);
