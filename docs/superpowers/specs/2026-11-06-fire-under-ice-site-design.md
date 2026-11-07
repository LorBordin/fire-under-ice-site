# Fire Under Ice website: design

Date: 2026-11-06. Status: design approved in conversation, awaiting review of this document.

Source requirements: `~/expeditions/Iceland/brochure/2027/website_spec.md` (purpose, audience, sections, content rules, acceptance). This document records how we build it and the decisions taken on top of that spec. Where the two differ, this document wins.

Paths below are relative to `~/expeditions/Iceland/website/` unless stated. `BROCHURE` means `~/expeditions/Iceland/brochure/2027/`.

## 1. Goal and success criteria

One public page for the Fire Under Ice project (CSI, glaciovolcanic caves in Iceland, 2025-2027), in English, styled like the brochure.

- Primary reader: a sponsor's marketing contact arriving from the brochure QR on a phone, who must see in under a minute that the project is real, active and documented. Then cavers, talk attendees, press.
- Low maintenance: one update per expedition season, done by Lorenzo (Python background, no front-end experience).
- The work is also a learning exercise: every step is explained, and `GUIDE.md` lets Lorenzo update the site alone.

Success: the printed QR opens `https://fireunderice.org` on a phone over mobile data in a few seconds; all facts match the brochure; Lighthouse mobile performance and accessibility at 90 or above; Lorenzo can do a seasonal update following `GUIDE.md`.

## 2. Decisions

| Topic | Decision |
|---|---|
| Domain | `fireunderice.org`, registered at Cloudflare Registrar (8.50 USD first year, 11.20 USD renewal) |
| Repository | `lorbordin/fire-under-ice-site`, public, on Lorenzo's personal GitHub account |
| Temporary URL | `https://lorbordin.github.io/fire-under-ice-site/` until the domain is connected |
| Hosting | GitHub Pages, deployed by GitHub Actions, HTTPS enforced |
| Contact | `info@fireunderice.org`, inbox only, via Cloudflare Email Routing (free) forwarding to Lorenzo (and Andrea if wanted). No personal addresses, no phone numbers |
| Team | All 13 members entered now; each shown only once their consent is recorded (section 5.3) |
| Photos | Brochure set only in v1; gallery later |
| Motion | Subtle (section 7) |
| Build | Content in YAML + Jinja2 templates + Python build script (approach B) |
| Python tooling | uv (`pyproject.toml`, `uv.lock`, local `.venv/`) |
| Italian version | Later; not blocking v1 |

## 3. Architecture

```
website/
├── pyproject.toml              # deps: jinja2, pyyaml, pillow; dev group: pytest
├── uv.lock
├── content.yaml                # all text and data
├── templates/
│   ├── base.html               # <head>, nav, footer, includes each section
│   └── sections/               # hero, project, years, watch, science,
│                               # team, press, partners, contact (.html)
├── static/
│   ├── style.css
│   ├── script.js
│   ├── fonts/                  # Cabin woff2 (OFL), self-hosted
│   └── img/                    # generated web images (committed)
├── build.py                    # content.yaml + templates -> _site/
├── prepare_images.py           # BROCHURE originals -> static/img/*.webp
├── check_links.py              # manual: verify external links resolve
├── GUIDE.md                    # how it works + seasonal update checklist
├── .gitignore
├── .github/workflows/deploy.yml
└── docs/superpowers/specs/     # this document
```

Data flow: `content.yaml` -> `build.py` (validate, render with Jinja2) -> `_site/` (`index.html` + copy of `static/`) -> GitHub Pages.

- `_site/` is build output and is never committed.
- All asset links in HTML are relative (`static/img/...`, never `/static/...`) so the page works both on the `github.io/fire-under-ice-site/` subpath and on the custom domain root.
- Commands: `uv run build.py`; preview with `uv run python -m http.server -d _site 8000`; images with `uv run prepare_images.py`.

## 4. Page structure

One scrolling page with a sticky top nav (Project, Years, Science, Team, Contact), the active link highlighted. Sections, in order:

1. **Hero**: `p01-cover` full-viewport with dark gradient; "Fire Under Ice", subtitle and "2025-2027" from `BROCHURE/pages/01-cover.tex`; small CSI logo; scroll cue.
2. **The project**: 3-4 sentences condensed from `02-project.tex` and `03-why.tex`.
3. **Three years**: three cards (2025 Recon, Kverkfjöll; 2026 Discovery, Freyja Hellir and Torfa; 2027 Expansion, Torfajökull + recon), photo + two lines each, from `04`-`10`. Below: 2006 vs 2025 before/after slider (from `f4_2006_vs_2025.jpg`, split into its two halves by `prepare_images.py`) and the Iceland map (`f2_iceland_map.pdf` rasterised to WebP).
4. **Watch**: click-to-load YouTube video (`913rFrz9-xo`). Shows a locally stored thumbnail with a play button; on click, JS swaps in a `youtube-nocookie.com` iframe. Without JS the button is a plain link to YouTube.
5. **Science**: microbiology (University of Milano-Bicocca), monitoring (team led by Lee J. Florea, PhD, Christian Stenner and Linda Sobolewski, PhD, University of Iceland), photogrammetry (`f7_3d`, `f7_ortho`). From `09-science.tex`.
6. **Team**: CSI logo, name and two-sentence origin blurb (website_spec section "About CSI"); then four groups as in `13-team.tex`, alphabetical by surname, photo + name + one line. Consented members only.
7. **Press and talks**: articles, talks, TG5 report link, from `14-partners.tex`.
8. **Partners and sponsors**: logo row: SSI, Regione FVG, CAI, Società Geografica Italiana (`soc_geo_logo_crop.png`), Gaibana (`gaibana_logo.png`). Sponsors added once confirmed. The CSI logo never appears here.
9. **Contact + footer**: `info@fireunderice.org` (mailto); CSI logo; credits: "Original artwork by Lee Florea", surveys by Cristian Monticone, basemap "Landmælingar Íslands, IS 50V, CC BY 4.0".

Copy is condensed from the brochure, never invented. Content rules of `website_spec.md` section 4 apply in full (spelling, forbidden phrases, Swiss not French, no rival-brand logos near sponsors).

## 5. Content model (`content.yaml`)

### 5.1 Shape

```yaml
site:
  title: Fire Under Ice
  url: https://fireunderice.org
  description: ...            # meta description / link previews
  contact_email: info@fireunderice.org
hero: {title, subtitle, years, image, image_alt}
project: {kicker, title, paragraphs: [...]}
years:
  - {year: 2025, label: Recon, place: Kverkfjöll, text, image, image_alt}
  - ...
comparison: {before, before_alt, after, after_alt, caption}
map: {image, image_alt, caption}
video: {youtube_id: 913rFrz9-xo, title, thumbnail, thumbnail_alt}
science:
  - {title, text, image?, image_alt?}
csi: {name, logo, blurb: [two sentences]}
team:
  - group: Core team
    members:
      - {name, line, photo, consent: false}
press:
  articles: [{year, title, byline, url?}]   # byline: authors + outlet, as in brochure p14
  talks: [{year, venue, place, title}]
  tv: [{title, outlet, url}]
partners:
  - {name, logo, url?, consent: true}
sponsors: []                  # same shape as partners
credits: [...]
```

Text fields may contain `*italic*` (rendered as `<em>`); everything else is HTML-escaped by Jinja2 autoescaping.

### 5.2 Validation in `build.py` (build fails, nothing is published)

- any value containing `TODO`;
- a required field missing (per section above);
- an image path that does not exist under `static/`;
- an image without non-empty alt text (team photos use the member name);
- a forbidden phrase from the content rules ("heart of Europe", "2000 MW", "Kinetic Trigger", "extremophile"), case-insensitive.

Errors are listed all at once with their YAML location, then exit code 1.

### 5.3 Consent

Every team member, partner and sponsor has `consent: true|false`. Only `true` entries are rendered; `build.py` prints the names it skipped. Initial values: team all `false`; partners SSI, FVG, CAI, SGI, Gaibana `true`. A team group with no consented members is not rendered; if no member is consented, the team section shows only the CSI blurb.

Unknown facts not in the brochure are entered as `TODO` and must be resolved by Lorenzo before publishing (5.2 enforces this).

## 6. Look

- CSS variables: `--bg #0D0D0D`, `--ice #00C2FF` (headings), `--magma #FF4500` (accents), `--text #FFFFFF`, plus a muted grey for secondary text checked to AA (4.5:1) on `--bg`.
- Font: Cabin (regular, italic, semibold, bold), woff2, self-hosted, `font-display: swap`, regular weight preloaded.
- Full-bleed photos with dark gradient fades; brochure-style uppercase kicker above section titles.
- Mobile-first CSS: base rules for phones, `min-width` media queries for wider screens (years and science cards side by side, team in columns).
- No third-party requests on page load (fonts, images, thumbnail all local). The only third-party request is the YouTube player after a click.

## 7. Motion (progressive enhancement)

`script.js` (plain JS, no libraries, ~100 lines) adds class `js` to `<html>`; CSS hides animatable elements only under `.js`, so with JS off everything is visible.

- Reveal on scroll: `IntersectionObserver` adds `.visible` to sections (fade + small rise).
- Hero parallax: hero image translates at a fraction of scroll speed (`requestAnimationFrame`, transform only).
- Nav: `IntersectionObserver` sets `aria-current` on the link of the section in view.
- Before/after slider: `<input type="range">` drives a CSS `clip-path` on the top image; without JS both images are shown stacked with labels.
- Click-to-load video (section 4).
- `prefers-reduced-motion: reduce` disables reveal, parallax and smooth scrolling.

## 8. Images

`prepare_images.py` (Pillow) reads originals from `BROCHURE` and writes to `static/img/`:

- photos and composites: WebP, widths 800 / 1400 / 2000 (never upscaled), quality ~78; used with `srcset` + `sizes`;
- team photos: square 400 px WebP;
- logos: PNG/WebP resized to display height x2, transparency kept;
- `f2_iceland_map.pdf`: rasterised (via ImageMagick `magick`, available locally) to WebP;
- `f4_2006_vs_2025.jpg`: split into two images for the slider;
- YouTube thumbnail: downloaded once, converted to WebP.

The script is a list of (source, output, kind) entries at the top, so adding a photo is one line. It is run by hand when images change; its outputs are committed. Expected total: about 3 MB.

Rules: originals never enter the repository; `.gitignore` excludes `_site/`, `.venv/`, `*.jpg`, `*.JPG`, `*.jpeg` (all web images are WebP or PNG), `*.tif*`, `*.raw`, `*.cr2`, `*.nef`, `*.dng`, `*.mp4`, `*.mov`, `*.pdf`. Below-the-fold images use `loading="lazy"`; the hero uses `fetchpriority="high"`. Width and height attributes are set on every `<img>` to avoid layout shift.

## 9. Deployment

`.github/workflows/deploy.yml`, triggered on push to `main` and manually:

1. checkout;
2. `astral-sh/setup-uv` (pinned major version);
3. `uv sync --frozen` (exact versions from `uv.lock`; dev group not needed);
4. `uv run build.py`;
5. `actions/upload-pages-artifact` with `_site/`;
6. `actions/deploy-pages`.

Permissions: `pages: write`, `id-token: write`, `contents: read`. A failed build leaves the previous version online. The custom domain is set in the repository's Pages settings (no `CNAME` file needed with Actions deployment).

## 10. Publishing stages (Lorenzo does account and payment steps; each step is explained)

1. **Machine**: install uv; `git config --global user.name/user.email`; create an ed25519 SSH key and add the public key to GitHub; first commit (this spec) made by Lorenzo.
2. **GitHub**: create public repo `fire-under-ice-site`; Settings > Pages > Source: GitHub Actions.
3. **First publish**: push; follow the Actions run; site live at the temporary URL.
4. **Domain**: buy `fireunderice.org` at Cloudflare; DNS: `A` records to 185.199.108.153, .109.153, .110.153, .111.153, `AAAA` to 2606:50c0:8000::153, 8001::153, 8002::153, 8003::153, `CNAME www -> lorbordin.github.io`, all "DNS only" (grey cloud); verify the domain in GitHub account settings (`TXT` record); set the custom domain in Pages settings; enable Enforce HTTPS once the certificate is issued. (IP addresses to be re-checked against GitHub's docs at that time.)
5. **Email**: Cloudflare Email Routing, `info@` forwarding to verified destination addresses.
6. **Brochure** (website_spec section 7): set `\expeditionurl` and `\urlconfirmedtrue` in `BROCHURE/style/brochure.sty`, adjust page 16 QR label, rebuild with `make all && make check`, scan the QR from a printed page.

## 11. Testing

- `build.py` validation (5.2) on every local build and in Actions.
- `check_links.py`, run by hand: HTTP status of every external URL in `content.yaml` (YouTube, TG5, partner sites).
- Local preview on desktop and on Lorenzo's phone over the LAN.
- HTML validity: W3C validator on the built page once.
- Lighthouse (Chrome DevTools, mobile): performance and accessibility at 90 or above.
- Without JS (DevTools > disable JavaScript): all content visible, slider stacked, video link works.
- Final acceptance per website_spec section 9, including the printed QR scan.

## 12. Out of scope for v1

Blog, CMS, contact form, newsletter, analytics, gallery (lifted in v2, see `2026-11-07-places-galleries-design.md`), interactive map, 3D viewer, Italian version, sending mail as `info@`.

## 13. Open items (do not block building, block going public where noted)

- Team consent: ask all 13 members; flip `consent` as answers arrive (blocks showing each member).
- Facts missing from the brochure: entered as `TODO`, answered by Lorenzo (blocks build).
- Whether Andrea also receives `info@` mail.
