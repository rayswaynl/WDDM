# WDDM × arma2-co-config-reference — Items Repo Integration

**Date:** 2026-06-27
**Status:** Approved design, pending implementation plan
**Repos:** `rayswaynl/WDDM` (the editor) · `rayswaynl/arma2-co-config-reference` (the items repo / ground-truth)

## Summary

Wire the new Arma 2 ground-truth reference repo (`arma2-co-config-reference`) into the
WDDM composition editor so the editor can (1) **validate** Arma 2 classnames, (2) **expand**
its buildable palette, (3) show **per-item picker thumbnails**, and (4) use those same
images as a **canvas fallback** for items that lack a real top-down sprite.

The items repo is a static reference dump — 6 base-game config exports (`CfgVehicles.txt`
3.9 MB, `CfgWeapons.txt`, `CfgMagazines.txt`, `CfgAmmo.txt`, `CfgWorlds.txt`,
`CfgCloudlets.txt`) plus 2,893 reference JPGs whose **filenames are exact classnames**
(`SPG9_TK_INS_EP1.jpg`, `Land_HBarrier_large.jpg`, …), organized in nested category
folders under `Images/A2/` and `Images/OA/`. Nothing in it is importable code; it is a
source we *derive* data from.

## Goals

- G1 — **Validate classnames** against the base-game config as ground-truth. Audit the
  existing CATALOG for typos; warn + autocomplete on free-text classname inputs.
- G2 — **Expand the palette** with a curated batch (+30–50) of buildable statics, walls,
  fortifications, and static weapons mined from `CfgVehicles.txt`.
- G3 — **Picker thumbnails** — show each item's real reference image in the palette panel
  and the Inspector, so the user sees what they're placing.
- G4 — **Canvas portrait fallback** — for items with no real top-down sprite, draw the
  portrait JPG on the canvas (fit-contained, dimmed) instead of the procedural glyph.

## Non-goals

- NG1 — Generating true orthographic top-down sprites (Blender/AI render pipeline). The
  repo has no top-down art; G4's stopgap (portrait-on-canvas) is the agreed substitute.
  A real top-down pipeline is a separate future effort.
- NG2 — Changing the SQF / `WFBE_NEURODEF_*` export in any way. All new data is editor-only.
- NG3 — Hard-blocking invalid classnames. Validation is **warn-only**; the editor stays permissive.
- NG4 — Bundling the full 2,893-image set or the full 3.9 MB config into the shipped Page.
  Only palette-relevant subsets are committed.

## Current state (WDDM `index.html`, single ~122 KB file)

- **`CATALOG`** array, lines **372–490**, ~92 items. Per-item fields: `grp` (group),
  `cls` (Arma classname — the only field that reaches SQF), `size` `[w,d]` footprint,
  `style` (key into the `TEX` glyph table), `art` (optional sprite span), `cat` (weapon
  category for AI cost), `label`, `icon`.
- **Visual rendering** is two-layer:
  - Layer A — real top-down PNG sprites: `SPRITE_FILES` set (lines 573–580, **28**
    classnames), `SPRITE_ALIAS` map (lines 523–565, ~40 aliases), preloaded by
    `preloadSprites()` (line 594) from `assets/sprites/<basename>.png`, drawn fit-contain
    at lines 1407–1409.
  - Layer B — procedural glyphs: `TEX` drawing functions (lines 1288–1345) keyed by `style`,
    colored from `PAL` (lines 1271–1275). Fallback when no sprite.
- **No classname validation.** `addCustomBtn` (line 1474) accepts any `prompt()` string;
  the Inspector `iClass` field (line 1259) accepts free text. `classAllowedInFortMode`
  (lines 503–506) is a UI filter, not validation.
- **Export**: `buildOut()` (lines 1595–1598) emits `missionNamespace setVariable
  ['WFBE_NEURODEF_*', [[cls,[x,y,z],dir], …]]`. Only `cls`, position, and `dir` are
  exported; all CATALOG metadata is editor-only.

## Architecture

A build-time **generator** (`tools/gen_assets.py`) parses the items repo once and commits
compact artifacts into WDDM. The runtime app (`index.html`) fetches those artifacts the
same way it already fetches sprites. The items repo is **not** a runtime dependency.

```
arma2-co-config-reference/            tools/gen_assets.py            WDDM/ (shipped Page)
  Config/CfgVehicles.txt   ──parse──▶  classname index     ──────▶  assets/data/classnames.json
  Images/**/<cls>.jpg       ──copy──▶  matched subset      ──────▶  assets/img/<cls>.jpg
                            ──diff──▶  expansion report    ──────▶  tools/expansion-candidates.md
                                                                    index.html (fetch + render)
```

### Rejected alternatives

- **Hotlink config/images live from GitHub** — couples two repos at runtime, breaks
  offline, risks raw.githubusercontent 404s / rate-limits, needs the items repo as Pages.
- **Inline all data into `index.html`** — dumps ~640 KB of classnames + base64 images into
  the single file; slow, unmaintainable.

## Components

### 1. `tools/gen_assets.py` (new, build-time, outside the shipped app)

Inputs: path to `arma2-co-config-reference` (default sibling `../arma2-co-config-reference`,
overridable via `--ref`), path to WDDM (default repo root).

Outputs:
- **`assets/data/classnames.json`** — parsed from `CfgVehicles.txt`. Map
  `cls → {dn: <displayName>, scope: <int>}`. Parse strategy: regex over `class <Name>`
  declarations + the nearest `displayName`/`scope` within each block (the file is regular
  C-like config). For pure name-validation the full declared set is retained; the
  autocomplete suggestion list filters to `scope >= 1` (placeable) to stay lean.
- **`assets/img/<cls>.jpg`** — for each unique `cls` in the CATALOG (and, in Phase 3, each
  newly added item), recursively locate `<cls>.jpg` under `Images/` and copy it in. Report
  any CATALOG classname with no matching image (these fall back to a glyph on canvas).
- **`tools/expansion-candidates.md`** — buildable statics/walls/fortifications present in
  `CfgVehicles` but absent from the CATALOG, with `displayName` + has-image flag, to drive
  Phase 3 curation. Heuristic filter: `scope == 2` and `vehicleClass`/parent indicating
  static defense / fortification / wall (tuned during implementation).

The generator is **idempotent** and re-runnable; output is committed so the Page needs no
build step to serve.

### 2. Runtime changes — `index.html`

Loaded once at startup alongside the existing sprite preload.

**Phase 1 — Validation (G1).**
- Fetch `assets/data/classnames.json`; build a `VALID_CLASSES` Set + a `dn` lookup.
- Startup self-audit: for each CATALOG `cls`, if absent from `VALID_CLASSES`, emit a
  dev-facing warning (console + a small in-UI badge/count). Surfaces typos.
- `addCustomBtn` and the Inspector `iClass` field gain a `<datalist>` of valid classnames
  (label shows `cls — displayName`) and an inline "⚠ unknown classname" indicator when the
  entered string isn't in `VALID_CLASSES`. Non-blocking.

**Phase 2 — Images (G3 + G4), unified on one `assets/img/<cls>.jpg` per item.**
- Extend preload to also load `assets/img/<cls>.jpg` into the existing image cache (missing
  files fail silently, exactly like the sprite path).
- Canvas draw becomes a **3-layer fallback**: real top-down sprite → portrait JPG
  (fit-contained, drawn slightly dimmed to signal "approximate, not top-down") → procedural
  `TEX` glyph.
- **Palette panel**: a thumbnail preview pane that updates to the selected item's image.
- **Inspector**: show the selected placed object's thumbnail.

**Phase 3 — Palette expansion (G2).**
- From `expansion-candidates.md`, curate a vetted batch (+30–50 high-value buildables).
- Add CATALOG entries: classnames validated (Phase 1) and images already wired (Phase 2);
  the manual work is each item's editor metadata (`size`/`style`/`cat`/`art`), since the
  config does not encode top-down footprints.

## Data flow

1. Dev runs `python tools/gen_assets.py` → JSON + JPGs + candidate report committed.
2. Browser loads `index.html` → fetches `classnames.json`, preloads sprites + `assets/img/*`.
3. User edits: classname inputs validate against `VALID_CLASSES`; palette + inspector show
   thumbnails; canvas renders sprite → portrait → glyph.
4. Export (`buildOut`) unchanged — emits the same `WFBE_NEURODEF_*` SQF as before.

## Error handling

- Missing `classnames.json` (e.g. served before generator run): validation degrades to
  off (no warnings, no autocomplete); editor fully functional. Log once.
- Missing `assets/img/<cls>.jpg`: silent fall-through to the next render layer (mirrors the
  existing sprite-404 behavior).
- Generator run with a wrong `--ref` path or missing config file: hard error with a clear
  message; commits nothing partial.
- Classname present in config but no image: allowed; canvas uses a glyph; generator notes it.

## Testing

- **Generator**: `classnames.json` parses and contains known anchors (e.g.
  `Land_HBarrier_large`, `SPG9_TK_INS_EP1`); every CATALOG `cls` is audited (found-or-flagged);
  copied image count == CATALOG items with a matching JPG.
- **Runtime (Playwright)**: page loads with **0 console errors**; a known-good classname
  (`M2StaticMG`) shows no warning; a known-bad one (`Land_Razorwire`) triggers the warning;
  palette + inspector thumbnails render; canvas shows portrait fallback for an
  image-but-no-sprite item.
- **Regression**: `buildOut()` output is **byte-identical** to a pre-change baseline for a
  saved composition; the existing 28 sprites still render.

## Risks & mitigations

- **`classnames.json` size** (~16 k entries). Mitigate by filtering the autocomplete list to
  `scope >= 1` and keeping the validation set as a compact string array; gzip via Pages.
- **Portrait-on-canvas looks misleading** (not actually top-down). Mitigate by dimming +
  fit-contain so it reads as an approximate badge, not a precise footprint; sprites still win.
- **Expansion metadata drift** — new CATALOG items need correct `size`/`style`; mitigate by
  validating classnames (Phase 1) and reusing existing glyph styles where possible.
- **Cross-repo provenance** — images are © Bohemia (non-commercial reference). We only copy
  the small palette-relevant subset into WDDM; same legal posture as the repo's own README.

## Build order

Phase 1 (foundation + validation) → Phase 2 (images, picker + canvas) → Phase 3 (curated
expansion). Each phase is independently shippable and leaves `index.html` working.
