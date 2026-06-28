# WDDM UX/UI Polish Pass — Hybrid Piece Picker + Left-Panel IA

**Date:** 2026-06-28
**Status:** Approved design, pending implementation plan
**Repo:** `rayswaynl/WDDM` (single-file `index.html`)

## Summary

A UX/UI polish pass on WDDM, triggered by the palette expansion to 204 items, which
outgrew its native `<select>` picker. Replace the dropdown with a **hybrid thumbnail
picker** (inline searchable grid + a "browse all" modal) that surfaces the 189 generated
thumbnails, fix the duplicate-optgroup wart for free, and tidy the dense left panel's
information architecture. Editor-chrome only — no change to the canvas renderer, the SQF
export, coordinates, or the `CATALOG` data.

## Goals
- G1 — **Hybrid piece picker** replacing the native `<select id="palette">`: an inline
  searchable thumbnail grid in the left panel for fast repetitive adding, plus a roomy
  "Browse all" modal for visual exploration.
- G2 — **Kill the duplicate optgroups** (currently 26 groups for 20 categories in defense
  mode) — achieved for free by the picker deriving categories from the *unique* `grp` set.
- G3 — **Left-panel IA cleanup** — reorder to the real build workflow and bound section
  heights so the panel stops infinitely stacking/overflowing.
- G4 — **Visual hierarchy & spacing polish** strictly within the existing design tokens.

## Non-goals
- NG1 — No change to the canvas renderer (`drawObj`, sprite/portrait/glyph layers), the
  **SQF export** (`buildOut`), coordinates/rotation, snap, or the `CATALOG` entries.
- NG2 — No framework/build step/new dependencies — vanilla JS + CSS in the single file.
- NG3 — No new features (no fields-of-fire/preview/PNG/share changes) — those stay as-is.
- NG4 — Not touching the right-panel inspector's core (X/Y/Z/dir/dup/mirror/delete) beyond
  a light export-actions tidy.

## Current state (index.html)

**Design tokens (`:root`, lines 18–22):** `--gunmetal #14171B`, `--steel #2A2F36`,
`--steel2 #343b44`, `--olive #5C6536`, `--bone #E7E3D6`, `--orange #D9763C`,
`--line #39414b`. Fonts: Oswald (headers), Inter (body), JetBrains Mono (mono). Components:
`.segmented`, `.modebox`, `.asset-list` (chips), `.btnbar`, `.obj-list`, `.divider`,
`.badge`, `.chip`. Layout grid `330px 1fr 350px` (line 39).

**Left panel `.scroll` (lines 130–215), in order:** Editor mode (segmented) → Load preset
(select + button) → `defenseCtrlsA` (Edit-walls button, `#fortOnly` check, `#wallModeInfo`
asset chips) → divider → Template variable name (`#tplName`) → `defenseCtrlsB`
(`#structureType`, `#missionTarget` selects) → divider → **Add object: `<select id="palette">`
+ `#addBtn`/`#addCustomBtn` + `#palThumb`** (lines 196–202) → divider → Placed objects
(`#count`, `#objList`) → hint.

**Picker-relevant JS:** `renderPalette()` (lines ~1131–1147) builds the `<optgroup>`/`<option>`
tree, filtered by `buildMode==='base'?isBaseStructure:(!isBaseStructure && (!fortOnly||
isFortificationAsset))`. `setMode`/`setFortOnly` call `renderPalette`. `#addBtn.onclick =
addObj($('palette').value)` (line ~1473); `setThumb('palThumb', s.value)` on palette change.
Helpers: `META(c)` (catalog entry), `IS_WPN(c)`, `CAT_OF(c)`, `CREW_OF(c)`, `SIZE_OF`,
`ART_OF`, `STYLE`, `TEX` glyph table, `PORTRAIT_FILES` Set, `VALID_CLASSES`, `addObj(cls)`.

**The pain (measured):** defense mode = 117 options / 26 optgroups (6 duplicates from
non-contiguous `grp` ordering); base mode = ~87 options. No search. Native `<select>` can't
show the 189 thumbnails; they only appear singly in `#palThumb` after selection.

## Architecture

A new **picker module** in `index.html` (JS + CSS, no new files) that renders tiles from a
derived item list and drives both the inline grid and the modal from shared code. The native
`<select id="palette">`, `#addBtn`, and `#palThumb` are removed.

### Components

**1. Item list builder — `pickerItems()`**
Returns the mode/fortOnly-filtered array (same predicate as today's `renderPalette`), each
as `{cls, label, grp, isWpn, ai}` where `label` is a short human name (derive: `META(cls).label
|| cls`), `isWpn = IS_WPN(cls)`, `ai = CREW_OF(cls)`. Order: by category (unique `grp` in
first-seen order), items within a category in array order — this groups items logically and
**eliminates duplicate categories** regardless of CATALOG contiguity.

**2. Tile renderer — `tileEl(item)`**
A clickable tile: a square image area + a one-line mono label + a corner badge for weapons
(`⚔` + `ai` if `ai>0`). Image source:
- if `PORTRAIT_FILES.has(cls)` → `assets/img/<cls>.jpg` (lazy `loading="lazy"`),
- else → the procedural `TEX[STYLE(cls)]` glyph rendered once to a small offscreen canvas
  (e.g. 64×64, cached by `cls`) and used as the tile image — so all ~15 art-less pieces
  still show a representative glyph, consistent with the canvas.
Click → `addObj(cls)` (adds to centre, selects). `title` = full classname.

**3. Inline grid (left panel)** — replaces lines 196–202:
- `<label>Add object</label>` + a search `<input id="pickSearch" placeholder="Search pieces…">`
  (reuses the existing input styling).
- Category filter chips `#pickCats` (the unique `grp` set + an "All" chip, `.chip`/`.chip.on`
  styling). Clicking a chip filters by category.
- A height-bounded scroll grid `#pickGrid` (3 columns, `max-height` ~260px, `overflow:auto`).
- A `<button id="browseAll">Browse all pieces…</button>` opening the modal.
- `#addCustomBtn` ("+ Custom…") stays, with its existing validation/confirm.
- Render = `renderPicker()`: filter `pickerItems()` by current search text (classname/label
  substring, case-insensitive) and active category; rebuild `#pickGrid` grouped by category
  with a small category subheading row when "All" is active.

**4. Browse modal `#pickModal`** — a normal-flow overlay (hidden via a `.open` class, NOT
`position:fixed` issues; use `position:fixed` full-screen overlay is fine in the real app —
only mockups need the faux-viewport workaround):
- Header: title "Browse pieces" + a wider search `#pickModalSearch` + close `×`.
- Left: category sidebar (the unique `grp` list + counts). Right: a 5-column scroll grid.
- Same `tileEl` + filter logic as the inline grid (shared functions). Click a tile → `addObj`;
  modal **stays open** for rapid multi-add. `Esc` or `×` or backdrop click closes.

**5. Wiring changes**
- `setMode`/`setFortOnly` call `renderPicker()` (and re-derive category chips) instead of
  `renderPalette()`. Remove `renderPalette`, the `#palette` select, `#addBtn`, `#palThumb`,
  and the palette-change `setThumb('palThumb',…)` listener. Keep `setThumb('iThumb',…)` for
  the inspector (unchanged).
- Search input: `input` listener → `renderPicker()` (debounce not required at this scale, but
  cap rendered tiles is unnecessary since search shortens the list).

### Left-panel IA reorg (G3)
New top-to-bottom order in `.scroll`:
1. **Editor mode** (segmented) — unchanged.
2. **Load preset** (select + button) — unchanged, stays near the top (a starting action).
3. **Pieces** — the new inline picker (search + chips + grid + Browse-all + Custom).
4. **Placed objects** (`#count`, `#objList`) — give `#objList` a `max-height` (~38vh) scroll
   so it and the picker don't both grow unbounded.
5. **hint** — unchanged (trimmed).
Collapse advanced config into one `<details id="tmplCfg"><summary>Template & wall target</summary>`
(closed by default), containing: `#tplName`, `#structureType`, `#missionTarget`, the
Edit-walls button, `#fortOnly`, and the `#wallModeInfo` asset chips. The per-piece building
loop never needs these open; factory-wall submitters expand it in one click. The
`defenseCtrlsA`/`defenseCtrlsB` show/hide logic in `setMode` continues to work (the elements
just live inside the `<details>` now).

### Visual polish (G4)
- Reuse existing tokens only — no new colors/fonts. Consistent label/divider rhythm.
- Tiles: `.pick-tile` = `background:var(--gunmetal); border:1px solid var(--line);
  border-radius:4px`; `:hover`/selected → `border-color:var(--orange)`. Label strip uses the
  existing mono style. Match the `.obj-list`/`.chip` visual language.
- Inspector tidy: group `#copyBtn` (Copy SQF) and `#shareBtn` (Copy share link) as a clear
  export action pair; move the verbose factory-wall hint `.modebox` into the
  `Template & wall target` details (it's the same context). No change to inspector fields.

## Data flow
1. Boot/`setMode`/`setFortOnly`/search/chip → `renderPicker()` → `pickerItems()` →
   `tileEl()` per item → grid DOM.
2. Tile click → `addObj(cls)` → existing add/draw/syncUI path (unchanged).
3. Export (`buildOut`) untouched — still driven by `objs`.

## Error handling
- Missing thumbnail JPG: `tileEl` already falls to the glyph path (uses `PORTRAIT_FILES` as
  the gate, so no 404s); the glyph canvas always succeeds.
- Empty filter result: grid shows a muted "No pieces match" row.
- Modal with no JS support / fetch failure of data: picker still renders from `CATALOG`
  (classnames + glyphs); thumbnails simply absent — degrades gracefully.
- `Esc` handler scoped so it only closes the modal when open (doesn't interfere with canvas
  keyboard nudges).

## Testing (Playwright + regression)
- Picker renders every mode/fortOnly item; **no duplicate category headings/chips** (assert
  unique category set; defense-mode category count == 20, not 26).
- Search filters (type "trench" → only trench tiles); category chip filters; "All" shows
  grouped sections.
- Click-to-add works in BOTH the inline grid and the modal; `objs.length` increments and the
  object draws.
- Thumbnails render for `PORTRAIT_FILES` members; glyph-canvas fallback renders for an
  art-less class (e.g. `Land_fort_watchtower_EP1`).
- Modal opens via Browse-all, closes via `×`, `Esc`, and backdrop; stays open across adds.
- `setMode('base')` shows base-structure categories; `setMode('defense')` shows defense ones;
  `fortOnly` filters to fortifications.
- **0 console errors.**
- **Export regression gate** (as in the items work): `buildOut()` output byte-identical to
  pre-change baseline for fixed presets — proves editor-chrome-only.
- Sanity at the 330px panel width (3-column grid fits, no horizontal scroll).

## Build order
1. Picker module: `pickerItems` + `tileEl` (+ glyph-canvas cache) + `renderPicker`, inline
   grid markup replacing the select; remove the select/addBtn/palThumb; wire setMode/fortOnly.
2. Category chips + search filter.
3. Browse-all modal (shared tile/filter code).
4. Left-panel IA reorg (collapse advanced config; bound heights; reorder).
5. Visual polish + inspector export tidy.
6. Verification: Playwright suite + export regression gate, then finish branch.
