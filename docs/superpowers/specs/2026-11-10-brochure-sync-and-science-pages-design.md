# Brochure 2027 sync and science pages: design

Date: 2026-11-10 · Status: approved in conversation, awaiting spec review

## 1. Goal

Two independent parts, shipped in this order:

- **Part A: brochure sync.** Bring fireunderice.org in line with the revised 2027 brochure
  (`~/expeditions/Iceland/brochure/2027`, see `changes.md`): new text, the new "Why research
  here" content, the paper in press, the 2027 patronage mark, and the new photos in `new_pics/`.
- **Part B: science pages.** Two new long-read pages, `/microbiology/` and `/analogues/`,
  drafted by Claude from the team's own documents and the published literature, and published only
  after review.

Success: Part A is live and matches the brochure; Part B pages exist as reviewed drafts behind a gate
that never blocks a deploy; Lorenzo can publish a page by flipping one flag.

### What the user said vs. what is assumed

- Said: update the site with the new brochure and photos; plan new "sessions" (sections) on
  microbiology (micro-organisms in extreme, lightless environments) and planetary analogues.
- Said: Claude drafts the science, the team checks it. Own pages plus a home-page teaser.
  Reviewers: Paolo Turrini then Prof. Andrea Franzetti for microbiology; Lorenzo for analogues.
- Assumed: the site's rule stands: facts come from the brochure, team documents or cited
  literature; nothing unverified is published.
- Not carried over: sponsor-specific brochure pages (p12 gear variants, p15 asks).

## 2. Part A: brochure sync

| Site area | Change | Brochure |
|---|---|---|
| `project.stats` | "1984–2026" gets `*`; note below: "*Surveys up to 2008 by Gérald Favre's Swiss team; ours start in 2025." | p2 |
| Science (home) | New "Why research here / Where ice meets magma" block, 4 items (texts verbatim from p8c): Ice and volcanoes, A changing climate, Jökulhlaups, Other worlds. Photos `sampling_1`, `sampling_2`. | p8c |
| Torfa place | Add `torfa_entrance_andrea` (becomes `cover`), `sala_graal`, `waterfall_torfa_cave`, `torfa_final_stream`, `ingresso_torfa_jerba`. The previous cover `P7110912` stays in the gallery. | p8b, p14, p14b |
| Kverkfjöll place | Add `lazzaro_mask_calderone` (Encelado cauldron). | p11b |
| `field` | "Air you cannot trust": text from p11b (5 % CO₂ vs the 4 % NIOSH IDLH threshold; ABEKP filters do not stop CO₂, CO or low oxygen; any alarm, we leave); image `lazzaro_mask_calderone`. "Rotten ice": image `descent.jpg`. Both replaced images are already in the Kverkfjöll gallery, so nothing is lost. | p11b, p12 |
| `press.articles` | New first entry: 2027, "Freyja Hellir: magia tra ghiaccio e riolite (Islanda)", Benassi A., Bordin L., Monticone C., Gerbaudo M., Turrini P. · *Speleologia*, issue 95, March 2027, `status: in press`. | p14b |
| Press section | Two photos from the Costacciaro national gathering, October 2026: `people.JPG` (full hall), `presentazione_2.JPG` (talk). | p14b |
| `partners` | `patron_2027: true` on all except Gaibana; star before the name; note "Patronage being sought for 2027". | p14 |

Photo credits (watermark and footer):

| Photo | Author |
|---|---|
| `descent.jpg` | Lorenzo Bordin |
| `ingresso_torfa_jerba.jpg`, `lazzaro_mask_calderone.JPG`, `sala_graal.jpg`, `waterfall_torfa_cave.JPG` | Andrea Benassi |
| `sampling_1.JPG`, `sampling_2.jpg`, `torfa_entrance_andrea.jpg`, `torfa_final_stream.JPG` | Cristian Monticone |
| `people.JPG`, `presentazione_1.JPG`, `presentazione_2.JPG` | Paolo Testa |

Originals are copied from `brochure/2027/new_pics/` to `~/expeditions/Iceland/photos/<place>/`
(gallery photos) or `photos/science/` (sampling photos), following the existing "originals outside the
repo" rule. Captions and alt text are written from the brochure captions and the photos themselves.

## 3. Part B: science pages

### 3.1 Content

Sources: own facts from `~/expeditions/Iceland/2026/docs/riassunto_per_sgi.pdf` (SGI summary) and
`Vatnajokull_2026_Italian_team_note.pdf`; general science from the SGI summary's bibliography plus
primary sources checked while drafting. Every factual claim carries a reference (with DOI where one
exists). Plain English, the site's style: short sentences, no hype.

**`/microbiology/`: Life without light** (reviewers: Paolo Turrini, then Prof. Franzetti)

1. *Dark, poor, volcanic.* DOVE (dark oligotrophic volcanic environments): no sunlight, so life
   runs on chemical energy (chemolithoautotrophy) from H₂S, H₂, CH₄, CO₂. Gradients from
   fumaroles up to 94.5 °C to air at 1–4 °C and ice put thermophiles, acidophiles and psychrophiles
   side by side. Only one comparable sulfidic glaciovolcanic cave studied: Mount Meager (Clance et
   al. 2024). Context: Erebus (Connell & Staudigel 2013), Kverkfjöll hot spring (Cousins et al. 2018).
2. *What we sampled in 2026.* Kverkfjöll: sediment in triplicate along the thermal gradient from
   fumaroles; rims of boiling pools; biofilm on ventilated ice walls; hot water from a methane-rich
   fumarole pool; the ~74 °C spring at the bottom of Encelado. Torfa, Freyja Hellir: soft coloured
   microbial mats; snottites at an acidic H₂S fumarole (outside the cave); filamentous communities
   along a thermal stream. Collected under agreement with Vatnajökull National Park.
3. *What comes next.* Sequencing and metagenomics with Prof. Andrea Franzetti (Università di
   Milano-Bicocca); Paolo Turrini is the team's sampling referent. Why it matters: early life,
   astrobiology, enzymes stable under extreme conditions.
4. *In 2027.* Plans to be supplied by Paolo Turrini (a TODO until then).

**`/analogues/`: Other worlds on Earth** (reviewer: Lorenzo Bordin)

1. *Ice over heat, elsewhere.* Enceladus (namesake of the Encelado cauldron): subsurface ocean and
   signs of hydrothermal activity from Cassini; Europa; volcano–ice interaction on Mars (Cousins &
   Crawford 2011; Cousins et al. 2013).
2. *What carries over, and what doesn't.* Carries over: darkness, cold, chemical energy, ice cover,
   how biosignatures and minerals are preserved and detected. Doesn't: oxygen atmosphere,
   pressure, radiation, gravity.
3. *Caves on other worlds.* Fumarolic ice caves as models for icy voids (Curtis 2020; Mount St.
   Helens, Davis et al. 2020).
4. *What we add.* Surveys, temperature and gas readings, samples, 2027 lidar: field data others can
   use. Framed as a contribution, not as our own planetary research.

Each page also gets a plain-text reviewer copy (`docs/review/<slug>.md`): the full text with one
reference per claim, for the reviewers to annotate.

### 3.2 Review gate

- `topics[].reviewed` (must be exactly `true`, like `consent`) and `topics[].reviewers` (free text,
  never rendered).
- Unreviewed topics are removed by `filter_consented` before rendering: no page, no menu link, no
  teaser card, no link from "Why research here".
- `validate` skips the TODO check inside unreviewed topics, so drafts never block a deploy. Reviewed
  topics get the full check (TODO, alt text, images).
- Publishing a page = set `reviewed: true`, build, push.

## 4. Implementation

### 4.1 Content model (`content.yaml`)

```yaml
science_why:                      # brochure p8c
  kicker: Why research here
  title: Where ice meets magma
  items:
    - {title: Ice and volcanoes, text: "...", topic: null}
    - {title: Other worlds, text: "...", topic: analogues}
  photos: [{image: img/why-sampling-1, image_alt: "...", credit: Cristian Monticone}, ...]

topics:
  - slug: microbiology
    kicker: Science
    title: Life without light
    teaser: "..."
    intro: ["..."]
    chapters:
      - heading: Dark, poor, volcanic
        paragraphs: ["..."]
        photo: {source: photos/science/sampling_1.JPG, author: Cristian Monticone, caption: "...", alt: "..."}
    references:
      - {text: "Clance, J. J., et al. (2024). ... Frontiers in Geochemistry, 2, 1410338.", url: "https://doi.org/..."}
    reviewers: Paolo Turrini, then Prof. Andrea Franzetti
    reviewed: false
```

Also: `project.stats[].note` (text after the stats, keyed by `*`), `press.articles[].status`,
`press.photos` (two images with credit), `partners[].patron_2027`, `headings.partners.patron_note`.
A topic slug must not clash with a place slug (validated).

### 4.2 Code

- `sitelib.py`: `filter_consented` drops unreviewed topics and strips `topic:` links to them from
  `science_why`; `validate` gains `_validate_topics` (required fields, alt, author, slug clash,
  images) and skips TODO inside unreviewed topics; `gallery_ref` reused for topic photos.
- `build.py`: renders `templates/topic.html` per published topic at `<slug>/index.html`
  (`root="../"`); `photo_authors` includes topic photos and `science_why` / press photo credits.
- `prepare_images.py`: watermarked topic photos from `content.yaml` (same path as galleries); `JOBS`
  lines for `science_why` and press photos.
- Templates: new `topic.html`; `sections/science.html` gains the "Why research here" block and
  topic teaser cards; `layout.html` menu shows "Research" only if a topic is published;
  `sections/press.html` shows status and photos; `sections/partners.html` shows the star and note;
  `sections/project.html` shows the stats note.
- `static/style.css`: topic page (readable measure, chapter photos, reference list), why-block,
  star.
- `GUIDE.md`: new "Science pages" section (edit, review, publish).

### 4.3 Testing

TDD with pytest, alongside the existing suite:

- An unreviewed topic is not rendered and not linked, and a TODO inside it does not fail the build.
- A reviewed topic renders at `/<slug>/`, and a TODO inside it fails the build.
- Topic validation errors: missing alt, missing author, slug clashing with a place.
- `science_why` links appear only for published topics.
- The patron star, the "in press" label and the stats note render.
- The full suite and `check_links.py` on the built site pass; visual check of the home page, the Torfa
  page and both topic pages (temporarily reviewed) at phone and desktop width.

### 4.4 Order of work

1. Part A (content and template changes, photos). Shippable alone.
2. Topic machinery, behind the review gate (no topics yet, or drafts unpublished).
3. Draft both pages and the reviewer copies; hand over for review.
