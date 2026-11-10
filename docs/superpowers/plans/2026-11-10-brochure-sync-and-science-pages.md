# Brochure 2027 sync and science pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring fireunderice.org in line with the revised 2027 brochure, and add two science pages (`/microbiology/`, `/analogues/`) that stay hidden until reviewed.

**Architecture:** Everything is driven by `content.yaml`. Part A adds a few optional keys (stat notes, article status, press photos, patron flag, `science_why`) and their template output. Part B adds a `topics:` list rendered like places (one page per topic via `templates/topic.html`), gated by `reviewed: true` in `sitelib.filter_consented`; drafts skip the TODO check so they never block a deploy.

**Tech Stack:** Python 3 (uv), Jinja2, PyYAML, Pillow, pytest. Static site to GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-11-10-brochure-sync-and-science-pages-design.md`

## Global Constraints

- Facts come from the brochure (`~/expeditions/Iceland/brochure/2027/pages`), the team documents (`~/expeditions/Iceland/2026/docs/riassunto_per_sgi.pdf`, `Vatnajokull_2026_Italian_team_note.pdf`) or cited literature. Nothing invented.
- Originals never enter the repo. Copy them from `~/expeditions/Iceland/brochure/2027/new_pics/` to `~/expeditions/Iceland/photos/{torfa,kverkfjoll,science,press}/`; reference them in `content.yaml` relative to `~/expeditions/Iceland/`.
- Forbidden phrases stay as they are (`FORBIDDEN` in `sitelib.py`, including "extremophile"), and they are checked in drafts too. Drafts name thermophiles, acidophiles and psychrophiles instead.
- Visibility flags count only when exactly YAML `true` (`consent`, `reviewed`, `patron_2027`).
- Photo credits: `descent.jpg` Lorenzo Bordin; `ingresso_torfa_jerba.jpg`, `lazzaro_mask_calderone.JPG`, `sala_graal.jpg`, `waterfall_torfa_cave.JPG` Andrea Benassi; `sampling_1.JPG`, `sampling_2.jpg`, `torfa_entrance_andrea.jpg`, `torfa_final_stream.JPG` Cristian Monticone; `people.JPG`, `presentazione_*.JPG` Paolo Testa.
- Reviewers: microbiology "Paolo Turrini, then Prof. Andrea Franzetti"; analogues "Lorenzo Bordin".
- Commands: tests `uv run pytest -q`; images `uv run prepare_images.py`; build `uv run build.py`; links `uv run check_links.py`.

## Review Focus

1. `reviewed: "true"` (a quoted string), `yes` in quotes, or a typo such as `reviwed: true`: the topic must stay hidden. Test in Task 6.
2. Text from an unreviewed draft leaking into a built page (home teaser, menu, "Why research here" link, footer credits): none of it should appear anywhere in `_site`. Test in Task 7.
3. A `science_why` item whose `topic:` names a slug that is unpublished or misspelt: the item renders as plain text, with no dead link. Test in Task 7.
4. Images of an unreviewed topic: they must not be flagged as "unused gallery files", which would block the build. Deleting a topic must clean its folder. Tests in Tasks 6 and 8.
5. A topic slug equal to a place slug, which would make both pages write `<slug>/index.html`: validation error. Test in Task 6.

---

### Task 1: Stat footnote

**Files:**
- Modify: `templates/sections/project.html`, `content.yaml` (`project.stats`), `static/style.css`
- Test: `tests/test_build.py`

**Interfaces:**
- Produces: optional `project.stats[].note` (string).

- [ ] **Step 1: Write the failing test** `test_stat_note`. In `minimal_content()`, set `project.stats = [{"value": "1984–2026", "label": "survey record", "note": "Surveys up to 2008 by others."}]`, then build. Assert `"1984–2026*"` is in the HTML once tags are stripped (`re.sub(r"<[^>]+>", "", html)`), and that `'<p class="note stats-note">* Surveys up to 2008 by others.</p>'` is in the HTML.
- [ ] **Step 2: Run** `uv run pytest tests/test_build.py::test_stat_note -v`. Expected: FAIL.
- [ ] **Step 3: Implement.** In `project.html`, the n-th stat that has a note gets `"*" * n` appended after its value (inside `<strong>`), and after the `<ul class="stats">` one `<p class="note stats-note">{{ stars }} {{ note | md }}</p>` per note, in the same order. In `content.yaml`, the "1984–2026" stat gets `note: Surveys up to 2008 by Gérald Favre's Swiss team; ours start in 2025.` Add CSS: `.stats-note` uses the same style as `.note`.
- [ ] **Step 4: Run** `uv run pytest -q`. Expected: all pass.
- [ ] **Step 5: Commit** `feat: footnote on the survey-record stat`.

### Task 2: Press, in-press status and talk photos

**Files:**
- Modify: `templates/sections/press.html`, `sitelib.py` (`REQUIRED`), `build.py` (`photo_authors`), `prepare_images.py` (`JOBS`), `content.yaml` (`press`), `static/style.css`
- Test: `tests/test_build.py`, `tests/test_sitelib.py`

**Interfaces:**
- Produces: optional `press.articles[].status` (string), optional `press.photos: [{image, image_alt, caption, credit}]`. `REQUIRED["press.photos"] = ["image", "image_alt", "caption", "credit"]`.

- [ ] **Step 1: Write the failing tests.**
  - `test_article_status`: the article has `status: "in press"`. Assert `'<span class="status">in press</span>'` is in the HTML.
  - `test_press_photos`: `press.photos = [{"image": "img/a", "image_alt": "Hall", "caption": "Costacciaro.", "credit": "Paolo Testa"}]`. Assert the `<img` has `alt="Hall"`, and that "Costacciaro." and "Paolo Testa" appear in the press section and the footer credits.
  - `test_press_photo_needs_credit` (test_sitelib): with `credit` removed, `validate` contains `"press.photos[0].credit: missing"`.
- [ ] **Step 2: Run** these three tests. Expected: FAIL.
- [ ] **Step 3: Implement.**
  - Status: a `<span class="status">` after the meta of an article.
  - Photos: `<div class="press-photos">` after Talks. Each photo is a `<figure>` with `image(...)` and `<figcaption>{{ caption }} © {{ credit }}</figcaption>`.
  - `photo_authors`: add the press photo credits.
  - `JOBS`: add `("responsive", "photos/press/people.JPG", "press-hall")` and `("responsive", "photos/press/presentazione_2.JPG", "press-talk")`.
- [ ] **Step 4: Content.**
  - Copy `people.JPG` and `presentazione_2.JPG` to `~/expeditions/Iceland/photos/press/`.
  - Add a new first article: `{year: 2027, title: "Freyja Hellir: magia tra ghiaccio e riolite (Islanda)", byline: "Benassi A., Bordin L., Monticone C., Gerbaudo M., Turrini P. · *Speleologia*, issue 95, March 2027", status: in press}`.
  - Add `press.photos`, both with caption "National speleology gathering, Costacciaro, October 2026." and credit Paolo Testa. Alts: "A packed hall of people listening to a talk under a white tent roof." and "Two speakers in front of a large screen showing a glacier photo, at a talk under a tent."
  - Run `uv run prepare_images.py`.
- [ ] **Step 5: Run** `uv run pytest -q && uv run build.py`. Expected: all pass, then "Built …".
- [ ] **Step 6: Commit** `feat: press in-press status and talk photos`.

### Task 3: Partners, 2027 patronage star

**Files:**
- Modify: `templates/sections/partners.html`, `sitelib.py` (`REQUIRED["headings.partners"]` unchanged; `patron_note` optional), `content.yaml`, `static/style.css`
- Test: `tests/test_build.py`

**Interfaces:**
- Produces: optional `partners[].patron_2027: true` and `headings.partners.patron_note` (string).

- [ ] **Step 1: Write the failing tests.**
  - `test_patron_star`: two partners, one with `patron_2027: True`, and `headings.partners.patron_note = "Patronage being sought for 2027"`. Assert exactly one `class="patron-star"` and that the note text appears.
  - `test_patron_star_exactly_true`: `patron_2027: "true"` gives no star. With no patron partner, the note is absent.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement.**
  - In the `logos` macro: `{% if p.patron_2027 is sameas true %}<span class="patron-star" aria-hidden="true">★</span><span class="visually-hidden">(patronage being sought for 2027)</span>{% endif %}` inside the `<li>`. Add a `.visually-hidden` CSS rule if none exists (check `style.css` first).
  - After the partner logos: `<p class="note">★ {{ patron_note }}</p>`, shown only when the note is defined and at least one partner has the flag.
  - CSS: star in the accent red, at the top-left corner of the logo cell.
- [ ] **Step 4: Content.** Set `patron_2027: true` on every partner except Gaibana, and add `headings.partners.patron_note: Patronage being sought for 2027`.
- [ ] **Step 5: Run** `uv run pytest -q`. Expected: all pass.
- [ ] **Step 6: Commit** `feat: mark partners whose 2027 patronage is sought`.

### Task 4: New photos in the galleries and In the field

No code change. This task is content and images only.

**Files:**
- Modify: `content.yaml` (`places`, `field`), `prepare_images.py` (`JOBS`)
- Delete: `static/img/field-rope-*.webp`

- [ ] **Step 1: Copy originals.**
  - To `~/expeditions/Iceland/photos/torfa/`: `torfa_entrance_andrea.jpg`, `ingresso_torfa_jerba.jpg`, `sala_graal.jpg`, `waterfall_torfa_cave.JPG`, `torfa_final_stream.JPG`, `descent.jpg`.
  - To `photos/kverkfjoll/`: `lazzaro_mask_calderone.JPG`.
  - To `photos/science/`: `sampling_1.JPG`, `sampling_2.jpg`.
- [ ] **Step 2: Torfa gallery.** Remove `cover: true` from `P7110912.JPG`. Add these photos (the `featured` photos stay as they are):

  | source | author | caption | alt | flag |
  |---|---|---|---|---|
  | photos/torfa/torfa_entrance_andrea.jpg | Cristian Monticone | Entrance, Freyja Hellir, July 2026. | A caver stands small at the bottom of a tall ice passage whose ceiling glows turquoise. | cover |
  | photos/torfa/ingresso_torfa_jerba.jpg | Andrea Benassi | Entrance gallery, Freyja Hellir, July 2026. | A caver with a headlamp climbs dark ground under a ribbed ice tunnel that opens to daylight. | |
  | photos/torfa/sala_graal.jpg | Andrea Benassi | Sala del Graal, Freyja Hellir, July 2026. | Two cavers, in yellow and red, on a dark mound under a vast scalloped ice ceiling, an orange stream below. | |
  | photos/torfa/waterfall_torfa_cave.JPG | Andrea Benassi | Waterfall inside the ice, Freyja Hellir, July 2026. | Water falls from a hole in a scalloped ice ceiling onto rocks where two cavers crouch with lights. | |
  | photos/torfa/torfa_final_stream.JPG | Cristian Monticone | A stream through the ice, Freyja Hellir, July 2026. | A caver in yellow walks beside a stream along a long round ice tunnel, orange sediment on the right. | |

- [ ] **Step 3: Kverkfjöll gallery.** Add `photos/kverkfjoll/lazzaro_mask_calderone.JPG`, author Andrea Benassi, caption "A boiling vent in a cauldron, Kverkfjöll, July 2026.", alt "A caver in a helmet and respirator points at a boiling vent in thick steam."
- [ ] **Step 4: In the field.**
  - "Air you cannot trust": new text "Cavities under the ice trap CO₂, H₂S and SO₂. In Freyja Hellir the detector alarmed at 5 % CO₂, above the 4 % NIOSH lists as immediately dangerous, and we turned back. We monitor gas continuously. Full-face respirators with ABEKP filters are a safety layer only: they do not stop CO₂, CO or low oxygen. Any alarm, we leave." Same `img/field-gas` and credit; new alt "A caver in a helmet and respirator points at a boiling vent in thick steam." Delete the YAML comment about waiting for Mattia's agreement (brochure p11b is reviewed).
  - "Rotten ice": `image: img/field-descent`, alt "A caver hangs on a rope inside a deep shaft in white glacier ice.", credit Lorenzo Bordin.
- [ ] **Step 5: JOBS.**
  - Change the `field-gas` source to `photos/kverkfjoll/lazzaro_mask_calderone.JPG`.
  - Replace the `field-rope` line with `("responsive", "photos/torfa/descent.jpg", "field-descent")`.
  - Delete `static/img/field-rope-*.webp`.
  - Run `uv run prepare_images.py`. Expected: no WARNING lines, and new files under `static/img/places/torfa/` and `kverkfjoll/`.
- [ ] **Step 6: Run** `uv run pytest -q && uv run build.py`. Expected: pass, then "Built …". Validation enforces one cover and three featured photos per place.
- [ ] **Step 7: Commit** `content: brochure 2027 photos in galleries and In the field` (generated images included).

### Task 5: "Why research here" block

**Files:**
- Modify: `sitelib.py` (`REQUIRED`, `OPTIONAL_SECTIONS`), `templates/sections/science.html`, `build.py` (`photo_authors`), `prepare_images.py` (`JOBS`), `content.yaml`, `static/style.css`
- Test: `tests/test_build.py`, `tests/test_sitelib.py`

**Interfaces:**
- Produces: optional top-level `science_why: {kicker, title, items: [{title, text, topic?}], photos: [{image, image_alt, credit}]}`.
  - `REQUIRED`: `"science_why": ["kicker", "title", "items"]`, `"science_why.items": ["title", "text"]`, `"science_why.photos": ["image", "image_alt", "credit"]`.
  - `"science_why"` is added to `OPTIONAL_SECTIONS`.
  - `item.topic` (a topic slug) renders as a link to `{{ root }}{{ topic }}/`. Task 6 strips the `topic` key from any item whose topic is not published, so the template just checks `item.topic is defined`.

- [ ] **Step 1: Write the failing tests.**
  - `test_science_why_block`: two items, one with `topic: "analogues"`, plus one photo. Assert `id="why"`, both titles, `href="analogues/"`, and the credit in the footer.
  - `test_science_why_optional`: without `science_why`, the build passes and there is no `id="why"`.
  - `test_science_why_item_needs_text` (sitelib): validation reports `science_why.items[0].text: missing`.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement.**
  - In `science.html`, before the cards, when `c.get("science_why")` is set: `<div class="why" id="why">` with an `<h3>` kicker and title, a `<dl>` or list of items (the title becomes a link when `topic` is defined), and the photos side by side.
  - `photo_authors`: add the `science_why.photos` credits.
  - `JOBS`: `("responsive", "photos/science/sampling_1.JPG", "why-sampling-1")` and `("responsive", "photos/science/sampling_2.jpg", "why-sampling-2")`.
- [ ] **Step 4: Content** (texts verbatim from brochure p8c). `kicker: Why research here`, `title: Where ice meets magma`. Items:
  - Ice and volcanoes: "How geothermal heat and glaciers reshape each other, seen from inside."
  - A changing climate: "Field data for models of how glaciovolcanic systems evolve as the ice retreats."
  - Jökulhlaups: "The meltwater paths behind glacial outburst floods."
  - Other worlds: "Dark, oligotrophic, volcanic environments: Earth analogues for icy moons such as Enceladus." Set `topic: analogues` (inert until Task 6/7).

  Photos: `img/why-sampling-1`, alt "Gloved hands take a sample with a pipette from an orange hot pool." and `img/why-sampling-2`, alt "A caver in a helmet and half-mask collects sediment at the foot of an ice wall.", both credited to Cristian Monticone. Remove the now-duplicated `intro` from `headings.science`. Run `uv run prepare_images.py`.
- [ ] **Step 5: Run** `uv run pytest -q && uv run build.py`. Expected: pass. Before Task 6, `topic: analogues` would link to a page that doesn't exist yet, so leave it commented out in `content.yaml` until Task 7 is done.
- [ ] **Step 6: Commit** `feat: Why research here block in Science`.

### Task 6: Topics, validation and review gate

**Files:**
- Modify: `sitelib.py`
- Create: `tests/test_topics.py`

**Interfaces:**
- Consumes: `gallery_ref(slug, source)`, `SLUG_RE`, `RESERVED_SLUGS`, `_unused_gallery_files(static_dir, used_refs)`.
- Produces:
  - Content shape `topics: [{slug, kicker, title, teaser, intro: [str], chapters: [{heading, paragraphs: [str], photo?: {source, author, caption, alt}}], references: [{text, url?}], reviewers: str, reviewed?: bool}]`.
  - `REQUIRED`: `"topics": ["slug", "kicker", "title", "teaser", "intro", "chapters", "references", "reviewers"]`, `"topics.chapters": ["heading", "paragraphs"]`, `"topics.chapters.photo": ["source", "author", "caption", "alt"]`, `"topics.references": ["text"]`. `"topics"` is added to `OPTIONAL_SECTIONS`.
  - `_validate_places(content, static_dir) -> tuple[list[str], set[str]]` now returns `(errors, used_refs)` and no longer calls `_unused_gallery_files`.
  - New `_validate_topics(content, static_dir) -> tuple[list[str], set[str]]`. `validate` calls both, then `_unused_gallery_files(static_dir, place_refs | topic_refs)`.
  - `filter_consented` also keeps only topics with `reviewed is True`, adds `"topic:<slug>"` to the skipped list for each topic it drops, and deletes `topic` from each `science_why.items[]` whose slug is not a kept topic.
  - Test helpers in `tests/test_topics.py`: `topic(slug="microbiology", reviewed=False, photo=True) -> dict` and `with_topics(static_dir, *topics) -> dict`, which write the photos' derived images the way `make_place_images` does.

- [ ] **Step 1: Write the failing tests** in `tests/test_topics.py`:
  - `test_topics_valid`: a reviewed topic and an unreviewed one give `validate(...) == []`.
  - `test_todo_allowed_in_unreviewed_topic`: an intro of `"TODO ask Paolo"` with `reviewed=False` gives `[]`.
  - `test_todo_blocks_reviewed_topic`: the same with `reviewed=True` gives an error containing `"topics[0].intro[0]: contains TODO"`.
  - `test_forbidden_phrase_checked_in_drafts`: "extremophile" in an unreviewed topic gives a "forbidden phrase" error.
  - `test_topic_slug_clashes_with_place`: a place `torfa` and a topic `torfa` give an error containing `"topics[0].slug: same as a place: torfa"`.
  - `test_topic_slug_rules`: `"Micro Bio"` gives a "lowercase letters" error; `"static"` gives "reserved name"; a duplicate gives "used twice".
  - `test_topic_photo_needs_author`: gives `"topics[0].chapters[0].photo.author: missing"`.
  - `test_topic_photo_image_missing`: deleting the derived files gives `"topics[0].chapters[0].photo: image not found"`.
  - `test_unreviewed_topic_images_not_unused`: the derived images of an unreviewed topic produce no "not used by any photo" error.
  - `test_filter_drops_unreviewed_topics`: for each of `reviewed` = `False`, `"true"`, `1`, and missing, the topic is dropped and `"topic:microbiology"` is in the skipped list. `True` keeps it.
  - `test_filter_strips_links_to_hidden_topics`: `science_why.items` with `topic: "analogues"` (unpublished) and `topic: "typo"` lose their `topic` key, while `topic: "microbiology"` (published) keeps it.
- [ ] **Step 2: Run** `uv run pytest tests/test_topics.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement.**
  - TODO skip: `walk(node, path, todo=True)`. When walking the items of the list at path `"topics"`, pass `todo=(item.get("reviewed") is True)` for each item, and check `"TODO" in node` only when `todo` is set. Forbidden phrases are always checked.
  - `_validate_topics`: the slug rules are the same as for places (shared helper `_check_slug(path, slug, seen) -> list[str]`, extracted from `_validate_places`), plus the clash check against place slugs. For each chapter photo, check `ref = gallery_ref(topic_slug, source)` with `image_info`. If it is missing, report the error with "(run uv run prepare_images.py)". Add every ref to the used set.
- [ ] **Step 4: Run** `uv run pytest -q`. Expected: all pass, including the existing place tests.
- [ ] **Step 5: Commit** `feat: topics in the content model, review gate`.

### Task 7: Topic pages, teaser cards and menu

**Files:**
- Create: `templates/topic.html`
- Modify: `build.py`, `templates/sections/science.html`, `templates/layout.html`, `static/style.css`
- Test: `tests/test_build.py` (fixture `site_with_topics`, built like `site_with_places`, using the `tests.test_topics` helpers)

**Interfaces:**
- Consumes: the filtered `content["topics"]` from Task 6, `gallery_ref`, the `image` macro.
- Produces:
  - `build()` writes `<slug>/index.html` for each published topic, rendered with `root="../"`. The build message becomes `"Skipped (no consent or not reviewed): …"`.
  - `photo_authors` includes topic chapter photo authors.
  - Home: `<div class="topic-cards" id="research">` in the science section when `c.topics` is non-empty. Menu: `<li><a href="{{ root }}#research">Research</a></li>` only when `c.get("topics")` is non-empty.

- [ ] **Step 1: Write the failing tests.**
  - `test_writes_topic_pages`: for a reviewed `microbiology` topic, `_site/microbiology/index.html` exists and contains the `<h1>` title, every chapter `<h2>`, an `<ol class="references">` with the reference text, and the `© author` of the chapter photo.
  - `test_unreviewed_topic_leaves_no_trace`: for an unreviewed topic with the unique title `"Zzdraft title"`, no `_site/<slug>/` exists and no `*.html` file under `_site` contains `"Zzdraft"`, `"#research"` or the topic's photo author (when that author appears nowhere else).
  - `test_topic_card_and_menu`: with a reviewed topic, the home page has `href="microbiology/"` inside `id="research"` and a `Research` menu link.
  - `test_why_link_only_when_published`: with `science_why` linking to an unreviewed topic, the home page has no `href="analogues/"` and still shows the item title.
  - `test_topic_reference_links`: a reference with a `url` renders `<a href="https://doi.org/…" rel="noopener">`.
  - Extend `test_all_local_links_resolve`'s fixture so it also covers a topic page.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** `topic.html`. Model it on `place.html`, with no viewer:
  - Blocks: `title` (topic title · site title), `description` (teaser), `og_image` (the first chapter photo if any; otherwise the layout default).
  - Body: kicker, `<h1>`, intro paragraphs. One `<section class="chapter">` per chapter: `<h2>`, paragraphs, and an optional `<figure>` with `image(gallery_ref(topic.slug, ph.source), ph.alt, …, root=root)` and `<figcaption>{{ caption | md }} © {{ author }}</figcaption>`.
  - Then `<h2>References</h2><ol class="references">`.
  - Then `<nav class="place-next">` with ← Home and "Next: <other topic title> →".
  - CSS: text width capped at about 40rem, figures at full content width, small reference text.
- [ ] **Step 4: Implement** the topic cards in `science.html`: kicker, title, teaser, "Read →". The image is the first chapter photo if any. Add the menu link in `layout.html`.
- [ ] **Step 5: Run** `uv run pytest -q`. Expected: all pass. Uncomment `topic: analogues` in `science_why` (from Task 5). It stays inert until the page is reviewed.
- [ ] **Step 6: Commit** `feat: topic pages, research cards and menu link`.

### Task 8: Watermarked topic photos in prepare_images

**Files:**
- Modify: `prepare_images.py` (`gallery_jobs`, `run_gallery`)
- Test: `tests/test_images.py`

**Interfaces:**
- Produces: `gallery_jobs(content)` also yields `(source, author, gallery_ref(topic_slug, source))` for every topic chapter photo (reviewed or not). `run_gallery` keeps folders for the place slugs and topic slugs together.

- [ ] **Step 1: Write the failing tests.**
  - `test_gallery_jobs_include_topics`: a topic with one chapter photo appears in the jobs with ref `img/places/microbiology/<stem>`.
  - `test_run_gallery_keeps_topic_folder_and_removes_deleted_topic`: running with the topic writes the files; running again without it deletes its folder.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** both changes.
- [ ] **Step 4: Run** `uv run pytest -q`. Expected: pass.
- [ ] **Step 5: Commit** `feat: watermarked photos for topic pages`.

### Task 9: Reviewer copies and guide

**Files:**
- Create: `review_copy.py`, `tests/test_review_copy.py`, `docs/review/` (output)
- Modify: `GUIDE.md`

**Interfaces:**
- Produces: `topic_markdown(topic: dict) -> str` and `main()`. `main()` writes `docs/review/<slug>.md` for every topic in `content.yaml`, reviewed or not. Run it with `uv run review_copy.py`.

- [ ] **Step 1: Write the failing test** `test_topic_markdown`. For a topic with two chapters, a photo and two references, the output:
  - starts with `# <title>`,
  - has the line `Reviewers: <reviewers> · Status: draft (not on the site)`, or `published` when `reviewed is True`,
  - has `## <heading>` for each chapter,
  - has the paragraphs separated by blank lines,
  - has the photo as `[Photo: <caption> © <author>]`,
  - ends with `## References` and a numbered list `1. <text> <url>`.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** `review_copy.py`, plain string building (the module docstring says what it is for). Add a "Science pages" section to `GUIDE.md`: where the text lives (`topics:`), how review works (`uv run review_copy.py`, send `docs/review/<slug>.md`), how to publish (`reviewed: true`, then build and push), and the TODO and forbidden-phrase rules for drafts. Also update the file table and the "facts must come from" comment at the top of `content.yaml` to mention the team documents and the cited literature.
- [ ] **Step 4: Run** `uv run pytest -q`. Expected: pass.
- [ ] **Step 5: Commit** `feat: reviewer copies of science pages; guide`.

### Task 10: Draft `/microbiology/`

**Files:**
- Modify: `content.yaml` (`topics[0]`)
- Create: `docs/review/microbiology.md` (generated)

- [ ] **Step 1: Read the sources.** Extract `riassunto_per_sgi.pdf` and `Vatnajokull_2026_Italian_team_note.pdf` (`pdftotext -layout`). Verify each reference below with WebSearch/WebFetch: authors, year, title, journal, volume and pages, and a DOI that resolves. Drop any reference that cannot be verified.
  - Clance J. J. et al. (2024), *Frontiers in Geochemistry* 2:1410338 (Mount Meager)
  - Connell L. & Staudigel H. (2013), *Biology* 2(2):798–809 (Erebus DOVE)
  - Cousins C. R. et al. (2018), *Geobiology* 16(5):507–521 (Kverkfjöll hot spring)
  - Cousins C. R. & Crawford I. A. (2011), *Astrobiology* 11(7):695–710
- [ ] **Step 2: Write the topic.**
  - `slug: microbiology`, `kicker: Science`, `title: Life without light`, a one-sentence `teaser`, a two-paragraph `intro`, `reviewers: Paolo Turrini, then Prof. Andrea Franzetti`, `reviewed: false`.
  - Chapters and their content, exactly as spec §3.1: "Dark, poor, volcanic"; "What we sampled in 2026"; "What comes next"; "In 2027". The last chapter's paragraph reads `TODO (Paolo Turrini): sampling plans for 2027.`
  - Reference our own facts as `Consorzio Speleologi Ipogenici (2026). Vatnajökull 2026 – Fire Under Ice: notes on the expedition. Report to the Società Geografica Italiana, unpublished.`
  - Mark each claim with a bracketed reference number in the text, e.g. `[1]`, matching the order of `references`.
  - Photos: chapter 1 `photos/torfa/RIMG0247.JPG` (Ivan Vicenzi; "The hot pool at the centre of the Sala del Graal, Freyja Hellir, July 2026."); chapter 2 `photos/science/sampling_1.JPG` (Cristian Monticone; "Sampling at a hot pool, July 2026."); chapter 3 `photos/science/sampling_2.jpg` (Cristian Monticone; "Collecting sediment under the ice, 2026.").
  - Style: short plain sentences, no hype. No "extremophile" (see Global Constraints). Nothing beyond the sources.
- [ ] **Step 3: Generate.** Run `uv run prepare_images.py && uv run review_copy.py && uv run pytest -q && uv run build.py`. Expected: the build passes, and the topic shows in "Skipped … topic:microbiology".
- [ ] **Step 4: Preview.** Temporarily set `reviewed: true`, build, and view `/microbiology/` at 375 px and 1280 px wide in the browser. Fix the layout if needed, then set it back to `false`. This step's commit must contain `reviewed: false`.
- [ ] **Step 5: Commit** `content: draft microbiology page for review`.

### Task 11: Draft `/analogues/`

**Files:**
- Modify: `content.yaml` (`topics[1]`)
- Create: `docs/review/analogues.md` (generated)

- [ ] **Step 1: Verify the references** as in Task 10:
  - Cousins & Crawford (2011), as above.
  - Cousins C. R. et al. (2013), *Journal of Volcanology and Geothermal Research*, doi 10.1016/j.jvolgeores.2013.02.009.
  - Hsu H.-W. et al. (2015), *Nature* 519:207–210 (silica nanoparticles, hydrothermal activity at Enceladus).
  - Waite J. H. et al. (2017), *Science* 356:155–159 (H₂ in the Enceladus plume).
  - Curtis A. (2020), abstract, 3rd International Planetary Caves Conference.
  - Davis R. et al. (2020), abstract, Analog Field Sites Mini Symposium (LPI).
  - One verified review source for Europa's ocean.
- [ ] **Step 2: Write the topic.**
  - `slug: analogues`, `kicker: Science`, `title: Other worlds on Earth`, a one-sentence `teaser`, an `intro`, `reviewers: Lorenzo Bordin`, `reviewed: false`.
  - Chapters as spec §3.1: "Ice over heat, elsewhere" (names the Encelado cauldron after Enceladus); "What carries over, and what doesn't"; "Caves on other worlds"; "What we add" (a contribution of field data, not planetary research of our own).
  - Photos: `photos/kverkfjoll/P7161033.JPG` (Andrea Benassi; "The Encelado cauldron, Kverkfjöll, July 2026.") and `photos/torfa/torfa_final_stream.JPG` (Cristian Monticone; "A stream through the ice, Freyja Hellir, July 2026.").
  - Same style rules as Task 10.
- [ ] **Step 3: Generate** as in Task 10, Step 3.
- [ ] **Step 4: Preview** as in Task 10, Step 4.
- [ ] **Step 5: Commit** `content: draft analogues page for review`.

### Task 12: Final verification

- [ ] **Step 1: Run** `uv run prepare_images.py && uv run pytest -q && uv run build.py && uv run check_links.py`. Expected: no WARNING lines, all tests pass, the build reports both topics as skipped, and there are no broken links.
- [ ] **Step 2: Check in the browser.** Serve `uv run python -m http.server -d _site 8000`. At 375 px and 1280 px wide, check:
  - the home page: the stats note, "Why research here", the press photos and "in press", the partner stars;
  - `/torfa/`: the new cover on the card and on the page, and the viewer working on the new photos;
  - `/kverkfjoll/`.
  - Confirm there is no "Research" menu entry while the drafts are unreviewed.
- [ ] **Step 3: Compare with the brochure.** Check each row of the table in spec §2 against the built site and note any mismatch. Fix mismatches, then commit `fix: …` if needed.
