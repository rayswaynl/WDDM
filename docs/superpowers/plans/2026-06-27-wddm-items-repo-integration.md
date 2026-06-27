# WDDM × arma2-co-config-reference — Items Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Derive a classname index + per-item thumbnails from the `arma2-co-config-reference` repo and wire them into WDDM for classname validation, palette expansion, picker thumbnails, and a portrait canvas fallback — without changing the SQF export.

**Architecture:** A dependency-free Python generator (`tools/gen_assets.py`) parses the items repo and commits compact artifacts into WDDM (`assets/data/*.json`, `assets/img/*.jpg`). The single-file app (`index.html`) fetches them at startup exactly as it already fetches sprites, then layers validation + image rendering on top. The items repo is never a runtime dependency.

**Tech Stack:** Python 3.12 (stdlib only) for the generator; vanilla JS/Canvas in `index.html`; Playwright MCP + `python -m http.server 8088` for runtime verification.

**Spec:** `docs/superpowers/specs/2026-06-27-wddm-items-repo-integration-design.md`

---

## File Structure

| File | Create/Modify | Responsibility |
| --- | --- | --- |
| `tools/gen_assets.py` | Create | Parse config → `classnames.json`; copy matching JPGs → `assets/img/`; write `portraits.json`; emit candidate report. Pure functions + `main()`. |
| `tools/test_gen_assets.py` | Create | `unittest` tests for the generator's pure functions (parser, classname extraction, image indexing). |
| `assets/data/classnames.json` | Generated | `{cls: displayName}` for every base-game class. Validation set + autocomplete labels. |
| `assets/data/portraits.json` | Generated | `[cls, …]` — classes with a copied thumbnail. Manifest so the app never requests a missing JPG (mirrors `SPRITE_FILES`). |
| `assets/img/<cls>.jpg` | Generated | One thumbnail per palette/preset classname that has art. |
| `tools/expansion-candidates.md` | Generated | Curation guide for Phase 3. |
| `index.html` | Modify | Fetch artifacts; self-audit; classname-warning + autocomplete; portrait preload + 3-layer canvas fallback; palette + inspector thumbnails; curated CATALOG additions. |

**Conventions to follow (already in `index.html`):** the sprite layer (`SPRITES`/`loadSprite`/`spriteFor`/`SPRITE_FILES`, lines 567–597) is the template for the portrait layer. `META(c)` (line 492) maps a classname to its CATALOG entry. `$('id')` is the `getElementById` shorthand. `queueDraw()` (line 569) coalesces async-load repaints.

**Generator path assumption:** the items repo sits at `C:\Users\Steff\arma2-co-config-reference` (sibling of `WDDM`), overridable via `--ref`.

---

## Task 1: Generator — config parser (`parse_cfg_classes`)

**Files:**
- Create: `tools/gen_assets.py`
- Test: `tools/test_gen_assets.py`

- [ ] **Step 1: Write the failing test**

Create `tools/test_gen_assets.py`:

```python
import unittest
import gen_assets

CFG = '''class CfgVehicles
{
\tclass All
\t{
\t\tscope = 0;
\t\tdisplayName = "Unknown";
\t};
\tclass Land_HBarrier_large : NonStrategic
\t{
\t\tscope = 2;
\t\tdisplayName = "HBarrier (large)";
\t};
\tclass ForwardOnly;
\tclass M2StaticMG : StaticMGWeapon
\t{
\t\tdisplayName = "M2 .50 cal";
\t};
};'''

class TestParse(unittest.TestCase):
    def test_names_and_displaynames(self):
        out = gen_assets.parse_cfg_classes(CFG)
        self.assertIn('Land_HBarrier_large', out)
        self.assertEqual(out['Land_HBarrier_large'], 'HBarrier (large)')
        self.assertEqual(out['M2StaticMG'], 'M2 .50 cal')

    def test_forward_declaration_recorded_empty(self):
        out = gen_assets.parse_cfg_classes(CFG)
        self.assertIn('ForwardOnly', out)
        self.assertEqual(out['ForwardOnly'], '')

    def test_nested_class_captured(self):
        out = gen_assets.parse_cfg_classes(CFG)
        self.assertIn('All', out)
        self.assertEqual(out['All'], 'Unknown')

if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /c/Users/Steff/WDDM/tools && python -m unittest test_gen_assets.TestParse -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'gen_assets'` (or `AttributeError: parse_cfg_classes`).

- [ ] **Step 3: Write minimal implementation**

Create `tools/gen_assets.py` with the parser only:

```python
#!/usr/bin/env python3
"""Generate WDDM editor data from the arma2-co-config-reference items repo.
Dependency-free (stdlib only). Idempotent. See docs/superpowers/plans/2026-06-27-wddm-items-repo-integration.md."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

_FWD   = re.compile(r'^class\s+([A-Za-z0-9_]+)\s*(?::\s*[A-Za-z0-9_]+)?\s*;\s*$')
_HEAD  = re.compile(r'^class\s+([A-Za-z0-9_]+)\s*(?::\s*[A-Za-z0-9_]+)?\s*(\{)?\s*$')
_DN    = re.compile(r'\bdisplayName\s*=\s*"((?:[^"\\]|\\.)*)"')

def parse_cfg_classes(text: str) -> dict:
    """Return {classname: displayName} for every class block in a CfgVehicles dump.
    Captures the displayName declared directly inside each class body; forward
    declarations (`class X;`) are recorded with an empty displayName. First
    displayName wins for a given name."""
    classes: dict[str, str] = {}
    stack: list[dict] = []          # open '{' frames: {'name': str|None}
    pending = None                  # class header awaiting its '{'
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = _FWD.match(line)
        if m:
            classes.setdefault(m.group(1), '')
            continue
        m = _HEAD.match(line)
        if m:
            pending = m.group(1)
            classes.setdefault(pending, '')
            if m.group(2) == '{':
                stack.append({'name': pending}); pending = None
            continue
        if line.startswith('{'):
            stack.append({'name': pending}); pending = None
            continue
        if line.startswith('}'):
            if stack:
                stack.pop()
            pending = None
            continue
        if stack and stack[-1]['name']:
            dn = _DN.search(line)
            if dn and not classes.get(stack[-1]['name']):
                classes[stack[-1]['name']] = dn.group(1)
    return classes
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /c/Users/Steff/WDDM/tools && python -m unittest test_gen_assets.TestParse -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Sanity-run against the real config**

Run: `cd /c/Users/Steff/WDDM/tools && python -c "import gen_assets,pathlib; t=pathlib.Path(r'C:\Users\Steff\arma2-co-config-reference\Config\CfgVehicles.txt').read_text(encoding='utf-8',errors='replace'); d=gen_assets.parse_cfg_classes(t); print(len(d), d.get('Land_HBarrier_large'), d.get('SPG9_TK_INS_EP1'))"`
Expected: a count in the ~16,000 range and non-empty displayNames for both classes.

- [ ] **Step 6: Commit**

```bash
cd /c/Users/Steff/WDDM
git add tools/gen_assets.py tools/test_gen_assets.py
git commit -m "feat(tools): config classname parser for WDDM asset generator"
```

---

## Task 2: Generator — CATALOG/preset classname extraction

**Files:**
- Modify: `tools/gen_assets.py`
- Test: `tools/test_gen_assets.py`

- [ ] **Step 1: Write the failing test**

Append to `tools/test_gen_assets.py`:

```python
HTML = """
const CATALOG=[
  {grp:'Walls', cls:'Land_HBarrier_large', size:[2.5,0.6], style:'hbarrier'},
  {grp:'MG / GL', cls:'M2StaticMG', size:[1,1.4], style:'mg', cat:'mg'},
];
const PRESETS={ demo:{ name:'x', tpl:'T', objs:[ ['Hedgehog',[0,0,0],0], ['Land_HBarrier_large',[2,0,0],0] ] } };
"""

class TestExtract(unittest.TestCase):
    def test_extracts_catalog_and_preset_classnames(self):
        out = gen_assets.extract_classnames(HTML)
        self.assertEqual(out, {'Land_HBarrier_large', 'M2StaticMG', 'Hedgehog'})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /c/Users/Steff/WDDM/tools && python -m unittest test_gen_assets.TestExtract -v`
Expected: FAIL — `AttributeError: module 'gen_assets' has no attribute 'extract_classnames'`.

- [ ] **Step 3: Write minimal implementation**

Add to `tools/gen_assets.py`:

```python
_CATALOG_CLS = re.compile(r"\bcls\s*:\s*'([A-Za-z0-9_]+)'")
_PRESET_CLS  = re.compile(r"\[\s*'([A-Za-z0-9_]+)'\s*,\s*\[")

def extract_classnames(html: str) -> set:
    """Union of every classname referenced in index.html: CATALOG `cls:'X'`
    entries plus PRESET object arrays `['X',[...`. These are the classes whose
    thumbnails the editor can render, so these are the images we copy."""
    return set(_CATALOG_CLS.findall(html)) | set(_PRESET_CLS.findall(html))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /c/Users/Steff/WDDM/tools && python -m unittest test_gen_assets.TestExtract -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /c/Users/Steff/WDDM
git add tools/gen_assets.py tools/test_gen_assets.py
git commit -m "feat(tools): extract catalog+preset classnames from index.html"
```

---

## Task 3: Generator — image index + copy

**Files:**
- Modify: `tools/gen_assets.py`
- Test: `tools/test_gen_assets.py`

- [ ] **Step 1: Write the failing test**

Append to `tools/test_gen_assets.py`:

```python
import tempfile, os
from pathlib import Path as _P

class TestImages(unittest.TestCase):
    def test_index_and_copy(self):
        with tempfile.TemporaryDirectory() as d:
            ref = _P(d) / 'Images' / 'A2' / 'Objects' / 'Fortifications'
            ref.mkdir(parents=True)
            (ref / 'Land_HBarrier_large.jpg').write_bytes(b'JPGDATA')
            (ref / 'Hedgehog.jpg').write_bytes(b'JPGDATA')
            dest = _P(d) / 'out'
            idx = gen_assets.index_images(_P(d) / 'Images')
            copied, missing = gen_assets.copy_images(
                {'Land_HBarrier_large', 'Hedgehog', 'DoesNotExist'}, idx, dest)
            self.assertEqual(set(copied), {'Land_HBarrier_large', 'Hedgehog'})
            self.assertEqual(missing, ['DoesNotExist'])
            self.assertTrue((dest / 'Land_HBarrier_large.jpg').exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /c/Users/Steff/WDDM/tools && python -m unittest test_gen_assets.TestImages -v`
Expected: FAIL — `AttributeError: ... 'index_images'`.

- [ ] **Step 3: Write minimal implementation**

Add to `tools/gen_assets.py`:

```python
import shutil

def index_images(images_root: Path) -> dict:
    """Map {classname: source_path} for every <classname>.jpg under the repo's
    Images/ tree (nested category folders). Built once; later lookups are O(1)."""
    idx: dict[str, Path] = {}
    for p in images_root.rglob('*.jpg'):
        idx.setdefault(p.stem, p)
    return idx

def copy_images(classnames, idx: dict, dest: Path):
    """Copy <cls>.jpg for each classname that has art. Returns (copied, missing)."""
    dest.mkdir(parents=True, exist_ok=True)
    copied, missing = [], []
    for cls in sorted(classnames):
        src = idx.get(cls)
        if src:
            shutil.copyfile(src, dest / f'{cls}.jpg')
            copied.append(cls)
        else:
            missing.append(cls)
    return copied, sorted(missing)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /c/Users/Steff/WDDM/tools && python -m unittest test_gen_assets.TestImages -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /c/Users/Steff/WDDM
git add tools/gen_assets.py tools/test_gen_assets.py
git commit -m "feat(tools): image index + selective thumbnail copy"
```

---

## Task 4: Generator — `main()` wiring + candidate report

**Files:**
- Modify: `tools/gen_assets.py`

- [ ] **Step 1: Add `main()` and the candidate report**

Append to `tools/gen_assets.py`:

```python
_DEFENSE_KW = ('Warfare', 'HBarrier', 'Bagfence', 'Nest', 'Hedgehog',
               'Razorwire', 'RazorWire', 'CncBlock', 'Barrier', 'Fort_',
               'Sandbag', 'Bunker', 'Watchtower', 'Pillbox', 'Wall', 'Camo')

def candidate_report(classes: dict, in_catalog: set, have_image: set) -> str:
    """Markdown table of defense-ish classes present in the config + with art but
    NOT yet in the CATALOG — the curation shortlist for palette expansion."""
    rows = []
    for cls in sorted(classes):
        if cls in in_catalog or cls not in have_image:
            continue
        if any(kw in cls for kw in _DEFENSE_KW):
            rows.append(f"| `{cls}` | {classes[cls] or ''} |")
    head = ("# Palette expansion candidates\n\n"
            "Defense/wall/fortification classes that exist in CfgVehicles, have a\n"
            "thumbnail, and are not yet in the CATALOG. Curate from here (Phase 3).\n\n"
            "| classname | displayName |\n| --- | --- |\n")
    return head + "\n".join(rows) + "\n"

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', default=r'..\arma2-co-config-reference',
                    help='path to the arma2-co-config-reference repo')
    ap.add_argument('--wddm', default='.', help='path to the WDDM repo root')
    args = ap.parse_args(argv)
    ref, wddm = Path(args.ref), Path(args.wddm)

    cfg = (ref / 'Config' / 'CfgVehicles.txt').read_text(encoding='utf-8', errors='replace')
    classes = parse_cfg_classes(cfg)

    html = (wddm / 'index.html').read_text(encoding='utf-8', errors='replace')
    wanted = extract_classnames(html)

    idx = index_images(ref / 'Images')
    copied, missing = copy_images(wanted, idx, wddm / 'assets' / 'img')

    data = wddm / 'assets' / 'data'
    data.mkdir(parents=True, exist_ok=True)
    (data / 'classnames.json').write_text(
        json.dumps(classes, ensure_ascii=False, sort_keys=True, separators=(',', ':')),
        encoding='utf-8')
    (data / 'portraits.json').write_text(
        json.dumps(sorted(copied), separators=(',', ':')), encoding='utf-8')

    (wddm / 'tools' / 'expansion-candidates.md').write_text(
        candidate_report(classes, wanted, set(idx)), encoding='utf-8')

    print(f"classes parsed : {len(classes)}")
    print(f"thumbnails copied: {len(copied)}  (missing art: {len(missing)})")
    if missing:
        print("  no image for:", ", ".join(missing))

if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Run the generator end-to-end**

Run: `cd /c/Users/Steff/WDDM && python tools/gen_assets.py --ref ../arma2-co-config-reference --wddm .`
Expected: prints `classes parsed : ~16239`, a `thumbnails copied:` count (~90+), and lists any classnames lacking art.

- [ ] **Step 3: Verify outputs exist**

Run: `cd /c/Users/Steff/WDDM && ls assets/data/ && python -c "import json;d=json.load(open('assets/data/classnames.json',encoding='utf-8'));print('classnames',len(d));p=json.load(open('assets/data/portraits.json'));print('portraits',len(p)); print('HBarrier' in str(d.get('Land_HBarrier_large')))"`
Expected: `classnames.json`, `portraits.json` present; counts printed; `Land_HBarrier_large` resolves to its displayName.

- [ ] **Step 4: Run the full test suite**

Run: `cd /c/Users/Steff/WDDM/tools && python -m unittest -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit (generator + generated artifacts)**

```bash
cd /c/Users/Steff/WDDM
git add tools/gen_assets.py assets/data/ assets/img/ tools/expansion-candidates.md
git commit -m "feat(tools): generate classnames.json, thumbnails, candidate report"
```

---

## Task 5: Runtime — fetch artifacts + startup self-audit (Phase 1a)

**Files:**
- Modify: `index.html` (insert after `preloadSprites()`, line ~597)

- [ ] **Step 1: Add the data loader + self-audit**

Insert immediately after the `preloadSprites()` function (after line 597, before the `Presets` comment block at line 599):

```javascript
/* ===================================================================
   Component 1b — CLASSNAME GROUND-TRUTH (from arma2-co-config-reference
   via tools/gen_assets.py). VALID_CLASSES powers validation + autocomplete;
   PORTRAIT_FILES is the thumbnail manifest (mirrors SPRITE_FILES so we
   never request a missing JPG). Both degrade to empty on fetch failure.
   =================================================================== */
let VALID_CLASSES = new Set();      // every base-game classname
const CLASS_DN = {};                // classname -> displayName
let PORTRAIT_FILES = new Set();     // classnames with a copied thumbnail
function loadClassData(){
  fetch('assets/data/classnames.json').then(r=>r.ok?r.json():{}).then(j=>{
    VALID_CLASSES = new Set(Object.keys(j));
    Object.assign(CLASS_DN, j);
    auditCatalog();
    updateClassWarn();
  }).catch(()=>{});                 // validation simply stays off if absent
  fetch('assets/data/portraits.json').then(r=>r.ok?r.json():[]).then(a=>{
    PORTRAIT_FILES = new Set(a); preloadPortraits(); queueDraw();
  }).catch(()=>{});
}
function auditCatalog(){            // dev-facing: surface typo'd palette classnames
  if(!VALID_CLASSES.size) return;
  const bad = CATALOG.map(o=>o.cls).filter(c=>!VALID_CLASSES.has(c));
  if(bad.length){ console.warn('[WDDM] CATALOG classnames not in base-game config:', bad); }
  const b=$('auditBadge'); if(b){ b.textContent = bad.length? `⚠ ${bad.length} unverified` : ''; b.title = bad.join(', '); }
}
```

- [ ] **Step 2: Call the loader at startup**

Find the existing startup call to `preloadSprites()` (search `preloadSprites()` invocation — it is called once on boot, distinct from its definition). Add `loadClassData();` on the next line.

Run: `cd /c/Users/Steff/WDDM && grep -n "preloadSprites()" index.html`
Expected: two hits — the definition (line ~594) and the boot call. Add `loadClassData();` after the boot call.

- [ ] **Step 3: Add the audit badge to the palette panel header**

Modify line 196 from:

```html
      <label>Add object — pick a class</label>
```

to:

```html
      <label>Add object — pick a class <span class="badge" id="auditBadge" style="background:#7a2d2d"></span></label>
```

- [ ] **Step 4: Add `preloadPortraits` + `updateClassWarn` stubs (filled in later tasks)**

Insert after the `loadClassData`/`auditCatalog` block:

```javascript
function preloadPortraits(){}      // implemented in Task 7 (portrait layer)
function updateClassWarn(){}       // implemented in Task 6 (inspector warning)
```

- [ ] **Step 5: Verify the page still loads (Playwright)**

Start the dev server (background): `cd /c/Users/Steff/WDDM && python -m http.server 8088`
Then with the Playwright MCP: navigate to `http://localhost:8088/`, wait for load, read console messages.
Expected: page renders; **0 errors** in console (a `console.warn` about unverified CATALOG classnames is acceptable and expected if any exist); evaluate `VALID_CLASSES.size` → a number in the ~16,000 range.

- [ ] **Step 6: Commit**

```bash
cd /c/Users/Steff/WDDM
git add index.html
git commit -m "feat: load base-game classname ground-truth + CATALOG self-audit"
```

---

## Task 6: Runtime — classname warning + autocomplete (Phase 1b)

**Files:**
- Modify: `index.html` (inspector HTML ~259; custom-add ~1474; iClass handler ~1525; selection sync ~1511)

- [ ] **Step 1: Add the warning element + datalist to the inspector**

Modify lines 258–259 from:

```html
        <label>Classname</label>
        <input id="iClass" type="text">
```

to:

```html
        <label>Classname <span id="iClassWarn" class="warn" style="display:none" title="Not found in the Arma 2 base-game config">⚠ unknown</span></label>
        <input id="iClass" type="text" list="classlist" autocomplete="off">
        <datalist id="classlist"></datalist>
```

- [ ] **Step 2: Implement `updateClassWarn` + a capped autocomplete**

Replace the `function updateClassWarn(){}` stub (from Task 5 Step 4) with:

```javascript
function updateClassWarn(){
  const el=$('iClass'), w=$('iClassWarn'); if(!el||!w) return;
  const v=(el.value||'').trim();
  w.style.display = (v && VALID_CLASSES.size && !VALID_CLASSES.has(v)) ? '' : 'none';
}
function refreshClassList(prefix){          // capped dynamic datalist (<=30 matches)
  const dl=$('classlist'); if(!dl) return;
  const p=(prefix||'').toLowerCase(); dl.innerHTML='';
  if(p.length<2) return;
  let n=0;
  for(const c of VALID_CLASSES){
    if(c.toLowerCase().includes(p)){
      const op=document.createElement('option');
      op.value=c; op.label=CLASS_DN[c]||''; dl.appendChild(op);
      if(++n>=30) break;
    }
  }
}
```

- [ ] **Step 3: Wire the inspector field (extend the existing handler, lines 1525–1527)**

Lines 1525–1527 currently read:

```javascript
['iX','iY','iZ','iDir','iClass'].forEach(id=>$(id).addEventListener('input',()=>{ const o=objs.find(x=>x.id===sel); if(!o)return;
  o.cls=$('iClass').value.trim(); o.x=parseFloat($('iX').value)||0; o.y=parseFloat($('iY').value)||0; o.z=parseFloat($('iZ').value)||0; o.dir=((parseFloat($('iDir').value)||0)%360+360)%360; draw(); }));
['iX','iY','iZ','iDir','iClass'].forEach(id=>$(id).addEventListener('change',syncUI));
```

Add a dedicated `iClass` listener immediately after them:

```javascript
$('iClass').addEventListener('input',()=>{ updateClassWarn(); refreshClassList($('iClass').value); });
```

- [ ] **Step 4: Update the warning when selection changes (line 1511)**

Line 1511 currently reads:

```javascript
  if(o){ $('iClass').value=o.cls; $('iX').value=o.x; $('iY').value=o.y; $('iZ').value=o.z; $('iDir').value=o.dir; }
```

Append `updateClassWarn();` inside that block:

```javascript
  if(o){ $('iClass').value=o.cls; $('iX').value=o.x; $('iY').value=o.y; $('iZ').value=o.z; $('iDir').value=o.dir; updateClassWarn(); }
```

- [ ] **Step 5: Guard the custom-add prompt (line 1474)**

Line 1474 currently reads:

```javascript
$('addCustomBtn').onclick=()=>{ const c=prompt('Enter exact Arma classname:'); if(c)addObj(c.trim()); };
```

Replace with:

```javascript
$('addCustomBtn').onclick=()=>{ const c=prompt('Enter exact Arma classname:'); if(!c) return;
  const cls=c.trim();
  if(VALID_CLASSES.size && !VALID_CLASSES.has(cls) && !confirm(`"${cls}" is not in the Arma 2 base-game config.\nAdd it anyway?`)) return;
  addObj(cls); };
```

- [ ] **Step 6: Verify (Playwright)**

With the dev server running, navigate to `http://localhost:8088/`. Then via Playwright `browser_evaluate`:
- `(()=>{ const e=document.getElementById('iClass'); e.value='Land_Razorwire'; updateClassWarn(); return document.getElementById('iClassWarn').style.display; })()` → expect `''` only if `Land_Razorwire` is invalid; for a known-good value `M2StaticMG` expect `'none'`.
- `(()=>{ refreshClassList('hbarrier'); return document.getElementById('classlist').options.length; })()` → expect a number between 1 and 30.

Expected: warning shows for an unknown classname, hidden for a known one; datalist populates.

- [ ] **Step 7: Commit**

```bash
cd /c/Users/Steff/WDDM
git add index.html
git commit -m "feat: classname validation warning + autocomplete on editor inputs"
```

---

## Task 7: Runtime — portrait layer + 3-layer canvas fallback (Phase 2a)

**Files:**
- Modify: `index.html` (portrait infra near the sprite layer; `drawObj` lines 1405–1412)

- [ ] **Step 1: Implement the portrait cache + `preloadPortraits`**

Replace the `function preloadPortraits(){}` stub (Task 5 Step 4) with a sprite-mirrored portrait layer:

```javascript
/* Portrait layer — reference thumbnails from assets/img/<cls>.jpg. Used as the
   middle render layer (below real top-down sprites, above procedural glyphs) and
   for picker/inspector thumbnails. Only PORTRAIT_FILES members are requested. */
const PORTRAITS = {};                       // cls -> {img, ok}
function loadPortrait(cls){
  if(PORTRAITS[cls] || !PORTRAIT_FILES.has(cls)) return;
  const img=new Image(); PORTRAITS[cls]={img,ok:false};
  img.onload =()=>{ PORTRAITS[cls].ok=(img.naturalWidth>0); if(PORTRAITS[cls].ok) queueDraw(); };
  img.onerror=()=>{ PORTRAITS[cls].ok=false; };
  img.src=`assets/img/${cls}.jpg`;
}
function portraitFor(cls){ const p=PORTRAITS[cls]; return (p&&p.ok)?p:null; }
function preloadPortraits(){ CATALOG.forEach(o=>loadPortrait(o.cls)); }
```

- [ ] **Step 2: Insert the portrait layer into `drawObj` (lines 1407–1412)**

The current sprite/fallback block (lines 1407–1412) reads:

```javascript
    if(sp && sp.ok){                                   // SPRITE: fit-contain into ART span (no stretch)
      const iw=sp.img.naturalWidth, ih=sp.img.naturalHeight, s=Math.min(aw/iw, ad/ih);
      ctx.drawImage(sp.img, -(iw*s)/2, -(ih*s)/2, iw*s, ih*s);
    } else {
      (TEX[st]||TEX.box)(aw,ad);                       // FALLBACK: procedural glyph at ART span
    }
```

Replace with a 3-layer fallback (sprite → portrait → glyph):

```javascript
    if(sp && sp.ok){                                   // LAYER A — real top-down sprite, fit-contain
      const iw=sp.img.naturalWidth, ih=sp.img.naturalHeight, s=Math.min(aw/iw, ad/ih);
      ctx.drawImage(sp.img, -(iw*s)/2, -(ih*s)/2, iw*s, ih*s);
    } else {
      const pt = USE_SPRITES ? portraitFor(o.cls) : null;
      if(pt){                                          // LAYER B — portrait thumbnail (approximate; dimmed)
        const iw=pt.img.naturalWidth, ih=pt.img.naturalHeight, s=Math.min(aw/iw, ad/ih);
        const a0=ctx.globalAlpha; ctx.globalAlpha=a0*0.55;
        ctx.drawImage(pt.img, -(iw*s)/2, -(ih*s)/2, iw*s, ih*s);
        ctx.globalAlpha=a0;
      } else {
        (TEX[st]||TEX.box)(aw,ad);                     // LAYER C — procedural glyph at ART span
      }
    }
```

- [ ] **Step 3: Verify the fallback chain (Playwright)**

Pre-req: `assets/img/` and `portraits.json` exist (Task 4). With the dev server running, navigate to `http://localhost:8088/`. Via `browser_evaluate`:
- `(()=>{ return PORTRAIT_FILES.size; })()` → expect > 0.
- Load a preset that uses an item WITH a portrait but WITHOUT a real sprite, then confirm no console errors and `Object.values(PORTRAITS).some(p=>p.ok)` → `true`.

Take a screenshot of the canvas with a preset loaded; confirm objects render (sprite, dimmed portrait, or glyph) with no broken-image artifacts.

- [ ] **Step 4: Commit**

```bash
cd /c/Users/Steff/WDDM
git add index.html
git commit -m "feat: portrait thumbnail canvas fallback (sprite -> portrait -> glyph)"
```

---

## Task 8: Runtime — palette + inspector thumbnails (Phase 2b)

**Files:**
- Modify: `index.html` (palette HTML ~197–201; inspector HTML ~259; `renderPalette` ~1131; selection sync ~1511)

- [ ] **Step 1: Add the palette preview image**

After the palette button bar (lines 198–201), insert a preview `<img>`:

```html
      <div class="btnbar">
        <button class="primary" id="addBtn">+ Add to centre</button>
        <button id="addCustomBtn">+ Custom…</button>
      </div>
      <img id="palThumb" alt="" style="display:none;max-width:100%;max-height:120px;margin-top:6px;border:1px solid #2a2f36;border-radius:4px;background:#11141a">
```

- [ ] **Step 2: Add the inspector thumbnail**

After the inspector classname input + datalist (added in Task 6 Step 1), insert:

```html
        <img id="iThumb" alt="" style="display:none;max-width:100%;max-height:110px;margin:4px 0;border:1px solid #2a2f36;border-radius:4px;background:#11141a">
```

- [ ] **Step 3: Add a thumbnail helper + wire the palette select**

Add this helper next to `renderPalette` (after line 1147):

```javascript
function setThumb(imgId, cls){            // show assets/img/<cls>.jpg if we have it, else hide
  const el=$(imgId); if(!el) return;
  if(cls && PORTRAIT_FILES.has(cls)){ el.src=`assets/img/${cls}.jpg`; el.style.display=''; }
  else { el.removeAttribute('src'); el.style.display='none'; }
}
```

At the end of `renderPalette` (after line 1146, before the closing `}` at 1147), refresh the preview and add a change listener once:

```javascript
  setThumb('palThumb', s.value);
  if(!s._thumbWired){ s._thumbWired=true; s.addEventListener('change',()=>setThumb('palThumb', s.value)); }
```

- [ ] **Step 4: Wire the inspector thumbnail to selection (line 1511)**

The line (already edited in Task 6 Step 4) now reads:

```javascript
  if(o){ $('iClass').value=o.cls; $('iX').value=o.x; $('iY').value=o.y; $('iZ').value=o.z; $('iDir').value=o.dir; updateClassWarn(); }
```

Append `setThumb('iThumb', o.cls);`:

```javascript
  if(o){ $('iClass').value=o.cls; $('iX').value=o.x; $('iY').value=o.y; $('iZ').value=o.z; $('iDir').value=o.dir; updateClassWarn(); setThumb('iThumb', o.cls); }
```

- [ ] **Step 5: Verify (Playwright)**

With the dev server running, navigate to `http://localhost:8088/`. Via `browser_evaluate`:
- `(()=>{ const s=document.getElementById('palette'); s.value=Array.from(s.options).map(o=>o.value).find(v=>PORTRAIT_FILES.has(v)); setThumb('palThumb', s.value); const t=document.getElementById('palThumb'); return [t.style.display, t.getAttribute('src')]; })()` → expect `['', 'assets/img/<cls>.jpg']`.

Take a screenshot confirming the preview image renders under the palette.

- [ ] **Step 6: Commit**

```bash
cd /c/Users/Steff/WDDM
git add index.html
git commit -m "feat: palette preview + inspector thumbnails from items repo"
```

---

## Task 9: Export regression gate (no SQF drift)

**Files:**
- No source change — verification only.

- [ ] **Step 1: Capture a baseline from before this branch**

Run: `cd /c/Users/Steff/WDDM && git stash list; git show main:index.html > /tmp/wddm_main_index.html 2>/dev/null || git show 238341d:index.html > /tmp/wddm_main_index.html`
(Use the pre-feature `main` tip `238341d`.)

- [ ] **Step 2: Compare export output for a fixed preset (Playwright, both versions)**

For BOTH the current `index.html` (served at `http://localhost:8088/`) and the baseline (serve `/tmp/wddm_main_index.html` on a second port, e.g. copy it to a temp dir and `python -m http.server 8089`), run the same sequence via Playwright:
- `loadPreset('wall_straight'); ` then read the export textarea (find its id via `grep -n "buildOut" index.html` and the element it writes to).
- Capture the exported SQF string from each.

- [ ] **Step 3: Assert byte-identical**

The two exported SQF strings for `wall_straight` (and one weapon preset, e.g. a manned defense) MUST be identical. If they differ, the editor-only contract is broken — stop and diagnose before proceeding.
Expected: identical strings.

- [ ] **Step 4: Commit (record the verification in the branch log — no file change)**

No commit needed if no files changed. If a regression fixture script was added under `tools/`, commit it:

```bash
cd /c/Users/Steff/WDDM
git add tools/ 2>/dev/null && git commit -m "test: SQF export byte-identical regression check" || echo "no fixture file to commit"
```

---

## Task 10: Palette expansion (Phase 3) — curated batch

**Files:**
- Modify: `index.html` (CATALOG, lines 372–490)
- Re-run: `tools/gen_assets.py`

> This phase is iterative curation, not fixed code. The validation (Task 5–6) and image pipeline (Task 4, 7–8) de-risk it: any bad classname trips the self-audit badge, and images are copied automatically on re-run.

- [ ] **Step 1: Generate the candidate shortlist**

Run: `cd /c/Users/Steff/WDDM && python tools/gen_assets.py --ref ../arma2-co-config-reference --wddm . && cat tools/expansion-candidates.md | head -60`
Expected: a markdown table of defense/wall/fortification classes not yet in the CATALOG, each with a thumbnail available.

- [ ] **Step 2: Curate with the user**

Pick a vetted batch (target ~30–50). For each chosen classname, author a CATALOG entry using the existing field shape. Reuse an existing `style` glyph and a sensible `size`/`cat`. Example entry shape (matches line 407's format):

```javascript
{grp:'Fortifications', cls:'<ChosenClassname>', size:[2.0,1.0], style:'hbarrier'}, // 0 AI wall
```

For static weapons, include `cat` so AI cost counts:

```javascript
{grp:'MG / GL', cls:'<ChosenWeaponClass>', size:[1.0,1.4], style:'mg', cat:'mg'},
```

Insert each into the appropriate `grp` block within `CATALOG` (lines 372–490), grouping with like items so the palette `<optgroup>` stays coherent.

- [ ] **Step 3: Re-run the generator to copy new thumbnails**

Run: `cd /c/Users/Steff/WDDM && python tools/gen_assets.py --ref ../arma2-co-config-reference --wddm .`
Expected: new `assets/img/<cls>.jpg` files for the added classnames; `portraits.json` updated; `thumbnails copied` count risen by the batch size.

- [ ] **Step 4: Verify the additions (Playwright)**

With the dev server running, navigate to `http://localhost:8088/`. Confirm:
- Console: **0 errors**; the `auditBadge` is empty (every new classname validated) — if it shows a count, fix the offending classname(s).
- The new items appear in the palette dropdown under their group, each with a preview thumbnail.

- [ ] **Step 5: Commit**

```bash
cd /c/Users/Steff/WDDM
git add index.html assets/img/ assets/data/portraits.json tools/expansion-candidates.md
git commit -m "feat: expand defense palette with curated base-game buildables"
```

---

## Task 11: Finalize

- [ ] **Step 1: Full generator test pass**

Run: `cd /c/Users/Steff/WDDM/tools && python -m unittest -v`
Expected: all PASS.

- [ ] **Step 2: Final Playwright smoke**

Navigate to `http://localhost:8088/`, load 2–3 presets across defense + base-layout modes, toggle the `sprites` checkbox on/off, select objects. Expected: 0 console errors; thumbnails render; portrait fallback engages with sprites on; glyphs draw with sprites off.

- [ ] **Step 3: README note**

Add a short section to `README.md` documenting `tools/gen_assets.py` (what it reads, what it generates, how to re-run after editing the CATALOG) and the validation/thumbnail features.

- [ ] **Step 4: Commit + stop**

```bash
cd /c/Users/Steff/WDDM
git add README.md
git commit -m "docs: document the items-repo asset generator + validation features"
```

Then stop the background dev server.

---

## Self-Review (completed by plan author)

- **Spec coverage:** G1 validation → Tasks 5–6; G2 expansion → Tasks 4 (report) + 10; G3 picker thumbnails → Task 8; G4 canvas portrait fallback → Task 7. Generator foundation → Tasks 1–4. Export-unchanged (NG2) → Task 9 gate. Warn-only (NG3) → Task 6 (confirm-guard, not block). No-bulk-bundle (NG4) → Task 3 copies only referenced classnames.
- **Type/name consistency:** `VALID_CLASSES`, `CLASS_DN`, `PORTRAIT_FILES`, `loadClassData`, `auditCatalog`, `updateClassWarn`, `refreshClassList`, `preloadPortraits`, `loadPortrait`, `portraitFor`, `setThumb` are defined once and referenced consistently. Stubs (Task 5 Step 4) are replaced in Tasks 6–7 before first use at runtime. Generator: `parse_cfg_classes`, `extract_classnames`, `index_images`, `copy_images`, `candidate_report`, `main` consistent across tasks/tests.
- **Placeholders:** none — Task 10 is explicitly iterative curation with a worked entry shape, not a TODO.
