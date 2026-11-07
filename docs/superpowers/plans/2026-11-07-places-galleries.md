# Places galleries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two watermarked place galleries (`/torfa/`, `/kverkfjoll/`) with home-page teasers, an "In the field" section, and photos for Science and Contact.

**Architecture:** `content.yaml` gains a `places:` list that drives both `prepare_images.py` (watermarked WebP sets under `static/img/places/<slug>/`) and the build. `build.py` renders a shared `layout.html` into `index.html` plus one `place.html` per place, with a `root` prefix (`""` or `"../"`) keeping every link relative. A vanilla-JS `<dialog>` viewer enhances plain image links.

**Tech Stack:** Python 3.12+, uv, Jinja2, PyYAML, Pillow, pytest; vanilla JS and CSS.

**Spec:** `docs/superpowers/specs/2026-11-07-places-galleries-design.md` (extends `docs/superpowers/specs/2026-11-06-fire-under-ice-site-design.md`). Read both.

## Global Constraints

- Facts come only from the brochure or Lorenzo; captions/alt texts are the spec's section 3 drafts, never new facts.
- Originals never enter the repository; `.gitignore` already excludes `*.jpg`, `*.JPG`, `*.jpeg`.
- Web images: WebP quality 78, no EXIF/metadata, never upscaled. Gallery widths `400 / 800 / 1400 / 2000`; other jobs keep `800 / 1400 / 2000`.
- Watermark: badge `BROCHURE/logos/csi_logo_crop.png` at 80 % opacity, bottom right; `base = min(W, H*4/3)`, margin `0.025*base`, badge width `0.08*base`, text size `0.02*base`, gap `0.012*base`, shadow blur `0.003*base`; text `"© " + author` in Cabin SemiBold, white (alpha 220) over a black (alpha 170) blurred shadow. Applied to each size separately.
- All HTML asset and page links are relative (no leading `/`).
- The page works without JavaScript; `prefers-reduced-motion` disables transitions.
- The build must never require the original photos: CI has only `static/`. Validation checks derived files in `static/img/places/`, never `source:` paths.
- Every commit leaves `uv run pytest -q` and `uv run build.py` green on the real `content.yaml`. Until Task 7, `places` and `field` are optional sections.
- Commit prefixes: `feat:`, `fix:`, `content:`, `docs:`, `test:`, `chore:`. End messages with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **A place page's `../` prefix.** Every `src`, `srcset` and local `href` on `_site/torfa/index.html` must resolve to an existing file. Test `test_all_local_links_resolve` (Task 3) checks all pages.
2. **Author names with non-ASCII characters** (e.g. "Lorenzo Scialò") in the watermark and slug of a source file with accents/spaces (`Copia di Vatnajökull 2026 - Paolo Testa (113).JPG`): watermark renders without error; `gallery_ref` yields `[a-z0-9-]` only. Tests in Tasks 1 and 2.
3. **Removing a photo from `content.yaml`** must remove its files from `static/img/places/` on the next `prepare_images.py` run, or the stale images would still be committed and served. Test `test_gallery_removes_stale` (Task 2).
4. **Portrait photos** (Maria's S24 hall shots are 3000×4000): mark the same visual size as on landscape, no overflow, grid crop sensible. Test `test_watermark_portrait` (Task 2).
5. **Viewer at the ends and with keyboard only.** Next on the last photo wraps to the first, Esc closes and focus returns to the thumbnail, Back closes when opened via hash. Manual checklist in Task 5 (no JS test runner in this repo).

---

## File Structure

| File | Responsibility |
|---|---|
| `sitelib.py` | + `gallery_ref`, `slugify`, places/field validation, `RESPONSIVE_WIDTHS` with 400 |
| `prepare_images.py` | root becomes `EXPEDITION`; + `watermark`, `gallery_jobs`, `run_gallery` |
| `fonts/Cabin-SemiBold.otf`, `fonts/OFL.txt` | watermark font, not published |
| `build.py` | renders `index.html` + one page per place, passes `root` |
| `templates/layout.html` | was `base.html`; head, nav, footer; blocks |
| `templates/index.html`, `templates/place.html` | home page; place page |
| `templates/macros.html` | `image` gains `root`; + `place_card`, `gallery_grid` |
| `templates/sections/places.html`, `field.html` | new home sections; `science.html`, `contact.html` gain images |
| `static/script.js`, `static/style.css` | viewer; styles for new parts |
| `content.yaml` | real places, field, section images, credits |
| `GUIDE.md` | "Adding a photo to a place" |
| `tests/test_sitelib.py`, `tests/test_images.py`, `tests/test_build.py` | tests per task |

---

### Task 1: Places in the content model (`sitelib.py`)

**Files:**
- Modify: `sitelib.py` (REQUIRED, OPTIONAL_SECTIONS, RESPONSIVE_WIDTHS, validate)
- Test: `tests/test_sitelib.py`

**Interfaces:**
- Produces:
  - `slugify(text: str) -> str`: lowercase, strip accents (NFKD, drop combining marks), runs of chars outside `[a-z0-9]` become one `-`, trimmed of `-`.
  - `gallery_ref(slug: str, source: str) -> str`: `f"img/places/{slug}/{slugify(Path(source).stem)}"`.
  - `RESPONSIVE_WIDTHS = (400, 800, 1400, 2000)`.
  - `OPTIONAL_SECTIONS = ("sponsors", "places", "field")`.
  - Content shape: `places[i] = {slug, name, years, teaser, intro: [str], photos: [{source, author, caption, alt, cover?: bool, featured?: bool}]}`; `field[i] = {title, text, image, image_alt, credit}`; `science[i].image/image_alt/credit` optional (`credit` optional even with an image); `contact_image = {image, image_alt, credit}` optional; `headings.places`, `headings.field` = `{kicker, title, intro?}`.

- [ ] **Step 1: Write failing tests** in `tests/test_sitelib.py`. Add a helper `place(slug="torfa", n=4)` returning a valid place whose first photo has `cover: True`, the next three `featured: True`, sources `photos/<slug>/P<i>.JPG`, plus a fixture writing the matching 400-wide webp files under `static/img/places/<slug>/`.

```python
def test_slugify():
    assert slugify("Copia di Vatnajökull 2026 - Paolo Testa (113)") == "copia-di-vatnajokull-2026-paolo-testa-113"
    assert slugify("P7110912") == "p7110912"
    assert slugify("20260711_143730") == "20260711-143730"

def test_gallery_ref():
    assert gallery_ref("torfa", "photos/torfa/RIMG0247.JPG") == "img/places/torfa/rimg0247"

def test_places_valid(...):            # minimal_content + places + headings.places -> validate == []
def test_places_optional(...):         # minimal_content without places/field -> []
def test_place_missing_keys(...):      # each of slug,name,years,teaser,intro,photos removed -> "places[0].<key>: missing"
def test_photo_missing_keys(...):      # each of source,author,caption,alt -> "places[0].photos[1].<key>: missing"
def test_place_empty_photos(...):      # "places[0].photos: missing"
def test_bad_slug(...):                # "Torfa", "static", duplicate slug -> error mentions "places[1].slug"
def test_duplicate_stem(...):          # sources "a/X 1.JPG" and "b/x-1.jpg" in one place -> error "same image name"
def test_cover_featured_counts(...):   # 0 covers, 2 covers, 2 featured, 4 featured, a photo with both -> one error each, path "places[0]"
def test_gallery_image_missing(...):   # delete one webp -> "places[0].photos[2]: image not found ... run uv run prepare_images.py"
def test_places_need_heading(...):     # places present, headings.places absent -> "headings.places: missing"
def test_field_item_rules(...):        # field item without image_alt -> "field[0].image_alt: missing"
def test_photo_alt_not_name(...):      # a photo entry is not mistaken for an image key: no "name: missing" error
def test_todo_in_caption(...):         # "TODO" in a caption -> "places[0].photos[0].caption: contains TODO"
```

- [ ] **Step 2: Run** `uv run pytest tests/test_sitelib.py -q`. Expected: the new tests FAIL (ImportError for `slugify`/`gallery_ref`).

- [ ] **Step 3: Implement** in `sitelib.py`. Add `"places": [...]`, `"places.photos": [...]`, `"field": ["title","text","image","image_alt","credit"]` to REQUIRED; a `_validate_places(content, static_dir) -> list[str]` called from `validate` for the slug, stem, cover/featured and derived-image rules (use `image_info(static_dir, gallery_ref(...))`), and the `headings.places`/`headings.field` requirement when the section is non-empty. `source` is not in `IMAGE_KEYS`, so the generic walk ignores it (no `source` existence check: constraint). Allowed-slug regex `^[a-z0-9-]+$`; reserved `{"static"}`.

- [ ] **Step 4: Run** `uv run pytest -q` and `uv run build.py`. Expected: all PASS; build prints `Built …` (real content has no places yet).

- [ ] **Step 5: Commit** `feat: places and field in the content model`.

---

### Task 2: Watermarked gallery images (`prepare_images.py`)

**Files:**
- Modify: `prepare_images.py`
- Create: `fonts/Cabin-SemiBold.otf` (copy of `/usr/share/fonts/opentype/cabin/Cabin-SemiBold.otf`), `fonts/OFL.txt` (copy of `static/fonts/OFL.txt`)
- Test: `tests/test_images.py`

**Interfaces:**
- Consumes: `gallery_ref`, `load_content` (Task 1).
- Produces:
  - `EXPEDITION = Path.home() / "expeditions/Iceland"`; `BROCHURE = EXPEDITION / "brochure/2027"` kept for the badge; every `JOBS` source gets the prefix `brochure/2027/` and `run_job` resolves against `EXPEDITION`.
  - `GALLERY_WIDTHS = (400, 800, 1400, 2000)`; `BADGE = BROCHURE / "logos/csi_logo_crop.png"`; `FONT = HERE / "fonts/Cabin-SemiBold.otf"`.
  - `watermark(im: Image.Image, author: str, badge: Image.Image, font_path: Path) -> Image.Image` (RGB in, RGB out, same size; pure).
  - `gallery_jobs(content: dict) -> list[tuple[str, str, str]]`: `(source, author, ref)` per photo, in content order.
  - `run_gallery(content: dict, root: Path, out_dir: Path, badge: Image.Image, font_path: Path) -> list[Path]`: writes `<out_dir>/<ref minus "img/">-<w>.webp` for each width ≤ source width (source narrower than 400: its own width), each watermarked after resizing; then deletes files in `out_dir/places/<slug>/` that no job wrote, and folders of slugs no longer in content.
  - `main()` runs `JOBS`, then `run_gallery(load_content(...), EXPEDITION, OUT_DIR, Image.open(BADGE), FONT)`, per-photo failures reported as WARNING like today.

- [ ] **Step 1: Write failing tests** in `tests/test_images.py`, using a generated badge (`Image.new("RGBA", (216, 206), (0,0,0,255))`) and the repo `FONT`.

```python
def test_watermark_keeps_size_and_marks_corner():
    im = Image.new("RGB", (2000, 1500), "white")
    out = watermark(im, "Andrea Benassi", badge, FONT)
    assert out.size == (2000, 1500) and out.mode == "RGB"
    assert out.getpixel((1950, 1440)) != (255, 255, 255)     # inside the badge
    assert out.getpixel((10, 10)) == (255, 255, 255)          # top-left untouched

def test_watermark_portrait():
    out = watermark(Image.new("RGB", (1500, 2000), "white"), "Maria F. Trombini", badge, FONT)
    # badge width 0.08 * min(1500, 2666) = 120 px: column 1500-37-121 is clear, 1500-37-60 is marked
    assert out.getpixel((1500 - 37 - 60, 2000 - 37 - 30)) != (255, 255, 255)

def test_watermark_non_ascii_author():   # "Lorenzo Scialò" renders, corner changed

def test_gallery_jobs(): # content with 2 places -> [("photos/torfa/P1.JPG","A","img/places/torfa/p1"), ...]

def test_run_gallery_writes_widths_without_exif(tmp_path):
    # source 2500x1875 JPEG saved WITH exif (Image.Exif(); exif[0x010F]="Cam") under root/photos/torfa/
    # -> places/torfa/p1-400/-800/-1400/-2000.webp exist, widths match, Image.open(p).getexif() is empty

def test_run_gallery_no_upscale():    # 900 px source -> exactly p1-400.webp and p1-800.webp
def test_run_gallery_tiny_source():   # 300 px source -> exactly p1-300.webp

def test_gallery_removes_stale(tmp_path):
    # pre-create places/torfa/old-800.webp and places/gone/x-800.webp -> after run both removed, new files present
```

- [ ] **Step 2: Run** `uv run pytest tests/test_images.py -q`. Expected: new tests FAIL (ImportError).

- [ ] **Step 3: Implement** the functions above. The watermark algorithm is the mock-up of 2026-11-07, values in Global Constraints: badge resized to `round(0.08*base)` wide (LANCZOS), alpha multiplied by 0.8; text drawn on a transparent layer, shadow layer blurred with `GaussianBlur(0.003*base)`; text vertically centred on the badge, right edge `0.012*base` left of it; composite over the photo. Save with `_save_webp` (Pillow writes no EXIF unless given `exif=`). Update the module docstring's "Job kinds" list with `gallery`.

- [ ] **Step 4: Run** `uv run pytest -q`. Expected: all PASS (existing `test_responsive_*` unchanged: normal jobs keep `WIDTHS`).

- [ ] **Step 5: Commit** `feat: watermarked gallery images from content.yaml` (include `fonts/`).

---

### Task 3: Multi-page build with a shared layout

**Files:**
- Rename: `templates/base.html` → `templates/layout.html`
- Create: `templates/index.html`, `templates/place.html`
- Modify: `templates/macros.html`, all `templates/sections/*.html` that call `image(...)` or link to `static/`, `build.py`
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `gallery_ref` (Task 1), as a Jinja global `gallery_ref`.
- Produces:
  - Templates render with `c` (content) and `root` (`""` or `"../"`); `place.html` also gets `place` (one entry of `c.places`).
  - `layout.html` blocks: `title`, `description`, `og_image`, `main`. Nav: Project, Years, Places (only if `c.places`), Science, Team, Contact, each `href="{{ root }}#id"`; brand `href="{{ root }}#top"`. Footer unchanged plus `{{ root }}` on its image.
  - `image(ref, alt, sizes, cls, priority, lazy, root="")` prefixes `src` and each `srcset` URL with `root`.
  - `gallery_grid(place, root)` macro: `<ul class="gallery">` of `<li><a href="{{ root }}{{ big.src }}" data-index="{{ i }}" id="photo-{{ i+1 }}" aria-label="{{ caption }} © {{ author }}">` + 400/800 `image(...)` + hidden `<span class="gallery-caption">` (caption) and `<span class="gallery-credit">` (© author) `</a></li>`, where `big = img(gallery_ref(...))`. The link carries `data-srcset` = the full srcset with `root` applied.
  - `place.html`: heading strip (`kicker` = years, `h1` = name), intro paragraphs, `gallery_grid`, footer links "← Home" (`{{ root }}`) and "Next: <other place>" (`{{ root }}<other.slug>/`, only when there is another place).
  - `build.build(root: Path, out: Path) -> int` writes `out/index.html` and `out/<slug>/index.html` for each place; page `<title>` `"{name} · {site.title}"`, description = teaser, `og:image` = cover's 1400 (or largest) file as an absolute URL `{site.url}/{src}`.

- [ ] **Step 1: Write failing tests** in `tests/test_build.py`. Extend the `site` fixture with an optional place (reuse Task 1's `place()` helper and image fixture).

```python
def test_writes_place_pages(site_with_places):
    out = site_with_places / "_site"
    assert build(site_with_places, out) == 0
    assert (out / "torfa" / "index.html").is_file() and (out / "kverkfjoll" / "index.html").is_file()

def test_all_local_links_resolve(site_with_places):
    # for every built .html: collect src=, href=, and each URL in srcset= / data-srcset=;
    # skip http(s):, mailto:, pure "#…"; strip "#…"; resolve against the page's folder;
    # a path ending in "/" means "<path>index.html"; assert each exists
def test_place_page_title_and_og(site_with_places):   # "<title>Torfa caldera · Fire Under Ice</title>", og:image starts with "https://fireunderice.org/static/img/places/torfa/"
def test_place_nav_points_home(site_with_places):     # 'href="../#team"' in torfa page
def test_gallery_links_without_js(site_with_places):  # each grid <a href> ends in "-2000.webp" (or largest) and has aria-label with "©"
def test_no_places_no_nav_link(site):                 # minimal content: no 'href="#places"' and no "places" folder
```

Keep `SECTION_IDS` tests passing (home page unchanged when there are no places).

- [ ] **Step 2: Run** `uv run pytest tests/test_build.py -q`. Expected: new tests FAIL.

- [ ] **Step 3: Implement** the templates and `build.py`. `index.html` extends `layout.html` and includes today's sections in today's order (sections added in Tasks 4 and 6). Pass `root=""` to the home page; sections calling `image(...)` forward `root`. `model-viewer` and `data-model` paths also get `root` (they are only on the home page, so `""`).

- [ ] **Step 4: Run** `uv run pytest -q && uv run build.py`, then diff the home page against the previous build: build at the previous commit into a scratch folder (`git worktree add <scratch>/before HEAD` there `uv run build.py`), then `diff <(tr -s ' \n' < <scratch>/before/_site/index.html) <(tr -s ' \n' < _site/index.html)`, then `git worktree remove <scratch>/before`. Expected: tests PASS; the only differences are whitespace from the template split (no content or path changes).

- [ ] **Step 5: Commit** `feat: multi-page build with a shared layout and place pages`.

---

### Task 4: Places section on the home page

**Files:**
- Create: `templates/sections/places.html`
- Modify: `templates/index.html` (include after `years.html`, only `{% if c.places %}`), `templates/macros.html` (+ `place_card`), `static/style.css`
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `gallery_ref`, `image` with `root` (Task 3); `c.headings.places`.
- Produces: `place_card(place, root)`: `<article class="place-card">` containing an `<a class="place-card-link" href="{{ root }}{{ place.slug }}/">` around the cover image (sizes `(min-width: 48rem) 50vw, 100vw`), `<h3>` name, kicker years, teaser, `<ul class="place-thumbs">` of the three featured images (sizes `8rem`), and the text "See all {{ place.photos|length }} photos". Section `id="places"`, class `reveal`.

- [ ] **Step 1: Write failing tests**: `test_places_section` (home page has `id="places"`, a card per place, `href="torfa/"`, text "See all 4 photos", exactly 3 `place-thumbs` images per card, cover image src contains the cover's ref) and `test_places_nav_link` (`href="#places"` present when places exist).

- [ ] **Step 2: Run** `uv run pytest tests/test_build.py -q`. Expected: the two tests FAIL.

- [ ] **Step 3: Implement** the section, macro and CSS: cards in a 1-column grid, 2 columns from `48rem`; cover `aspect-ratio: 4/3; object-fit: cover`; thumbs square, `gap: .5rem`; whole card keyboard-focusable through its link with a visible focus ring; reuse existing colour variables (`--ice`, card styles from `.card`). Gallery grid CSS for `place.html` here too: `.gallery` 2 columns, 3 from `48rem`, 4 from `72rem`, square cells via `aspect-ratio: 1; object-fit: cover`; `.gallery-caption, .gallery-credit` visually hidden.

- [ ] **Step 4: Run** `uv run pytest -q && uv run build.py`. Expected: PASS, `Built …`.

- [ ] **Step 5: Commit** `feat: places teaser section on the home page`.

---

### Task 5: Photo viewer

**Files:**
- Modify: `templates/place.html` (one `<dialog class="viewer" aria-label="Photo viewer">` with `<img>`, `<p class="viewer-caption">`, `<p class="viewer-credit">`, buttons `.viewer-prev`, `.viewer-next`, `.viewer-close` with `aria-label`s "Previous photo", "Next photo", "Close"), `static/script.js` (new numbered block "Photo viewer"), `static/style.css`
- Test: `tests/test_build.py` (markup only)

**Interfaces:**
- Consumes: grid links from Task 3 (`.gallery a[data-index]`, `href`, `data-srcset`, hidden caption/credit spans).
- Produces: behaviour per spec section 7.

- [ ] **Step 1: Write failing test** `test_viewer_markup`: a place page contains exactly one `<dialog class="viewer"`, the three buttons with their `aria-label`s, and the dialog is absent from the home page.

- [ ] **Step 2: Run** `uv run pytest tests/test_build.py::test_viewer_markup -q`. Expected: FAIL.

- [ ] **Step 3: Implement** the dialog markup and the script block: only when `HTMLDialogElement` exists; click on a grid link → `preventDefault`, `showModal()`, set `img.srcset`/`sizes="100vw"`/`src`/`alt` (alt = the thumbnail's alt), caption, credit; preload the next image with `new Image()`; prev/next wrap around; ArrowLeft/ArrowRight; swipe via `pointerdown`/`pointerup` with |dx| > 50 px and |dx| > |dy|; Esc (native `cancel`) and close button; on close focus returns to the opening link. Hash: opening sets `history.pushState(null, '', '#photo-N')`; `popstate` without a photo hash closes; loading a page with `#photo-N` opens that photo. CSS: dialog full viewport, dark backdrop, image `max-height: calc(100svh - 7rem); object-fit: contain`, buttons ≥ 44 px; transitions only under `prefers-reduced-motion: no-preference`.

- [ ] **Step 4: Verify** `uv run pytest -q && uv run build.py`, The hand check runs in Task 7 Step 5, on the real pages (`uv run python -m http.server -d _site 8000`, `http://localhost:8000/torfa/`). Viewer checklist: click opens; ←/→ and buttons move and wrap from last to first; Esc and × close and focus returns to the thumbnail; Back closes after opening; `…/torfa/#photo-3` opens photo 3; swipe in DevTools device mode; with JavaScript disabled a click opens the large image file.

- [ ] **Step 5: Commit** `feat: photo viewer for place pages`.

---

### Task 6: In the field, Science images, Contact background, photo credits

**Files:**
- Create: `templates/sections/field.html`
- Modify: `templates/index.html` (field after science, `{% if c.field %}`), `templates/sections/science.html`, `templates/sections/contact.html`, `templates/layout.html` (footer), `static/style.css`
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `field`, `science[i].image`, `contact_image`, `headings.field`, `places[].photos[].author` (Task 1 shapes).
- Produces:
  - Jinja global `photo_authors(c) -> list[str]` in `build.py`: unique authors from places photos, `field`, `science` and `contact_image` credits, sorted by surname (last word).
  - Footer: when non-empty, `<li>Photos: A, B, C.</li>` and `<li>Photos © their authors. For use, write to <a href="mailto:…">…</a>.</li>` before the existing credits.

- [ ] **Step 1: Write failing tests**: `test_field_section` (`id="field"`, one item per entry with its image and title), `test_science_card_images` (a science entry with `image` renders an `<img>` inside its `.card`; the existing wide figure for an entry with `model` still renders), `test_contact_background` (`contact_image` renders an `<img class="contact-bg"`), `test_photo_credits_footer` (authors "Andrea Benassi", "Maria F. Trombini", "Ivan Vicenzi" → `Photos: Andrea Benassi, Maria F. Trombini, Ivan Vicenzi.`), `test_no_photo_credit_without_photos` (minimal content: no "Photos:" line).

Note: Science today renders `image` as the wide figure below the cards. Keep that for the photogrammetry 3D figure by renaming its keys in Task 7's content to `figure`, `figure_alt`, `figure_caption` and reading those in the wide-figure loop; `image`/`image_alt` now mean the card image. Update `sitelib` `ALT_FROM_SIBLING`/`IMAGE_KEYS` with `figure` and adapt existing tests that use `science[].image` as a figure.

- [ ] **Step 2: Run** `uv run pytest tests/test_build.py -q`. Expected: new tests FAIL.

- [ ] **Step 3: Implement** templates and CSS: field items in the existing `.cards` grid with a 4:3 image on top; science card images 4:3 `object-fit: cover`; contact section `position: relative`, background image `object-fit: cover` under a dark overlay so text keeps at least 4.5:1 contrast.

- [ ] **Step 4: Run** `uv run pytest -q && uv run build.py`. Expected: PASS, `Built …`.

- [ ] **Step 5: Commit** `feat: In the field section, science and contact photos, photo credits`.

---

### Task 7: Real content and images

**Files:**
- Create (outside the repo): `~/expeditions/Iceland/photos/torfa/`, `~/expeditions/Iceland/photos/kverkfjoll/`
- Modify: `content.yaml`, `prepare_images.py` (`JOBS` lines), generated `static/img/**`

**Interfaces:**
- Consumes: everything above.

- [ ] **Step 1: Copy originals** (copy, never move; keep `~/Desktop/to_add` intact):
  - to `photos/torfa/`: `river_crossing.JPG`; from `sala_graal/`: `P7110912.JPG`, `P7110909.JPG`, `20260711_143730.jpg`, `20260711_144140.jpg`; `sala_graal/Copia di RIMG0247.JPG` as `RIMG0247.JPG`; `Copia di Vatnajökull 2026 - Paolo Testa (113).JPG` as `thermal_camera.JPG`.
  - to `photos/kverkfjoll/`: from `encelado_w_lake/`: `P7161033.JPG`, `20260716_093800.jpg`, `P7171153.JPG`; from `sala_graal/`: `P7161066.JPG`, `P7161094.JPG`, `P7181204.JPG`; `blue_ice.jpg`.
  - Not copied: `sala_graal/P7181214.JPG`, `sala_graal/20260711_143915.jpg`.
  Verify: `ls ~/expeditions/Iceland/photos/*/ | wc -l` lists 7 + 7 files.

- [ ] **Step 2: Write `content.yaml`**: `headings.places` `{kicker: Places, title: Where we work}`; `headings.field` `{kicker: In the field, title: What the ice demands}`; `places` exactly as spec section 3 (order, sources, authors, captions, ◆ = `cover: true`, ★ = `featured: true`, intros from 3.1/3.2, a one-sentence `teaser` drawn from each intro); alt texts written by looking at each photo, describing only what is visible (e.g. "Two cavers on a dark mound in a domed ice hall, orange mineral crust below."); Lorenzo reviews them before publishing. `field` from spec section 6 (four items, credits Paolo Testa / Andrea Benassi ×3) with images `img/field-river`, `img/field-rope`, `img/field-gas`, `img/field-heat`. Science: Microbiology `img/science-pool` (Ivan Vicenzi), Monitoring `img/science-thermal` (Paolo Testa), Photogrammetry `img/f7-ortho` (no `credit`: it is a drone orthophoto) plus the renamed `figure*` keys. `contact_image`: `img/contact-blue-ice` (Maria F. Trombini).

- [ ] **Step 3: Add `JOBS` lines** (sources relative to `EXPEDITION`):

```python
("responsive", "photos/torfa/river_crossing.JPG", "field-river"),
("responsive", "photos/kverkfjoll/P7161066.JPG", "field-rope"),
("responsive", "photos/kverkfjoll/P7181204.JPG", "field-gas"),
("responsive", "photos/kverkfjoll/P7161094.JPG", "field-heat"),
("responsive", "photos/torfa/RIMG0247.JPG", "science-pool"),
("responsive", "photos/torfa/thermal_camera.JPG", "science-thermal"),
("responsive", "photos/kverkfjoll/blue_ice.jpg", "contact-blue-ice"),
```

- [ ] **Step 4: Generate** `uv run prepare_images.py`. Expected: no WARNING lines; `static/img/places/torfa/` holds 9 photos × up to 4 widths, `kverkfjoll/` 10; total printed under ~12 MB. Open three outputs (one portrait hall shot, one snow photo, one 2000-px `p06-lake`) and check the mark: "© Name" correct, badge legible.

- [ ] **Step 5: Build and check** `uv run pytest -q && uv run build.py`. Expected: PASS, `Built …`, no "Skipped" for new entries. Run the Task 5 manual checklist on the real pages, plus: phone over LAN; home page Places cards; In the field; Science; Contact contrast; Lighthouse mobile on `/` and `/torfa/` with performance and accessibility ≥ 90.

- [ ] **Step 6: Commit** `content: Torfa and Kverkfjöll galleries, In the field, section photos` (`git status` first: no `.jpg` staged).

---

### Task 8: Guide and spec bookkeeping

**Files:**
- Modify: `GUIDE.md`, `docs/superpowers/specs/2026-11-06-fire-under-ice-site-design.md` (section 12: point "gallery" to the new spec)

- [ ] **Step 1: Update `GUIDE.md`**: table rows for `fonts/`, `templates/layout.html`/`index.html`/`place.html`, `~/expeditions/Iceland/photos/`; section 1 diagram shows one page per place; new section "Adding a photo to a place" (copy original into `~/expeditions/Iceland/photos/<place>/`; add an entry with `source`, `author`, `caption`, `alt`; optionally `cover`/`featured` keeping one cover and three featured; `uv run prepare_images.py`; build; preview; commit including `static/img/places/`); rules "removing an entry removes its images on the next prepare run" and "a photo replaced elsewhere moves into its place's gallery"; seasonal checklist step 1 mentions galleries; open item: swap the five brochure-cropped sources for originals.

- [ ] **Step 2: Verify** `uv run pytest -q && uv run build.py`. Expected: PASS.

- [ ] **Step 3: Commit** `docs: guide for place galleries`.
