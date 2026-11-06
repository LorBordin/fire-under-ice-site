# Fire Under Ice website: guide

How this site works and how to update it. Written for Lorenzo; no web experience assumed.

Live site: <https://fireunderice.org> · Repository: <https://github.com/lorbordin/fire-under-ice-site>

## 1. How it works

```
content.yaml ─┐
templates/  ──┼─> build.py ──> _site/index.html + _site/static/ ──> GitHub Pages ──> fireunderice.org
static/     ──┘   (checks, then fills the templates)    (git push triggers GitHub Actions)
```

| File / folder | What it is | Do you edit it? |
|---|---|---|
| `content.yaml` | **All the text** on the page, plus image paths and consent flags | Yes, every season |
| `templates/` | The HTML skeleton, one file per section (Jinja2: HTML with `{{ gaps }}`) | Rarely |
| `static/style.css` | The look: colours, fonts, layout | Rarely |
| `static/script.js` | The motion: fade-ins, slider, video. The page works without it | Rarely |
| `static/img/` | Web-sized images, **generated**: never edit by hand | No (scripts write it) |
| `prepare_images.py` | Turns brochure originals into web images (`JOBS` list at the top) | Add a line per new photo |
| `make_comparison.py` | Builds the 2006 vs 2025 slider images from the KML + orthophoto | Only if surveys change |
| `make_model.py`, `geo.py` | Builds the interactive 3D model (`static/model/*.glb`) from the ODM OBJ, and prints the cave marker position | Only for a new model |
| `static/vendor/` | `<model-viewer>` 4.0.0 (Google, Apache-2.0), the 3D viewer, kept here so no other server is contacted | No |
| `build.py`, `sitelib.py` | The generator: load, validate, filter consent, render | No |
| `check_links.py` | Checks that external links (YouTube, TG5, …) still work | No, just run it |
| `tests/` | Automatic checks of the generator (`uv run pytest`) | No |
| `.github/workflows/deploy.yml` | Instructions for GitHub: test, build, publish on every push | No |
| `_site/` | Build output. Not in git; recreated by every build | No |

**The safety nets.** `build.py` refuses to build (and so GitHub refuses to publish) if `content.yaml` has:
a `TODO`, a missing required field, an image file that doesn't exist, an image without alt text, or a forbidden phrase
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
| `uv run prepare_images.py` | Regenerate web images from the brochure originals |
| `uv run check_links.py` | Check external links (some sites block robots: open those by hand) |
| `uv run --group model make_model.py` | Rebuild the 3D model (~30 s; installs pymeshlab the first time). Paste the printed `model_marker` into `content.yaml` |
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
   `("responsive", "figures/photos/p05-recon.jpg", "p05-recon"),` and run `uv run prepare_images.py`.
   Check each photo for rival-brand logos if a sponsor's gear is in the season.
2. **Text.** Edit `content.yaml`: the new year in `years:`, figures in `project.stats`, new articles and talks in `press:`.
   Facts come from the brochure or from you, never guessed; unknown means `TODO` until you know.
3. **People.** New team members: add them with `consent: false`, switch to `true` once they agree. Each needs a
   `role:` (their job in the expedition, shown in red) and a `line:` (short bio). Team photos go through
   the `square` job in `prepare_images.py` (400×400).
4. **Check.** `uv run build.py`, preview on laptop and phone, `uv run check_links.py`.
5. **Publish.** Commit and push (section 3). Open <https://fireunderice.org> on your phone to confirm.

### Adding a sponsor

1. Get the sponsor's agreement and logo (PNG with transparency, or SVG exported to PNG).
2. Add a `logo` job: `("logo", "logos/brand.png", "logos/brand.png"),` and run `uv run prepare_images.py`.
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
