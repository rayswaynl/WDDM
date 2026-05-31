# WDDM Deeper Pass — Design Spec

**Date:** 2026-05-31
**Status:** Draft for review
**Project:** WDDM (Warfare Dynamic Defense Manager) editor + the Arma 2 WASP "Warfare" mission engineer-defense feature.

---

## 1. Goal

A deeper, better-researched pass on the engineer-defense feature and the WDDM editor, in seven coherent workstreams:

0. **Measurement accuracy (foundation)** — replace the editor's eyeballed object footprints with real-world measured dimensions, with an optional later lock to the game's own `boundingBoxReal`. Done FIRST because layouts + sprites both depend on honest scale.
1. **Sprite asset system** — replace the editor's procedural glyphs with a consistent set of top-down sprites (style B, grounded in real-world kit), generated in ChatGPT, with a safe procedural fallback.
2. **Doctrine layout rework** — revise the 16 SQF + 16 editor preset layouts to match real NATO vs Warsaw Pact field-fortification doctrine (see `RESEARCH.md`).
3. **Fields-of-fire overlay** — filled translucent firing-arc wedges (style A) as an editor toggle.
4. **Shareable layout links** — encode a composition in the URL hash for one-click Discord sharing.
5. **Mission orphan-cleanup** — delete a position's props when it is destroyed or sold (server health).
6. **Funny easter eggs** — one or two low-risk editor gags.

**Locked decisions (from brainstorming):** overlay = **A** (filled wedges); sprites = **B** (top-down minis) anchored to **real weapon systems** (not Bohemia models — IP + brand "original assets" rule); integration = **sprite-or-procedural fallback**; build order = **3-sprite pilot → layouts → editor features → cleanup → eggs**; prompt pack covers the **full set**.

**Research basis:** `C:\Users\Steff\wddm-mockups\RESEARCH.md` (US FMs 5-103, 6-50/ATP 3-09.50, 44-18-1, 19-4, 17-98; Soviet FM 100-2-1/-3; CIA FOIA; DTIC). All claims cited there.

---

## 1b. Component 0 — Measurement accuracy (asset → map → in-game)

**Problem (confirmed by code read).** The editor's `size:[w,d]` values are **eyeballed approximations** (original catalog comment: "approx footprints"). They are *not* exported and *not* read by Arma — they only control how big an object **draws in the editor**. The position/rotation chain is already provably exact and is NOT touched here:

- Editor stores `{x,y,z}` in **metres** → export writes them verbatim into `['cls',[x,y,z],dir]` → SQF `_origin modelToWorld _relPos` interprets `[x,y,z]` as **model-space metres** → object spawns at the exact metre point. No scale factor anywhere.
- Rotation: editor `headingOf = (parentDir − dir)` ≡ SQF `setDir (_dir − _relDir)`. Grid = 1 m, snap = 0.5 m.

So the ONLY soft spot in asset→map→in-game is the footprint sizes, and they're guessed. A wrong `size` never moves anything in-game; it makes the **preview lie about scale**, so the user spaces objects by eye wrongly → clipping or gaps in-game. Fixing this = an honest preview.

### 0.1 Data model: `size` (collision footprint) + optional `art` (visual span) — both in real metres

A thin barrel/trail overhangs but doesn't collide. One number can't serve both spacing and art (a D-30 carriage ≈ 2.4 m wide, but barrel+trail span ≈ 5.4 m). So each catalog entry gets:

- **`size:[w,d]`** — the object's **base/carriage footprint** in metres. Drives spacing intuition, 0.5 m snap, hit-testing, selection rect. = the "will it clip in-game" box.
- **`art:[w,d]`** *(optional)* — the **full visual span** in metres incl. barrel/trail, used only to draw the sprite/glyph at true scale. Defaults to `size` when omitted. The fit-contain draw (§2.4) uses `art` if present, else `size`.

Both are real metres → editor visual extent = in-game reality. Hit-testing/snap stay on `size` so selecting a howitzer isn't a giant barrel-sized hitbox.

### 0.2 Source of truth — real-world now, game-exact later (user decision)

- **Phase A (now):** set all ~35 footprints from **cited real-world equipment dimensions** (RESEARCH.md + manufacturer/Wikipedia specs). ~90% match to Arma's model boxes. Examples to correct from current guesses:
  | class | current (guess) | real-world `size` | `art` (w/ barrel) |
  |---|---|---|---|
  | M2StaticMG (M3 tripod) | 1.6×1.6 | 1.6×1.9 | — |
  | ZU23_TK_EP1 | 3×2.2 | 2.9×4.6 | — (twin barrels ~ within) |
  | D30_TK_EP1 | 4×2.6 | 2.4×2.4 (carriage) | 2.4×6.0 (barrel+trail) |
  | M119_US_EP1 | 4×2.6 | 2.0×2.5 (carriage) | 2.0×6.3 (barrel+trail) |
  | TOW_TriPod_US_EP1 | 2×2 | 1.8×1.8 | — |
  | Stinger_Pod_US_EP1 | 2×2 | 1.4×1.4 | — |
  | Land_HBarrier_large | 5×1.2 | 5.0×1.2 (≈ correct) | — |
  | Hedgehog | 1.5×1.5 | 2.0×2.0 | — |
  (full table produced during implementation; every value cited.)
- **Phase B (optional, later, user-run):** a throwaway ~10-line SQF dumps `boundingBoxReal` for each classname; user pastes output; catalog locked to the engine's exact numbers. Not a shipped tool — run once and discard. (User chose: do Phase A now, keep B available.)

### 0.3 Sprite contract tie-in

Each generated sprite is **trim-to-content** (cropped to its alpha bounding box) at asset-prep, so the drawn equipment maps exactly onto its `art` (or `size`) metre box → fit-contain becomes exact, not approximate. The orientation contract (front=up) is unchanged.

### 0.4 What this explicitly does NOT change

Coordinates, `modelToWorld`, rotation, snap granularity, SQF, crew counts, the 16 m clear-radius. Only the per-class draw dimensions and (additively) the optional `art` field. No QA gadgets are shipped in the editor (user declined ruler/extent/ring tools).

---

## 2. Component 1 — Sprite asset system

### 2.1 Locked style preamble (reused verbatim in every prompt)

> Top-down (plan view), straight 90° bird's-eye, a single piece of military equipment centred on a fully transparent background. Semi-realistic but slightly stylised game-counter look — clean readable shapes, not photoreal, not cartoon. Soft contact shadow directly beneath the object. Even lighting from the top-left. Muted militaristic palette. The object's firing/front direction points toward the TOP of the image. No text, no labels, no grid, no base ring unless it is physically part of the object. Square PNG with alpha unless an aspect ratio is specified. The object fills ~80% of the frame with even padding.

Faction tint: **US/WEST = olive drab + tan, dark-steel barrels**; **Soviet/EAST = darker Soviet green, amber Bakelite where noted**; **concrete = neutral grey**; **sandbags/HESCO = tan/khaki**.

Per-asset prompt = **preamble + the real-world SPRITE NOTE from RESEARCH.md + faction tint + aspect note**.

### 2.2 File conventions

- Path: `assets/sprites/<exactClassname>.png` (case-sensitive; must equal the catalog `cls` string). GitHub Pages is case-sensitive.
- Master render **1024×1024** (or specified aspect); ship a **512** long-edge web copy. Transparent PNG.
- **Orientation contract:** front/barrel points UP (+Y) in the image (image-top). The editor's `withLocal` frame has +Y forward and already inverts canvas-Y, so an image drawn top-up renders front-forward. **Pilot step MUST visually confirm sprites are not upside-down** before locking the style (if they are, the draw adds a 180° pre-rotate or y-flip — one line).
- **Footprint contract + NO-DISTORTION RULE:** the sprite's drawn extent = the object's **art span** (`art` if present else `size`, real metres — see Component 0). Sprite canvas aspect SHOULD match that box, but the renderer does **not rely** on it: `drawObj` uses **fit-contain** — scale the image by `min(aw/imgW, ad/imgH)` (metre units after reading natural px size), centre it, so a mismatched aspect is letterboxed, never stretched. This also makes **aliases with differing footprints safe** (e.g. `Land_BagFenceShort` → long sandbag sprite renders contained, not squashed).

### 2.3 Asset list (dedup: ~37 classes → ~27 distinct sprites; aliases share a file at load time)

**Weapons (14 distinct):**
| Sprite file | Real anchor (SPRITE NOTE) | Aliases |
|---|---|---|
| M2StaticMG | M2 Browning on M3 tripod: 3-leg triangle, dark receiver, long barrel fwd | M2HD_mini_TripodCamo_US |
| MK19_TriPod_US_EP1 | Mk19: M3 triangle, stubby boxy body, side ammo can | — |
| DSHKM_TK_INS_EP1 | DShKM wheeled: 2 side wheels, finned barrel + oval muzzle brake, tail boom | KORD_high_TK_EP1 |
| AGS_TK_EP1 | AGS-17: small tripod, squat drum-fed body | — |
| TOW_TriPod_US_EP1 | TOW M220: tripod + boxy launch tube + sight block (chunky) | — |
| Metis_TK_EP1 | Metis: very small tripod + thin tube + control box | — |
| SPG9_TK_INS_EP1 | SPG-9: long slender tube, flared venturi rear, low tripod | — |
| Stinger_Pod_US_EP1 | Avenger-style pod: 2 slim rectangular 4-tube blocks, OD/tan | — |
| Igla_AA_pod_TK_EP1 | Dzhigit pod: small pedestal, 2 parallel tubes up/fwd | — |
| ZU23_TK_EP1 | ZU-23-2: twin parallel barrels fwd, 2 side ammo boxes, 2 wheels (wide) | — |
| M119_US_EP1 | M119 105mm: V split-trails rear, 2 wheels at hip, thin barrel + muzzle brake | — |
| D30_TK_EP1 | D-30 122mm: **3 trail legs at 120° (Y/star)**, central jack, barrel over one leg | — |
| M252_US_EP1 | M252 81mm: round baseplate + tube + bipod V, OD | — |
| 2b14_82mm_TK_EP1 | 2B14: same as M252, darker steel | — |

**Fortification / props (13 distinct):**
| Sprite file | Real anchor | Aspect | Aliases |
|---|---|---|---|
| Land_HBarrier_large | HESCO: row of open-top square cells, tan walls + brown fill | 4:1 | Land_HBarrier5 |
| Land_HBarrier3 | HESCO short (3 cells) | 2.5:1 | — |
| Land_HBarrier_corner | HESCO L-corner | 1:1 | — |
| Land_fort_bagfence_long | Sandbag wall: tan brickwork strip | 4:1 | Land_BagFenceLong, Land_BagFenceShort |
| Land_fort_bagfence_corner | Sandbag L-corner | 1:1 | — |
| Land_fort_bagfence_round | Sandbag ring (circular parapet) | 1:1 | — |
| Land_fortified_nest_small_EP1 | Sandbag MG nest: square ring w/ entrance | 1:1 | Land_fortified_nest_small |
| Land_fort_watchtower_EP1 | Watchtower: dark square platform + 4 corner posts | 1:1 | Land_fort_watchtower |
| Land_CamoNetVar_NATO | Camo net: irregular polygon, disruptive pattern (semi-transparent) | 1:1 | Land_CamoNetVar_EAST (green tint) |
| Land_Razorwire | Concertina: line of overlapping silver loops | 5:1 | — |
| Hedgehog | Czech hedgehog: 6-point steel asterisk + centre dot | 1:1 | — |
| Land_CncBlock_Stripes | Jersey barrier, hazard stripes, grey | 1.5:1 | Land_CncBlock (plain grey) |
| RoadCone_L_EP1 | Traffic cone: orange ring + dark base, top-down | 1:1 | — |
| USBasicAmmunitionBox_EP1 | US ammo crate: olive rectangle, latches | 1.4:1 | USLaunchersBox_EP1, TKBasicAmmunitionBox_EP1*, TKVehicleBox_EP1* |

*EAST ammo boxes get a green-tinted variant file if desired; otherwise alias to the US crate. Decision: ship US crate first, add EAST tint in the full set.

The full per-asset prompt strings (preamble + note) are generated into `docs/sprite-prompts.md` as a deliverable so they can be pasted into ChatGPT one at a time.

### 2.4 Editor integration — sprite-or-procedural fallback (~20 LOC)

```js
// alias map: class -> sprite file basename
const SPRITE_ALIAS = { M2HD_mini_TripodCamo_US:'M2StaticMG', KORD_high_TK_EP1:'DSHKM_TK_INS_EP1', /* ... */ };
const SPRITES = {};                  // basename -> {img, ok}
let _spriteDrawQueued = false;       // coalesce burst loads into one repaint
function queueDraw(){ if(_spriteDrawQueued) return; _spriteDrawQueued=true;
  requestAnimationFrame(()=>{ _spriteDrawQueued=false; draw(); }); }
function spriteFor(cls){ const b = SPRITE_ALIAS[cls]||cls; return SPRITES[b]; }
function loadSprite(b){ if(SPRITES[b]) return; const img=new Image();
  SPRITES[b]={img,ok:false};
  img.onload =()=>{ SPRITES[b].ok=true; queueDraw(); };   // debounced (SHOULD-FIX #4)
  img.onerror=()=>{ SPRITES[b].ok=false; };               // silently fall back to TEX
  img.src = `assets/sprites/${b}.png`;
}
// kick off loads for every catalog class (+aliases) at boot
```

In `drawObj`, inside the existing `withLocal(o,H,…)` scaled+rotated metre frame — draw to the **art span** (`art` if present, else `size`), **fit-contain** to avoid distortion (BLOCKER #1 + Component 0):

```js
const [aw, ad] = ART_OF(o.cls);             // = art || size, real metres
const sp = spriteFor(o.cls);
if (USE_SPRITES && sp && sp.ok) {
  const iw = sp.img.naturalWidth, ih = sp.img.naturalHeight;
  const s  = Math.min(aw/iw, ad/ih);        // metre-per-pixel that fits the art box
  const dw = iw*s, dh = ih*s;               // contained draw size (metres)
  ctx.drawImage(sp.img, -dw/2, -dh/2, dw, dh);
} else {
  (TEX[st]||TEX.box)(aw, ad);               // procedural path also draws to art span
}
if (isSel) { /* existing orange selection rect — drawn on `size` (collision box), unchanged */ }
```

Note: the sprite/glyph draws to the **art span** (true visual extent incl. barrel), while hit-testing and the selection rect stay on the **collision `size`** — so a howitzer looks full-length but selects by its carriage, not a giant barrel hitbox.

**Properties:** zero new deps; offline-safe (missing files → procedural); custom user classnames → procedural; **coalesced repaint** (one rAF per burst, not one per image — SHOULD-FIX #4); fit-contain so imperfect-aspect art is letterboxed, never stretched. **Expected behaviour:** on first load users briefly see procedural glyphs that pop to sprites as PNGs arrive — this is intended, not a bug (SHOULD-FIX #5). A **"sprites on/off"** toggle (`USE_SPRITES`, default on) lets users compare and keeps the procedural path first-class.

### 2.5 Pilot first

Generate **M2StaticMG**, **D30_TK_EP1**, **Land_fort_bagfence_long** (a US weapon, the signature Soviet weapon, a long-aspect prop). Wire in the loader, verify in-editor at real draw scale, lock the style, then generate the rest.

---

## 3. Component 2 — Doctrine layout rework

Apply the 7 **TOP CORRECTIONS** from `RESEARCH.md` to all 16 templates in `Server/Init/Init_Defenses.sqf` and the 16 editor presets, **preserving gun counts** (the crew/AI contract: AA/Arty 2→4, Emp 3→6, CP 1→3) and ~footprints.

| Type | Correction applied |
|---|---|
| **AA** | Signature **circular sandbag ring** per weapon (round, not horseshoe). NATO: 2/4 dispersed rings + camo, wider spread. EAST: tighter cluster, mix gun+MANPADS, earth/H-barrier, denser. |
| **Artillery** | NATO = **lazy-W** irregular stagger (±3-4 m lateral, 1-2 m fore/aft), horseshoe parapet opening **rear**, **ammo in a separate pit set back/flank** (not at the gun). EAST D-30 = tighter **arc**, can read the 3-leg splay; ammo still separated. |
| **Emplacement** | **MGs on left+right flanks angled INWARD** (interlocking FPL crossfire). **AT offset to a flank, set back** for standoff with an oblique lane (not centred/forward). Horseshoe opening rear. EAST = more linear/trench-connected + obstacle belt. |
| **Checkpoint** | Linear sequence: warning cones → **S-chicane of offset blocks** → search gap → **overwatch MG with clear lane down the approach** + guard tower. NATO cones+jersey expeditionary; EAST more concrete + 2nd tower. |

Net: this is **repositioning within existing gun counts** + swapping horseshoe→ring for AA + moving ammo back. No change to crew cost, PV protocol, caps, or footprints. The **prop list (`_created`) length changes** (e.g. horseshoe→ring swaps prop counts) — harmless, since orphan cleanup (§6) iterates the whole array regardless; only the **gun (`cat`) count** is contract-critical and is preserved.

**SQF↔editor parity verification (the contract guard):** the Playwright check re-run in §9 step 3 loads each of the 16 presets and asserts `cWpn`/`cAI` equals the expected gun count per type/weight (the same check used in prior sessions, returning `allMatch:true`). A second grep over `Server/Init/Init_Defenses.sqf` counts weapon classnames per template and asserts the same numbers. Both must pass before commit — that is what keeps SQF and editor presets in lockstep (they are authored from the same coordinate data, but the checks prove it).

---

## 4. Component 3 — Fields-of-fire overlay (style A)

Toolbar toggle **"Fields of fire"** (default **off**). When on, each crewable weapon draws a filled translucent wedge in the object's heading, reusing `localToWorld`.

| Category (`cat`) | Arc | Indicative range (grid m) | Colour |
|---|---|---|---|
| mg | 90° | 9 | orange `#D9763C` |
| gl | 75° | 8 | orange |
| at | 25° | 15 | steel-blue `#7fb0c8` |
| aa | full circle (360°) | 11 | olive `#5C6536` |
| arty / mortar | — (indirect: no wedge; optional faint dashed min-range ring) | — | — |

**Arc geometry (explicit, SHOULD-FIX #11):** the wedge is **centred on the object's heading** — it spans `heading ± arc/2`, built by sampling points at `localToWorld(sin θ · range, cos θ · range, H)` for θ across that span and filling back to the apex (the weapon position). The **aa** case is drawn as a full filled circle (it represents hemispheric/all-round coverage projected to plan view — "dome" only as a concept, geometrically a circle).

Ranges are **indicative, not to scale** (real ranges dwarf a 12 m pad) — labelled as such in the panel. Wedge = `rgba(col,.22)` fill + `rgba(col,.55)` edge. Overlap naturally shows interlocking fire. Implementation ≈ a `drawFOF()` pass after `objs.forEach(drawObj)` in `draw()`, gated by the toggle. (Heatmap "C" is a possible later second toggle; out of scope now.)

---

## 5. Component 4 — Shareable layout links

- **Encode:** the existing save payload `{name,parentW,parentD,parentDir,objs}` → compact JSON → UTF-8 bytes → **base64url** → `location.hash = 'd='+enc`.
- **Button:** "Copy share link" beside "Copy SQF". Writes `${location.origin}${location.pathname}#d=…` to clipboard.
- **Decode on boot:** if `location.hash` starts with `#d=`, decode and load it instead of the default preset; show a small "loaded from link" note.
- **Encoding (BLOCKER #2 — modern, real base64url, no deprecated `unescape`):**
  ```js
  const b64u = {
    enc(obj){ const u = new TextEncoder().encode(JSON.stringify(obj));
      let s=''; u.forEach(c=>s+=String.fromCharCode(c));
      return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,''); },
    dec(str){ let b = str.replace(/-/g,'+').replace(/_/g,'/'); while(b.length%4) b+='=';
      const bin = atob(b), u = Uint8Array.from(bin, c=>c.charCodeAt(0));
      return JSON.parse(new TextDecoder().decode(u)); }
  };
  ```
  `TextEncoder`/`TextDecoder` give correct UTF-8 for names containing `×`, `·`, or emoji; `-_` substitution + strip `=` make it genuinely URL-fragment-safe (no `+//=` to be mangled when copied). Decode is wrapped in `try/catch` (`atob` throws on bad input) → malformed hash silently falls back to the default preset, never throws (SHOULD-FIX #17).
- **Size:** a 16-object layout ≈ ~960 chars JSON → ~1.3 kB base64 + URL prefix ≈ ~1.4 kB — within Discord's ~2 kB URL limit. If a layout ever exceeds budget the share button warns and still copies (graceful). Build-order step 5 round-trips a layout whose **name contains `×`, `·`, and an emoji** to prove UTF-8 (SHOULD-FIX #15).

`★ Security:` the hash is read **only** to reconstruct objects (classname strings + numbers drawn on a canvas) — never `eval`'d, never written to DOM as HTML (names go through `textContent`, not `innerHTML`), never sent anywhere. A hostile link can at worst draw silly shapes or set a silly template-name string.

---

## 6. Component 5 — Mission orphan-cleanup (SQF)

Today a destroyed/sold position can leave its sandbags/walls forever (object creep over a long match). Add cleanup so a position's props die with it.

- After `CreateDefenseTemplate` builds `_created` (props) and crew, spawn **one light monitor** per position. **A2-OA safe — no `params`, uses `_this select N` (BLOCKER #3):**
  ```sqf
  [_created, _weapons] spawn {
    private ["_objs","_guns"];
    _objs = _this select 0;
    _guns = _this select 1;
    waitUntil { sleep 30; ({alive _x} count _guns) == 0 };  // all guns dead OR deleted (alive null = false)
    sleep 60;                                                // grace period
    { if (!isNull _x) then { deleteVehicle _x } } forEach _objs;
  };
  ```
- A "sold" defense already deletes its weapon (existing CoIn sell path); when the last gun is gone the monitor reaps the props.
- **Edge cases (from review):** `alive` on a null ref returns `false`, so the loop also exits if guns are *deleted* (sell path or disconnect cleanup), not only killed — correct. If the disconnect handler deletes props first, the monitor's `deleteVehicle` on already-null objects is a **harmless no-op** in A2 (double-delete safe), and the loop still terminates (count hits 0) so **no thread leak**. The monitor **does not read or write the `WFBE_EngDefense_Busy` mutex** (that guards only the build path) — fully independent.
- Cost: one suspended thread per position polling at 30 s — negligible; ends when the position dies. (The heavier `enableSimulation` threat-sleep idea is explicitly **out of scope / ask-first**, noted as future.)
- Keep the existing per-UID disconnect cleanup as-is (belt and suspenders).

---

## 7. Component 6 — Easter eggs (editor only, low-risk)

1. **Konami code** (`↑↑↓↓←→←→ B A`) → brief CSS confetti + loads a hidden **"⛄ Snowman OP"** preset (sandbag-art smiley/snowman) with a `GroupChat`-style toast. Pure client, no effect on export validity.
2. **"CHAOS" tiny link** in the footer → randomly scatters the current objects into a daft but valid layout (still exports fine).

Both are gated, reversible (reload), and never touch the SQF contract.

---

## 8. Non-goals (explicit)

- No framework/build step — single-file offline HTML stays the point.
- No backend / analytics / accounts.
- No `enableSimulation` threat-sleep, no capturable positions, no HC offload (all **ask-first / future**).
- No change to crew counts, caps, PV protocol, or **coordinates/rotation** (only the editor-only draw dimensions change; positions stay 1:1 metres).
- No shipped QA gadgets in the editor (ruler / extent readout / clear-radius ring) — user declined.
- Sprites do not replace the procedural renderer — they layer on top of it.

---

## 9. Build order + verification

0. **Measurement accuracy** → add `art` support (`ART_OF`, fit-contain uses art, hit-test stays on size) + replace all ~35 footprints with cited real-world dimensions → browser check: presets still load, gun counts unchanged, 0 console errors; spot-check a few extents look right vs known sizes. (Phase B `boundingBoxReal` lock deferred to user.)
1. **Sprite pilot** (3: M2 / D-30 / sandbag-long) → loader + fit-contain draw + toggle → Playwright screenshot at real scale, console-clean. **Confirm not upside-down**, lock style.
2. **Full sprite prompt pack** → `docs/sprite-prompts.md` (deliverable; user generates in ChatGPT).
3. **Layout rework** *(needs step-1 sprites available for visual verification of the new positions)* → edit SQF + presets → browser parity check: 16 presets report expected gun counts (`allMatch:true`), 0 console errors; SQF grep: weapon-class counts per template unchanged, no A3 syntax, mutex still balanced.
4. **Fields-of-fire overlay** → toggle → screenshot each category (mg/at/aa visible, centred on heading).
5. **Share links** → round-trip test in Playwright **including a layout name with `×`, `·`, and an emoji** (encode → reload with hash → decoded layout deep-equals original).
6. **Orphan cleanup** → SQF static checks (bracket balance, **no `params`/A3 syntax**, `private` var scoping, mutex untouched) + adversarial review. **Cannot test in-engine here** → must be playtested by the user on the Mini PC / test server before merge to the mission's production branch.
7. **Easter eggs** → manual trigger test (Konami + CHAOS), confirm export still valid.
8. Refresh `doctrine-overview.png`; update README; commit per workstream; push.

Each editor change is verified headless (Playwright, console-clean) before commit. Mission SQF gets static + adversarial review only (no Arma runtime here — **standing caveat: needs an in-game playtest, owned by the user, before production merge**).
