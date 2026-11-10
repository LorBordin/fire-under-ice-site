# Fire Under Ice website: guide

How this site works and how to update it. Written for Lorenzo; no web experience assumed.

Live site: <https://fireunderice.org> · Repository: <https://github.com/lorbordin/fire-under-ice-site>

## 1. How it works

```
content.yaml ─┐
templates/  ──┼─> build.py ──> _site/ ──> GitHub Pages ──> fireunderice.org
static/     ──┘   (checks, then fills the templates)    (git push triggers GitHub Actions)
```

`_site/` holds the home page (`index.html`), one page per place (`<slug>/index.html`, e.g. `torfa/`), and `static/`.

| File / folder | What it is | Do you edit it? |
|---|---|---|
| `content.yaml` | **All the text** on the page, plus image paths, consent flags and the place galleries | Yes, every season |
| `templates/` | The HTML skeleton (Jinja2: HTML with `{{ gaps }}`): `layout.html` (head, menu, footer, shared by every page), `index.html` (home), `place.html` (one page per place), `sections/` (home-page sections). `base.html` is gone: `layout.html` replaces it | Rarely |
| `fonts/` | `Cabin-SemiBold.otf`, the watermark font on gallery photos; not published on the site. `OFL.txt` is its licence | No |
| `~/expeditions/Iceland/photos/` | Original photos of the place galleries, one folder per place (`torfa/`, `kverkfjoll/`). Outside the repo, like the brochure | Yes: copy new originals here |
| `static/style.css` | The look: colours, fonts, layout | Rarely |
| `static/script.js` | The motion: fade-ins, slider, video. The page works without it | Rarely |
| `static/img/` | Web-sized images, **generated**: never edit by hand. Gallery photos are in `static/img/places/<slug>/` | No (scripts write it) |
| `prepare_images.py` | Turns the originals into web images: brochure images from the `JOBS` list at the top, and place gallery photos from `content.yaml` (watermarked) | Add a `JOBS` line per new brochure image; gallery photos need no line |
| `make_comparison.py`, `georef.py` | Builds the 2006 vs 2025 slider images, on two backgrounds: 2024 satellite (default) and 2026 drone orthophoto | Only if surveys or backgrounds change |
| `make_model.py`, `geo.py` | Builds the interactive 3D model (`static/model/*.glb`) from the ODM OBJ, and prints the cave marker position | Only for a new model |
| `static/vendor/` | `<model-viewer>` 4.0.0 (Google, Apache-2.0), the 3D viewer, kept here so no other server is contacted | No |
| `build.py`, `sitelib.py` | The generator: load, validate, filter consent, render | No |
| `review_copy.py` | Writes a plain-text copy of each science page for the reviewers (`uv run review_copy.py`) | Run it before sending a draft |
| `docs/review/` | Output of `review_copy.py`, one `<slug>.md` per science page | No (the script writes it) |
| `check_links.py` | Checks that external links (YouTube, TG5, …) still work | No, just run it |
| `tests/` | Automatic checks of the generator (`uv run pytest`) | No |
| `.github/workflows/deploy.yml` | Instructions for GitHub: test, build, publish on every push | No |
| `_site/` | Build output. Not in git; recreated by every build | No |

**The safety nets.** `build.py` refuses to build (and so GitHub refuses to publish) if `content.yaml` has:
a `TODO`, a missing required field, an image file that doesn't exist (for a gallery photo it says to run `uv run prepare_images.py`), a place without exactly one `cover: true` and exactly three `featured: true` photos, an image without alt text, or a forbidden phrase
("heart of Europe", "2000 MW", "Kinetic Trigger", "extremophile"). It lists every problem at once with its location, e.g.
`team[0].members[2].photo: file not found: img/team/x.webp`.

People, partners and sponsors appear **only** with `consent: true`. Anything else (`false`, a typo, a missing line) hides them. Write exactly `true`: YAML also treats an unquoted `yes` as true, so avoid it. The build prints who was skipped.

## 2. Everyday commands

Run these in `~/expeditions/Iceland/website`.

| Command | What it does |
|---|---|
| `uv run build.py` | Build the site into `_site/` |
| `uv run python -m http.server -d _site 8000` | Preview at <http://localhost:8000> (Ctrl+C to stop) |
| `uv run pytest` | Run the automatic checks |
| `uv run prepare_images.py` | Regenerate web images: brochure originals (`JOBS`) and place galleries |
| `uv run review_copy.py` | Write `docs/review/<slug>.md` for every science page |
| `uv run check_links.py` | Check external links (some sites block robots: open those by hand) |
| `uv run --group assets make_model.py` | Rebuild the 3D model (~30 s; installs pymeshlab the first time). Paste the printed `model_marker` into `content.yaml` |
| `git status` | What changed since the last commit |
| `git diff` | The changes, line by line |
| `git log --oneline` | History of commits |

Preview on your phone: same Wi-Fi, find your laptop's address with `hostname -I` (first number), open `http://<that>:8000`.

## 3. Publishing a change

```
uv run build.py                      # 1. it must say "Built ..."
uv run python -m http.server -d _site 8000   # 2. look at it; Ctrl+C when happy
git add -A                           # 3. put all changes on the tray
git status                           #    check the list: no surprises?
git commit -m "content: what changed"  # 4. snapshot
git push                             # 5. upload; GitHub builds and publishes
```

Then open the repository's **Actions** tab. A yellow dot means running; a green tick means the site is updated (about a minute);
a red cross means something failed. Click it, open the red step and read the message (it is usually the same list `build.py` prints locally).
**A failed run never takes the site down**: the previous version stays online.

Commit message prefixes, by convention: `content:` text changes, `feat:` new feature, `fix:` correction, `docs:` documentation, `chore:` housekeeping.

## 4. Seasonal update checklist

1. **Photos.** Put originals in the brochure folder (never in this repo). Add one line per photo to `JOBS` in `prepare_images.py`, e.g.
   `("responsive", "brochure/2027/figures/photos/p05-recon.jpg", "p05-recon"),` and run `uv run prepare_images.py`.
   Check each photo for rival-brand logos if a sponsor's gear is in the season.
   Place gallery photos are not in `JOBS`: see "Adding a photo to a place" below.
2. **Text.** Edit `content.yaml`: the new year in `years:`, figures in `project.stats`, new articles and talks in `press:`.
   Facts come from the brochure, the team documents, cited literature (science pages) or from you, never guessed; unknown means `TODO` until you know.
3. **People.** New team members: add them with `consent: false`, switch to `true` once they agree. Each needs a
   `role:` (their job in the expedition, shown in red) and a `line:` (short bio). Team photos go through
   the `square` job in `prepare_images.py` (400×400).
4. **Check.** `uv run build.py`, preview on laptop and phone, `uv run check_links.py`.
5. **Publish.** Commit and push (section 3). Open <https://fireunderice.org> on your phone to confirm.

### Changing the slider's satellite background

Google Earth Pro can't export a positioned image, so the site finds it from a frame drawn on it:

1. `uv run --group assets make_comparison.py --kml` writes `~/expeditions/Iceland/2026/maps/slider_frame.kml`.
2. Open it in Google Earth Pro and follow the steps in its description: pick the date in Historical Imagery,
   press `u` then `n`, save the view as `slider_with_frame.jpg`, untick the KML, save again as `slider_no_frame.jpg`.
3. Copy the copyright line Google prints at the bottom into `SAT_CREDIT` in `make_comparison.py`, and into the
   `credit:` of the satellite background in `content.yaml` and in `credits:` (Google requires it to stay visible).
4. `uv run --group assets make_comparison.py`, then build and preview.

### Adding a photo to a place

Each place in `places:` (in `content.yaml`) has a gallery on its own page. Every gallery photo gets "© author" and the CSI badge burned in by `prepare_images.py`.

1. Copy the original into the place's folder, `~/expeditions/Iceland/photos/<place>/`. Never into this repo.
2. Add an entry under that place's `photos:`. `source` is relative to `~/expeditions/Iceland/`. Real example from Kverkfjöll:

```yaml
      - source: photos/kverkfjoll/P7161033.JPG
        author: Andrea Benassi
        caption: The Encelado cauldron, Kverkfjöll, July 2026.
        alt: Steam rises from a deep ice cauldron with a green lake at its bottom; a caver in yellow watches from the rim.
        cover: true
```

| Field | What it is |
|---|---|
| `source` | The original, relative to `~/expeditions/Iceland/` |
| `author` | Printed on the watermark |
| `caption` | Shown under the photo |
| `alt` | Describes the photo in plain words, for screen readers |
| `cover: true` | The big picture on the place's card on the home page. Exactly one per place |
| `featured: true` | One of the three pictures shown on that card. Exactly three per place |

3. Run `uv run prepare_images.py`. It writes four widths (400, 800, 1400, 2000 px) under `static/img/places/<slug>/`.
4. Run `uv run build.py`. If it says an image is not found, you skipped step 3.
5. Preview, then commit with `static/img/places/` included (section 3).

**Rules**

- **Removing an entry** from `content.yaml` removes its images on the next `uv run prepare_images.py`. Removing a whole place does the same for its folder.
- **A photo replaced elsewhere moves into its place's gallery.** If a photo leaves a background or a section picture (for example a home-page section photo), it goes into its place's gallery, never just deleted. Section photos are clean; their gallery copies carry the watermark.

**Open item.** Five gallery photos are still read from the brochure's cropped copies: `p01-cover`, `p05-recon`, `p06-lake`, `p08-cauldron`, `p08-sala-rosa`. When the full-size originals are available: copy each into `~/expeditions/Iceland/photos/<place>/`, change its `source:` line to the copy, and rerun `uv run prepare_images.py`.

### Science pages

The science pages (e.g. `/microbiology/`, `/analogues/`) are the `topics:` list in `content.yaml`. Each topic has a title, a short teaser, an intro, chapters (a heading, paragraphs, optionally one photo) and references. A reviewer's name goes in `reviewers:`.

**Other text keys worth knowing** (all in `content.yaml`):

- `science_why`: the "Why research here" block above the Science cards. An item with `topic: <slug>` links to that science page, but only once the page is published; before that it is plain text.
- `press.photos`: the photos shown in the press section.
- `press.articles[].status`: optional, e.g. `status: in press`, printed next to the article.
- `partners[].patron_2027: true` marks a partner as a 2027 patron. `headings.partners.patron_note` is the line shown with them ("Patronage being sought for 2027").
- `project.stats[].note`: optional small footnote under a figure.

**Review flow**

1. Write or edit the topic in `content.yaml`. Leave `reviewed: false`.
2. Run `uv run review_copy.py`. It writes `docs/review/<slug>.md`.
3. Send that file to the people named in the topic's `reviewers:` line.
4. Put their corrections into `content.yaml` and repeat until they are happy.

**Publish.** When the reviewers agree, set `reviewed: true` (exactly that; quoted `"true"`, `yes` or a typo keeps the page hidden). Then build, check, commit and push (section 3). Until then the page does not exist on the site: no page, no Research menu link, no card on the home page. The Research menu link and the home cards appear only for published pages.

**Drafts.** A draft may contain `TODO`; it never blocks the build. But forbidden phrases such as "extremophile" are refused even in a draft. Write "thermophiles", "acidophiles" or "psychrophiles" instead.

**Photos.** A draft's photos are made by `uv run prepare_images.py`, like gallery photos (original in `~/expeditions/Iceland/photos/science/`, `source:` relative to `~/expeditions/Iceland/`). They carry the same watermark.

### Adding a sponsor

1. Get the sponsor's agreement and logo (PNG with transparency, or SVG exported to PNG).
2. Add a `logo` job: `("logo", "brochure/2027/logos/brand.png", "logos/brand.png"),` (logo file in the brochure's `logos/` folder) and run `uv run prepare_images.py`.
3. In `content.yaml` under `sponsors:` add
   `- {name: Brand, logo: img/logos/brand.png, url: https://brand.example, consent: true}`.
4. Build, preview, commit, push.

**Rival brands.** No competitor's logo next to a sponsor's (also check photos for visible gear brands).
Concretely: when a **footwear** sponsor is confirmed, set Gaibana (footwear) to `consent: false` under `partners:`.
The brochure does the same in its boots variant (`config/boots.tex`, `\showgaibanafalse`), and that brochure's QR leads here.

## 5. Where things live

| Thing | Where | Notes |
|---|---|---|
| Code and history | GitHub, `lorbordin/fire-under-ice-site` | Public repository (required for free Pages) |
| Publishing settings | Repository → Settings → Pages | Source: GitHub Actions; custom domain; Enforce HTTPS |
| Domain `fireunderice.org` | Cloudflare dashboard → Domain Registration | Renews yearly (~11 USD); keep auto-renew on |
| DNS records | Cloudflare → fireunderice.org → DNS | `A`/`AAAA` to GitHub, `CNAME www`, all "DNS only" (grey cloud) |
| `info@` mail forwarding | Cloudflare → fireunderice.org → Email → Email Routing | Inbox only; replies go out from your own address |
| SSH key | `~/.ssh/id_ed25519` (+ `.pub` registered on GitHub) | Lets `git push` prove it's you |

## 6. Troubleshooting

- **`uv: command not found`**: open a new terminal (uv lives in `~/.local/bin`).
- **Build error list**: fix each line in `content.yaml` at the path shown; rerun.
- **Page looks unstyled in preview**: you opened the file directly; use the `http.server` command and `localhost`.
- **Change not visible online**: check the Actions tab is green; then hard-refresh (Ctrl+Shift+R), browsers cache.
- **`git push` rejected**: someone (or you, from GitHub's web editor) changed the repo; run `git pull` then push again.
- **HTTPS "certificate pending"** right after connecting the domain: wait up to an hour; GitHub issues it automatically.
- **Domain not loading after DNS changes**: DNS takes minutes, occasionally hours, to spread. `dig +short fireunderice.org`
  should list `185.199.108.153` … `.111.153`.
