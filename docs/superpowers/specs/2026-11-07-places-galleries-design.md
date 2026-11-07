# Places galleries, In the field, section photos: design

Date: 2026-11-07. Status: design approved in conversation, awaiting review of this document.

Extends `2026-11-06-fire-under-ice-site-design.md` (the "v1 spec"). Where the two differ, this document wins; in particular it lifts the v1 out-of-scope item "gallery" and turns the site from one page into several.

Paths are relative to `~/expeditions/Iceland/website/` unless stated. `EXPEDITION` means `~/expeditions/Iceland/`; `BROCHURE` means `EXPEDITION/brochure/2027/`.

## 1. Goal

Show more of the photos Lorenzo selected (`~/Desktop/to_add`), without copying the brochure:

1. **Two place pages**, Torfa caldera and Kverkfjöll, each a photo gallery that grows every season, with teasers on the home page.
2. **A watermark** (CSI badge + "© Author") on every gallery photo, so a naive copier sees the source and the author. It is a courtesy layer, not protection: no right-click blocking or other tricks.
3. **"In the field"** section on the home page: what the conditions demand of people and gear.
4. **Photos for Science and Contact** on the home page.

Unchanged from v1: primary reader is a sponsor contact on a phone from the brochure QR; facts come only from the brochure or Lorenzo; originals never enter the repository; web images carry no camera metadata; the page works without JavaScript; Lighthouse mobile performance and accessibility at 90 or above.

Rule for the future: a photo replaced as a background or section image is never dropped; it moves into the gallery of its place.

## 2. Decisions

| Topic | Decision |
|---|---|
| Structure | Separate pages `/torfa/` and `/kverkfjoll/`; home page gets a "Places" section with one teaser card per place (approach C) |
| Photo sources | New folder `EXPEDITION/photos/{torfa,kverkfjoll}/`, files *copied* from `~/Desktop/to_add`. Photos already cropped for the brochure are read from `BROCHURE/figures/photos/` until Lorenzo's full-size originals are available; then only their `source:` line changes |
| Watermark | CSI badge (`BROCHURE/logos/csi_logo_crop.png`) at 80 % opacity, bottom right, width 8 % of the image's reference size; to its left "© Author" in Cabin SemiBold, white with a soft dark shadow. Burned into the pixels by `prepare_images.py`. Approved from the mock-ups of 2026-11-07 |
| Where the mark appears | Every image produced for a gallery, including the home page teaser images (they are gallery images). Section photos on the home page (Science, Contact, In the field) are clean |
| Gallery image size | 400 / 800 / 1400 / 2000 px wide, never upscaled. 2000 px is the largest copy published |
| Home page photo credit | Footer credit line: "Photos: Andrea Benassi, Ivan Vicenzi, Maria F. Trombini, Paolo Testa." (built from the authors in use) plus "Photos © their authors. For use, write to info@fireunderice.org." |
| Viewer | Native `<dialog>` lightbox; each thumbnail is a plain link to the large image, so it works without JavaScript |

## 3. Photos and places

Authors by camera: Galaxy S24 = Maria F. Trombini; E-M10 Mark IV = Andrea Benassi; Ricoh WG-4 = Ivan Vicenzi; Nikon D3300 = Paolo Testa.
Excluded: `sala_graal/P7181214.JPG` (a screenshot of the folder), `sala_graal/20260711_143915.jpg` (near duplicate of `143730`); `gas_mask/` is empty.

Captions below are drafts built only from facts given by Lorenzo or the brochure; Lorenzo checks every caption and alt text before publishing. Order is the page order. ★ = featured: one of the three thumbnails on the home page teaser; ◆ = cover: the teaser's lead image.

### 3.1 Torfa caldera (`slug: torfa`)

Intro (from brochure p6, p8, p10): Freyja Hellir on Kaldaklofsjökull, a new glaciovolcanic cave found in 2026: almost 1500 m surveyed, a hall about 50 m across and roughly 40 m high. From the surface, only a faint hollow in the snow. In 2027 we return to the caldera, this time on its main glacier, Torfajökull.

| # | Source (relative to `EXPEDITION`) | Author | Draft caption |
|---|---|---|---|
| 1 | `photos/torfa/river_crossing.JPG` ★ | Paolo Testa | River crossing on the way to the Torfa caldera, 2026. |
| 2 | `brochure/2027/figures/photos/p08-cauldron.jpg` | Maria F. Trombini | The faint cauldron above the hall of Freyja Hellir, July 2026. |
| 3 | `brochure/2027/figures/photos/p08-sala-rosa.jpg` | Maria F. Trombini | Sala Rosa dei Beati, Freyja Hellir, July 2026: about 50 m across. |
| 4 | `photos/torfa/P7110912.JPG` ◆ | Andrea Benassi | Sala del Graal, Freyja Hellir, July 2026. |
| 5 | `photos/torfa/P7110909.JPG` | Andrea Benassi | Sala del Graal, Freyja Hellir, July 2026. |
| 6 | `photos/torfa/20260711_143730.jpg` | Maria F. Trombini | Sala del Graal, Freyja Hellir, July 2026. |
| 7 | `photos/torfa/20260711_144140.jpg` | Maria F. Trombini | Sala del Graal, Freyja Hellir, July 2026. |
| 8 | `photos/torfa/RIMG0247.JPG` ★ | Ivan Vicenzi | The hot pool at the centre of the Sala del Graal, July 2026. It melted the hall. |
| 9 | `photos/torfa/thermal_camera.JPG` | Paolo Testa | Thermal camera inside a cave, Torfa caldera, 2026. |

(On copying, `Copia di RIMG0247.JPG` becomes `RIMG0247.JPG` and `Copia di Vatnajökull 2026 - Paolo Testa (113).JPG` becomes `thermal_camera.JPG`.)

### 3.2 Kverkfjöll (`slug: kverkfjoll`)

Intro (from brochure p5, p6): in 2025, four people on the trail of Gérald Favre's Swiss team, which explored Kverkfjöll from the 1980s to 2008. The great cave stayed closed; near the hut we found the Hveradalur system, almost 1 km. In 2026 a thaw lake had flooded most of it: 150 m remained above water.

| # | Source (relative to `EXPEDITION`) | Author | Draft caption |
|---|---|---|---|
| 1 | `brochure/2027/figures/photos/p05-recon.jpg` ★ | Andrea Benassi | Kverkfjöll, 2025 reconnaissance. |
| 2 | `brochure/2027/figures/photos/p01-cover.jpg` | Andrea Benassi | Ice cave, Kverkfjöll, 2026. |
| 3 | `photos/kverkfjoll/P7161033.JPG` ◆ | Andrea Benassi | The Encelado cauldron, Kverkfjöll, July 2026. |
| 4 | `photos/kverkfjoll/20260716_093800.jpg` | Maria F. Trombini | The Encelado cauldron, Kverkfjöll, July 2026. |
| 5 | `photos/kverkfjoll/P7171153.JPG` ★ | Andrea Benassi | Lake at the glacier's edge, Kverkfjöll, July 2026. |
| 6 | `brochure/2027/figures/photos/p06-lake.jpg` | Ivan Vicenzi | The thaw lake that flooded Hveradalur, July 2026. |
| 7 | `photos/kverkfjoll/P7161066.JPG` | Andrea Benassi | Rope work on an ice wall, Kverkfjöll, July 2026. |
| 8 | `photos/kverkfjoll/P7161094.JPG` | Andrea Benassi | Steam and volcanic gas, Kverkfjöll, July 2026. |
| 9 | `photos/kverkfjoll/P7181204.JPG` ★ | Andrea Benassi | Full-face respirator beside a fumarole, Kverkfjöll, July 2026. |
| 10 | `photos/kverkfjoll/blue_ice.jpg` | Maria F. Trombini | Blue ice, Kverkfjöll, July 2026. |

The teaser shows the ◆ cover plus the three ★ in list order.

## 4. Content model (`content.yaml`)

New top-level list `places`, plus headings and the two new home sections:

```yaml
headings:
  places:   {kicker: Places, title: Where we work}
  field:    {kicker: In the field, title: What the ice demands}

places:
  - slug: torfa                      # page address /torfa/; lowercase letters, digits, hyphens
    name: Torfa caldera
    years: "2026–2027"
    teaser: One sentence for the home page card.
    intro: [paragraph, ...]
    photos:
      - source: photos/torfa/P7110912.JPG     # relative to ~/expeditions/Iceland/
        author: Andrea Benassi
        caption: Sala del Graal, Freyja Hellir, July 2026.
        alt: Two cavers on a dark mound in a domed ice hall, orange mineral crust below.
        cover: true                  # lead image of the home page card (exactly one per place)
      - source: photos/torfa/RIMG0247.JPG
        ...
        featured: true               # one of the card's three thumbnails (exactly three per place)

field:                               # In the field: 3-4 items
  - title: Rivers
    text: ...
    image: img/field-river           # clean section image (normal JOBS line)
    image_alt: ...
    credit: Paolo Testa

science:
  - title: Microbiology
    text: ...
    image: img/science-pool          # new: card image, cropped 4:3 by CSS
    image_alt: ...
    credit: Ivan Vicenzi

contact_image: {image: img/contact-blue-ice, image_alt: ..., credit: Maria F. Trombini}
```

- The web image of a gallery photo is derived from its entry, never written by hand: `img/places/<slug>/<stem>`, where `<stem>` is the source file name without extension, lowercased, spaces and other non `[a-z0-9-]` characters replaced by `-`. `sitelib.gallery_ref(place, photo)` is the single function both `prepare_images.py` and the templates use.
- The name burned into the watermark is `author:`, so caption credit and watermark cannot disagree.

### 4.1 Validation added to `sitelib.validate`

The build refuses (and so GitHub refuses to publish) when:

- a place lacks `slug`, `name`, `years`, `teaser`, `intro` or `photos`, or has an empty `photos` list;
- a photo lacks `source`, `author`, `caption` or `alt`;
- a slug is not `[a-z0-9-]+`, is repeated, or collides with `static`;
- two photos in one place derive the same `<stem>`;
- a place does not have exactly one `cover: true` photo and exactly three `featured: true` photos, or one photo has both;
- a derived gallery image is missing from `static/img/places/` (message: "run uv run prepare_images.py");
- `field`/`science` images or `contact_image` break the existing image rules (file exists, alt present).

The existing TODO and forbidden-phrase checks apply to all new text. `RESPONSIVE_WIDTHS` becomes `(400, 800, 1400, 2000)`; `image_info` already uses only the widths that exist, so v1 images are unaffected.

## 5. Images (`prepare_images.py`)

- One source root for everything: `EXPEDITION`. Existing `JOBS` lines get the `brochure/2027/` prefix; behaviour is otherwise unchanged.
- New job kind `gallery`, generated automatically from `places` in `content.yaml` (no `JOBS` lines needed): open, apply EXIF rotation, resize to each width, watermark *each size separately* (so the mark has the same proportions at every width), save WebP quality 78 without metadata.
- `watermark(im, author) -> Image` is a pure function: reference size `base = min(W, H·4/3)` (same visual size for portrait and landscape), margin `0.025·base`, badge width `0.08·base`, text size `0.02·base`, gap `0.012·base`, shadow blur `0.003·base`. The badge is read from `BROCHURE/logos/csi_logo_crop.png`. The font is `fonts/Cabin-SemiBold.otf`, kept in the repository outside `static/` (not published; OFL licence alongside).
- Section photos (In the field, Science, Contact) are normal `responsive` `JOBS` lines from `photos/...`, no watermark.
- Stale files: the gallery job deletes `static/img/places/<slug>/` files that no entry produces, so removing a photo from `content.yaml` removes it from the site.

## 6. Pages and templates

```
templates/
├── layout.html          # was base.html: <head>, nav, footer; blocks: title, description, og_image, main
├── index.html           # extends layout; the home page sections in order
├── place.html           # extends layout; one place page
├── macros.html          # + gallery_grid, place_card
└── sections/            # + places.html, field.html; science.html and contact.html gain images
```

- `build.py` renders `index.html` to `_site/index.html` and `place.html` once per place to `_site/<slug>/index.html`.
- Relative links everywhere: templates receive `root` (`""` on the home page, `"../"` on place pages). The `image` macro and every asset or section link are prefixed with it. Place pages link to the home sections as `../#team` and so on.
- Nav: Project, Years, Places, Science, Team, Contact. On a place page "Places" leads to `../#places`, and a small switch links to the other place.
- Each place page has its own `<title>` ("Torfa caldera · Fire Under Ice"), description (the teaser) and `og:image` (the lead photo).

**Home page order**: Hero, Project, Years (with slider and map), **Places**, Watch, Science, **In the field**, Team, Press, Partners, Contact.

**Places section**: two cards side by side from 48rem, stacked below. Card: lead image (4:3), place name, years, teaser, row of three square thumbnails, link "See all N photos". The whole card leads to the place page.

**Place page**: heading strip (name, years), intro, grid of thumbnails (2 columns on a phone, 3 from 48rem, 4 from 72rem; square crops via `object-fit`, 400/800 px sources). Below each thumbnail, no text; caption and credit appear in the viewer and as the link's accessible name. At the end, a link back to the home page and to the other place.

**In the field**: a short intro line and 3-4 items (image + bold title + one or two sentences). Draft, from the brochure p12 variants, for Lorenzo's check:

- *Rivers.* Gear carried on foot for days, through glacial rivers. (`river_crossing`, Torfa)
- *Rotten ice.* Anchors in poor ice and firn have to hold. (`P7161066`, Kverkfjöll)
- *Air you cannot trust.* Cavities under the ice trap CO₂, H₂S and SO₂. In Freyja Hellir the detector alarmed at 5 % CO₂ and we turned back. Respirators are only a safety layer: any alarm, we leave. (`P7181204`, Kverkfjöll)
- *Heat.* Water from 0.2 to 59.4 °C, ground up to 47 °C. (`P7161094`, Kverkfjöll)

The gas text comes from the brochure page owned by Mattia Gerbaudo and still marked "pending his review" there: it is published only after Lorenzo confirms it.

**Science**: each card gets a 4:3 image on top: Microbiology the hot pool (`RIMG0247`), Monitoring the thermal camera (`thermal_camera`), Photogrammetry the drone orthophoto (`img/f7-ortho`, already generated, unused today). The 3D model figure below the cards stays.

**Contact**: `blue_ice` as a dimmed full-width background behind heading and address, text kept readable (contrast checked).

## 7. Viewer (`static/script.js`)

- Progressive enhancement: without JS, each thumbnail is `<a href="…-2000.webp">`, opening the image.
- With JS: a click opens one shared `<dialog>` with the image (`srcset` with sizes `100vw`, so the browser picks 1400 or 2000), caption and "© Author". Previous/next buttons, arrow keys, swipe (pointer events, horizontal threshold), Esc and a close button. Focus moves to the dialog and back to the thumbnail on close. The large image loads only when opened; the next one is preloaded.
- `prefers-reduced-motion`: no transition.
- The URL hash records the open photo (`#photo-5`), so a link can point to one photo; Back closes the viewer.

## 8. Testing

- `pytest`:
  - build writes `_site/index.html`, `_site/torfa/index.html`, `_site/kverkfjoll/index.html`;
  - every `src`, `srcset` entry and local `href` in every built page resolves to an existing file in `_site/` (catches broken `../` prefixes);
  - each validation rule of 4.1, one failing fixture each;
  - `gallery_ref` slug rules (spaces, accents, upper case);
  - `watermark`: same size out as in, bottom-right corner changed, top-left untouched, works on portrait and landscape;
  - gallery output has no EXIF;
  - stale gallery files are removed.
- By hand: preview on laptop and phone; viewer with keyboard, swipe and without JS; Lighthouse mobile on home and one place page (90 or above); a check that no team member is shown in a gallery against their wishes (all 13 consented in 2026-11; new people in photos need the same consent rule).
- `GUIDE.md`: new section "Adding a photo to a place" (copy original into `EXPEDITION/photos/<place>/`, add the entry, `uv run prepare_images.py`, build, preview), plus the replaced-photo rule.

## 9. Out of scope

Lightbox zoom, download buttons, EXIF display, maps on the place pages, per-cave pages, Italian version, video in galleries.

## 10. Open items (block publishing, not building)

- Lorenzo checks every caption and alt text (sections 3 and 6), in particular the year of `p01-cover` (assumed 2026, from the brochure's "2026 cover" note), and that the lake in `P7171153` needs no name.
- The gas text needs Mattia Gerbaudo's agreement (as on brochure p12).
- When the full-size originals of `p01-cover`, `p05-recon`, `p06-lake`, `p08-cauldron`, `p08-sala-rosa` are available: copy them into `EXPEDITION/photos/<place>/`, change their `source:`, rerun `prepare_images.py`.
