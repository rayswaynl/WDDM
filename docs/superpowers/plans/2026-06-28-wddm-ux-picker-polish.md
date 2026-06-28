# WDDM UX Picker Polish — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace WDDM's 204-item native `<select>` palette with a hybrid thumbnail picker (inline searchable grid + browse modal), fix the duplicate-optgroup wart, and tidy the left-panel IA — editor-chrome only, SQF export unchanged.

**Architecture:** A new picker module in `index.html` (vanilla JS + CSS, no new files) renders tiles from a mode-filtered, category-deduped item list and drives both an inline left-panel grid and a modal from shared code. The native `#palette` select, `#addBtn`, and `#palThumb` are removed.

**Tech Stack:** Vanilla JS/Canvas/CSS in the single `index.html`; Playwright MCP + `python -m http.server 8088` for verification.

**Spec:** `docs/superpowers/specs/2026-06-28-wddm-ux-picker-polish-design.md`

---

## File Structure

| File | Change | Responsibility |
| --- | --- | --- |
| `index.html` | Modify | Add `.pick-*` CSS; add picker module JS; replace the palette markup; add the browse modal; reorder/collapse the left panel; light inspector tidy. Remove `#palette`/`#addBtn`/`#palThumb` + `renderPalette` + palette-thumb wiring. |

**Conventions to follow (existing):** design tokens at `:root` (lines 18–22: `--gunmetal`,
`--steel`, `--steel2`, `--olive`, `--bone`, `--orange`, `--line`); `.chip`/`.chip.on`,
`.btnbar`, `.obj-list`, `.divider`, `.segmented`, `.modebox`; `$('id')` shorthand; helpers
`META(cls)`, `IS_WPN(cls)`, `CAT_OF(cls)`, `CREW_OF(cls)`, `STYLE(cls)`, `TEX`,
`isBaseStructure(o)`, `isFortificationAsset(o)`, `PORTRAIT_FILES` (Set), `addObj(cls)`.
Apply edits by exact-string match (line numbers drift as you edit).

---

## Task 1: Inline thumbnail picker (replaces the native select)

**Files:** Modify `index.html` — CSS in `<style>`; new JS near `renderPalette`; markup at lines ~196–202; wiring in `setMode`/`setFortOnly`.

- [ ] **Step 1: Add picker CSS** — insert before `</style>` (after line ~102, the scrollbar rules):

```css
  .pick-search{display:flex;align-items:center;gap:7px;margin-top:4px}
  .pick-search input{flex:1}
  .pick-cats{display:flex;flex-wrap:wrap;gap:5px;margin:8px 0}
  .pick-cats .chip{cursor:pointer}
  .pick-scroll{max-height:264px;overflow:auto;border:1px solid var(--line);border-radius:6px;padding:6px;background:#0e1115}
  .pick-cat-h{font-size:10px;text-transform:uppercase;letter-spacing:.6px;color:#9aa3ad;margin:6px 2px 4px}
  .pick-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
  .pick-tile{position:relative;padding:0;border:1px solid var(--line);border-radius:5px;background:var(--gunmetal);
    cursor:pointer;overflow:hidden;display:flex;flex-direction:column}
  .pick-tile:hover{border-color:var(--orange)}
  .pick-tile img{width:100%;height:52px;object-fit:contain;background:#11141a;display:block}
  .pick-lab{font-family:'JetBrains Mono',monospace;font-size:9px;color:#c8d0d8;padding:3px 4px;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;border-top:1px solid var(--steel);text-align:left}
  .pick-wpn{position:absolute;top:2px;right:2px;background:rgba(20,23,27,.85);color:var(--orange);
    font-size:9px;border-radius:8px;padding:0 5px;line-height:15px}
  .pick-empty{font-size:11px;color:#8b939c;padding:10px}
  .modal-back{position:fixed;inset:0;background:rgba(8,10,13,.6);display:none;align-items:center;
    justify-content:center;z-index:30;backdrop-filter:blur(3px)}
  .modal-back.open{display:flex}
  .modal{width:760px;max-width:94vw;max-height:86vh;background:var(--steel);border:1px solid var(--line);
    border-radius:8px;display:flex;flex-direction:column;overflow:hidden}
  .modal-head{display:flex;align-items:center;gap:10px;padding:10px 12px;border-bottom:1px solid var(--line);background:var(--gunmetal)}
  .modal-head h2{font-size:15px}.modal-head .x{cursor:pointer;color:#9aa3ad;font-size:20px;line-height:1;background:none;border:none}
  .modal-body{display:flex;min-height:0;flex:1}
  .modal-side{width:150px;border-right:1px solid var(--line);overflow:auto;padding:8px 6px;display:flex;flex-direction:column;gap:3px}
  .modal-side .chip{cursor:pointer;text-align:left}
  .modal-grid-wrap{flex:1;overflow:auto;padding:10px}
  .modal .pick-grid{grid-template-columns:repeat(5,1fr)}
```

- [ ] **Step 2: Add the picker JS module** — insert immediately BEFORE the `function renderPalette(){` definition (around line 1131):

```javascript
/* ===== Hybrid piece picker (replaces the native <select> palette) ===== */
const _glyphCache = {};                              // cls -> dataURL of procedural glyph
function glyphThumb(cls){
  if(_glyphCache[cls]) return _glyphCache[cls];
  const c=document.createElement('canvas'); c.width=c.height=64;
  const g=c.getContext('2d'); ctxStack(g, ()=>{ g.translate(32,32); g.scale(6,-6);
    g.lineJoin='round'; g.lineCap='round';
    const st=STYLE(cls); try{ (TEX[st]||TEX.box)(5,5); }catch(e){} }, c);
  return (_glyphCache[cls]=c.toDataURL());
}
function ctxStack(g, fn, c){ g.clearRect(0,0,c.width,c.height); g.save(); fn(); g.restore(); }
function pickerItems(){
  return CATALOG.filter(o=> buildMode==='base' ? isBaseStructure(o)
      : (!isBaseStructure(o) && (!fortOnly || isFortificationAsset(o))))
    .map(o=>({cls:o.cls, label:o.label||o.cls, grp:o.grp, isWpn:IS_WPN(o.cls), ai:CREW_OF(o.cls)}));
}
function pickerCategories(){ const s=[]; pickerItems().forEach(i=>{ if(!s.includes(i.grp)) s.push(i.grp); }); return s; }
function tileEl(item){
  const t=document.createElement('button'); t.type='button'; t.className='pick-tile'; t.title=item.cls;
  const img=document.createElement('img'); img.alt=item.label; img.loading='lazy';
  img.src = PORTRAIT_FILES.has(item.cls) ? `assets/img/${item.cls}.jpg` : glyphThumb(item.cls);
  img.onerror=()=>{ img.onerror=null; img.src=glyphThumb(item.cls); };
  const lab=document.createElement('span'); lab.className='pick-lab'; lab.textContent=item.label;
  t.appendChild(img); t.appendChild(lab);
  if(item.isWpn){ const b=document.createElement('span'); b.className='pick-wpn'; b.textContent=item.ai>0?('⚔'+item.ai):'⚔'; t.appendChild(b); }
  t.onclick=()=>addObj(item.cls);
  return t;
}
let _pickCat='All', _pickQ='';
function _filtered(){
  const q=_pickQ.toLowerCase();
  return pickerItems().filter(i=> (_pickCat==='All'||i.grp===_pickCat) &&
    (!q || i.cls.toLowerCase().includes(q) || i.label.toLowerCase().includes(q)));
}
function _renderGrid(host, items, grouped){
  host.innerHTML='';
  if(!items.length){ const e=document.createElement('div'); e.className='pick-empty'; e.textContent='No pieces match'; host.appendChild(e); return; }
  if(grouped){
    const cats=[]; items.forEach(i=>{ if(!cats.includes(i.grp)) cats.push(i.grp); });
    cats.forEach(c=>{ const h=document.createElement('div'); h.className='pick-cat-h'; h.textContent=c; host.appendChild(h);
      const g=document.createElement('div'); g.className='pick-grid'; items.filter(i=>i.grp===c).forEach(i=>g.appendChild(tileEl(i))); host.appendChild(g); });
  } else { const g=document.createElement('div'); g.className='pick-grid'; items.forEach(i=>g.appendChild(tileEl(i))); host.appendChild(g); }
}
function renderPicker(){
  const chipHost=$('pickCats');
  if(chipHost){ chipHost.innerHTML='';
    ['All',...pickerCategories()].forEach(c=>{ const ch=document.createElement('span');
      ch.className='chip'+(c===_pickCat?' on':''); ch.textContent=c;
      ch.onclick=()=>{ _pickCat=c; renderPicker(); }; chipHost.appendChild(ch); }); }
  _renderGrid($('pickGrid'), _filtered(), _pickCat==='All' && !_pickQ);
  if($('pickModalBack') && $('pickModalBack').classList.contains('open')) renderModal();
}
```

- [ ] **Step 3: Replace the palette markup** — change lines ~196–202 from:

```html
      <label>Add object — pick a class <span class="badge" id="auditBadge" style="background:#7a2d2d"></span></label>
      <select id="palette"></select>
      <div class="btnbar">
        <button class="primary" id="addBtn">+ Add to centre</button>
        <button id="addCustomBtn">+ Custom…</button>
      </div>
      <img id="palThumb" alt="" style="display:none;max-width:100%;max-height:120px;margin-top:6px;border:1px solid #2a2f36;border-radius:4px;background:#11141a">
```

to:

```html
      <label>Add object — click a piece <span class="badge" id="auditBadge" style="background:#7a2d2d"></span></label>
      <div class="pick-search"><input id="pickSearch" type="text" placeholder="Search pieces…" autocomplete="off"></div>
      <div class="pick-cats" id="pickCats"></div>
      <div class="pick-scroll" id="pickGrid"></div>
      <div class="btnbar">
        <button id="browseAll">Browse all pieces…</button>
        <button id="addCustomBtn">+ Custom…</button>
      </div>
```

- [ ] **Step 4: Wire search + replace renderPalette calls.** (a) Delete the entire `function renderPalette(){ … }` body (lines ~1131–1147) — it is fully replaced by `renderPicker`. (b) In `setFortOnly` and `setMode`, change every `renderPalette()` call to `renderPicker()`. (c) Find the boot/init code that calls `renderPalette()` on startup and change it to `renderPicker()`. (d) Remove the `#addBtn` click handler line (`$('addBtn').onclick=()=>addObj($('palette').value);`) and the palette-change `setThumb('palThumb', …)` listener + its one-time wiring inside the old renderPalette (already deleted). (e) Add the search listener near the other `$('…').addEventListener` wiring:

```javascript
$('pickSearch').addEventListener('input', ()=>{ _pickQ=$('pickSearch').value.trim(); renderPicker(); });
```

Run `grep -n "renderPalette\|#palette\|'palette'\|addBtn\|palThumb" index.html` and confirm ZERO remaining references except inside the deleted region (there should be none left).

- [ ] **Step 5: Stub `renderModal` (filled in Task 2)** — add near `renderPicker`:

```javascript
function renderModal(){}   // implemented in Task 2 (browse modal)
```

- [ ] **Step 6: Verify (Playwright)** — serve `python -m http.server 8088` (background); via the Playwright MCP navigate to `http://localhost:8088/`:
  - `browser_console_messages` → 0 errors.
  - `() => document.querySelectorAll('#pickGrid .pick-tile').length` → > 50 (defense items render as tiles).
  - `() => { const c=new Set(Array.from(document.querySelectorAll('#pickCats .chip')).map(x=>x.textContent)); return c.size === Array.from(document.querySelectorAll('#pickCats .chip')).length; }` → `true` (no duplicate category chips).
  - `() => { const n=objs.length; document.querySelector('#pickGrid .pick-tile').click(); return objs.length - n; }` → `1` (click-to-add works).
  - `browser_take_screenshot` of the left panel.
  - Stop server.

- [ ] **Step 7: Commit**

```bash
cd /c/Users/Steff/WDDM
git add index.html
git commit -m "feat: inline thumbnail piece picker replaces native select"
```

---

## Task 2: Browse-all modal

**Files:** Modify `index.html` — modal markup; `renderModal` + open/close JS.

- [ ] **Step 1: Add the modal markup** — insert just before the closing `</div>` of `<div class="app">` (after the right panel, before `</div><!-- app -->` / `</body>`; place it as a sibling overlay):

```html
  <div class="modal-back" id="pickModalBack">
    <div class="modal" role="dialog" aria-label="Browse pieces">
      <div class="modal-head">
        <h2>Browse pieces</h2>
        <div class="pick-search" style="flex:1"><input id="pickModalSearch" type="text" placeholder="Search pieces…" autocomplete="off"></div>
        <button class="x" id="pickModalClose" aria-label="Close">×</button>
      </div>
      <div class="modal-body">
        <div class="modal-side" id="pickModalCats"></div>
        <div class="modal-grid-wrap"><div id="pickModalGrid"></div></div>
      </div>
    </div>
  </div>
```

- [ ] **Step 2: Implement `renderModal` + open/close** — replace the `function renderModal(){}` stub with:

```javascript
function renderModal(){
  const side=$('pickModalCats');
  if(side){ side.innerHTML='';
    ['All',...pickerCategories()].forEach(c=>{ const ch=document.createElement('span');
      ch.className='chip'+(c===_pickCat?' on':''); ch.textContent=c;
      ch.onclick=()=>{ _pickCat=c; renderPicker(); }; side.appendChild(ch); }); }
  _renderGrid($('pickModalGrid'), _filtered(), _pickCat==='All' && !_pickQ);
}
function openBrowse(){ $('pickModalBack').classList.add('open'); renderModal(); $('pickModalSearch').focus(); }
function closeBrowse(){ $('pickModalBack').classList.remove('open'); }
$('browseAll').onclick=openBrowse;
$('pickModalClose').onclick=closeBrowse;
$('pickModalBack').addEventListener('click', e=>{ if(e.target===$('pickModalBack')) closeBrowse(); });
$('pickModalSearch').addEventListener('input', ()=>{ _pickQ=$('pickModalSearch').value.trim();
  const s=$('pickSearch'); if(s) s.value=_pickQ; renderPicker(); });
document.addEventListener('keydown', e=>{ if(e.key==='Escape' && $('pickModalBack').classList.contains('open')) closeBrowse(); });
```

Note: tiles in the modal use the same `tileEl`, so clicking one calls `addObj` and the modal **stays open** for rapid multi-add (no close on add) — matches the spec.

- [ ] **Step 3: Verify (Playwright)** — serve + navigate:
  - `() => { openBrowse(); return document.getElementById('pickModalBack').classList.contains('open'); }` → `true`.
  - `() => document.querySelectorAll('#pickModalGrid .pick-tile').length` → > 50.
  - `() => { const n=objs.length; document.querySelector('#pickModalGrid .pick-tile').click(); return [objs.length-n, document.getElementById('pickModalBack').classList.contains('open')]; }` → `[1, true]` (adds + stays open).
  - `() => { const ev=new KeyboardEvent('keydown',{key:'Escape'}); document.dispatchEvent(ev); return document.getElementById('pickModalBack').classList.contains('open'); }` → `false` (Esc closes).
  - 0 console errors. `browser_take_screenshot` of the open modal. Stop server.

- [ ] **Step 4: Commit**

```bash
cd /c/Users/Steff/WDDM
git add index.html
git commit -m "feat: browse-all modal piece picker (shared tile/filter code)"
```

---

## Task 3: Left-panel IA reorg

**Files:** Modify `index.html` — wrap advanced config in `<details>`; reorder; bound heights.

- [ ] **Step 1: Collapse advanced config into a `<details>`.** Wrap the block spanning the
`defenseCtrlsA` open (the `<div id="defenseCtrlsA">` at ~line 140) through the end of
`defenseCtrlsB` (`</div><!-- /defenseCtrlsB -->` at ~line 192) — i.e. the Edit-walls button,
`#fortOnly`, `#wallModeInfo`, `#tplName` label+input, `#structureType`, `#missionTarget` — in:

```html
      <details id="tmplCfg" style="margin-top:8px">
        <summary>Template &amp; wall target</summary>
        <!-- existing defenseCtrlsA + Template variable name + defenseCtrlsB block stays here, unchanged -->
      </details>
```

Move the `<label>Template variable name</label><input id="tplName" …>` (lines ~158–159) and the
two dividers so the `<details>` contains: Edit-walls/fortOnly/wallModeInfo, then tplName, then
structureType + missionTarget. Keep the inner element IDs and the `defenseCtrlsA`/`defenseCtrlsB`
wrapper divs intact (the `setMode` show/hide logic targets them). Remove the now-redundant
divider that separated them.

- [ ] **Step 2: Reorder so the picker sits right under preset.** Ensure top-to-bottom order in
`.scroll` is: Editor mode → Load preset (+ button) → `<details id="tmplCfg">` → divider →
**Pieces (picker block from Task 1)** → divider → Placed objects → hint. (The picker block and
the `<details>` may need to swap position so the picker is prominent and config is tucked above
it; place `<details id="tmplCfg">` immediately after the Load-preset button, then a divider,
then the Pieces block.)

- [ ] **Step 3: Bound the placed-objects list height.** Change the `#objList` usage — add a
wrapper style so it scrolls instead of growing unbounded. Modify the `.obj-list` rule (line ~63)
OR add inline: set `#objList { max-height: 38vh; overflow:auto; }`. Add this CSS near the other
`.obj-list` rules:

```css
  .obj-list{max-height:38vh;overflow:auto}
```

- [ ] **Step 4: Verify (Playwright)** — serve + navigate:
  - 0 console errors.
  - `() => document.getElementById('tmplCfg').tagName` → `'DETAILS'`; `() => document.getElementById('tmplCfg').open` → `false` (closed by default).
  - `() => { setMode('base'); const r = !!document.querySelector('#pickGrid .pick-tile'); setMode('defense'); return r; }` → `true` (mode switch still renders the picker; `defenseCtrls` show/hide didn't break).
  - `() => getComputedStyle(document.getElementById('objList')).overflowY` → `'auto'`.
  - `browser_take_screenshot` of the reorganized left panel. Stop server.

- [ ] **Step 5: Commit**

```bash
cd /c/Users/Steff/WDDM
git add index.html
git commit -m "refactor: left-panel IA — collapse advanced config, bound list heights"
```

---

## Task 4: Visual polish + inspector export tidy

**Files:** Modify `index.html` — minor spacing/grouping; move factory-wall hint.

- [ ] **Step 1: Group the export actions.** In the right panel (lines ~286–291), the Copy SQF
(`#copyBtn`) and Copy share link (`#shareBtn`) buttons — wrap them in a `.btnbar` row so they
read as a pair, and move the verbose `<div class="hint modebox">Factory wall submissions…</div>`
(lines ~288–291) OUT of the export area and INTO the `<details id="tmplCfg">` from Task 3 (it is
the same context — factory-wall workflow). Replace lines ~286–291:

```html
        <button class="primary copybtn" id="copyBtn" style="width:100%">Copy SQF</button>
        <button class="copybtn" id="shareBtn" style="width:100%;margin-top:6px" title="Copy a link that opens this exact layout — great for Discord">Copy share link</button>
        <div class="hint modebox">
          <b>Factory wall submissions:</b> use <code>Edit HQ / Factory walls</code>, keep <code>Fortifications only</code> on,
          then submit the copied SQF or share link with the target name shown above.
        </div>
```

with:

```html
        <div class="btnbar">
          <button class="primary copybtn" id="copyBtn" style="flex:2">Copy SQF</button>
          <button class="copybtn" id="shareBtn" style="flex:1" title="Copy a link that opens this exact layout — great for Discord">Share link</button>
        </div>
```

And add inside the `<details id="tmplCfg">` (Task 3), at its end:

```html
        <div class="hint">
          <b>Factory wall submissions:</b> keep <code>Fortifications only</code> on, then submit the copied SQF or share link with the target name shown above.
        </div>
```

- [ ] **Step 2: Trim the left-panel hint.** The bottom `.hint` (lines ~209–214) duplicates mode
guidance now shown by the segmented control. Shorten it to:

```html
      <div class="hint">
        Click an object on the canvas or list to select. Drag the body to move, drag the handle to rotate. Arrow keys nudge (Shift = 1&nbsp;m).
      </div>
```

- [ ] **Step 3: Verify (Playwright)** — serve + navigate:
  - 0 console errors.
  - `() => [!!document.getElementById('copyBtn'), !!document.getElementById('shareBtn')]` → `[true, true]` (export buttons intact).
  - `() => { copyOut && copyOut(); return true; }` is not required; instead confirm `#copyBtn` still triggers its handler by checking it exists and `#out` has SQF text: `() => document.getElementById('out').value.length > 0` → `true`.
  - `browser_take_screenshot` full page. Stop server.

- [ ] **Step 4: Commit**

```bash
cd /c/Users/Steff/WDDM
git add index.html
git commit -m "polish: group export actions, relocate factory-wall hint, trim hints"
```

---

## Task 5: Full verification + export regression gate + finish

**Files:** No source change — verification only.

- [ ] **Step 1: Export byte-identical gate.** Extract the pre-polish baseline and compare SQF
output for fixed presets (same method as the items work):
  - `git show main:index.html > /c/Users/Steff/AppData/Local/Temp/claude/C--/7f692bf3-bf26-4f69-a5a8-9b48e9647148/scratchpad/wddm_polish_base/index.html` (mkdir -p the dir first).
  - Serve current on 8088 (repo root) and the baseline on 8089 (the temp dir).
  - Via Playwright on each: for presets `wall_straight`, `mg_west_v1`, `fortress_west_8ai`,
    `hq_concrete_walk_exit` — run `() => { loadPreset('<key>'); return buildOut(); }` and capture.
  - Assert each current string === baseline string. **Any difference = FAIL** (the picker must
    not touch export). Stop both servers; delete the temp dir.

- [ ] **Step 2: Full smoke (Playwright).** Serve 8088:
  - 0 console errors on load.
  - Inline picker: search "trench" → only trench tiles; click a category chip → filters; "All"
    → grouped sections present.
  - Click-add inline AND via modal both increment `objs`.
  - `setMode('base')` shows base categories; `setMode('defense')` shows defense; `fortOnly`
    toggle filters.
  - Glyph fallback: a tile for an art-less class (e.g. `Land_fort_watchtower_EP1`) has an `img`
    with a `data:` src (not a 404) — `() => { const t=[...document.querySelectorAll('#pickGrid .pick-tile')].find(el=>el.title==='Land_fort_watchtower_EP1'); return t? t.querySelector('img').src.startsWith('data:') : 'not-in-defense-mode'; }` (acceptable if not in current mode).
  - `browser_take_screenshot` final. Stop server.

- [ ] **Step 3: README note.** Add a one-paragraph note to `README.md` that the palette is now a
searchable thumbnail picker (inline grid + Browse-all modal). Commit:

```bash
cd /c/Users/Steff/WDDM
git add README.md
git commit -m "docs: note the new thumbnail piece picker"
```

- [ ] **Step 4: Finish** — use `superpowers:finishing-a-development-branch` (verify, then
present merge/PR options).

---

## Self-Review (completed by plan author)

- **Spec coverage:** G1 hybrid picker → Tasks 1 (inline) + 2 (modal); G2 dedup optgroups →
  Task 1 (category-deduped `pickerCategories`/grouped render, native select removed); G3 IA
  reorg → Task 3; G4 visual polish + inspector tidy → Task 4. NG1 export-unchanged → Task 5
  gate. Glyph fallback (spec §Components 2) → Task 1 `glyphThumb`. Testing → Tasks' Playwright
  steps + Task 5.
- **Name consistency:** `pickerItems`, `pickerCategories`, `tileEl`, `glyphThumb`, `_filtered`,
  `_renderGrid`, `renderPicker`, `renderModal`, `openBrowse`/`closeBrowse`, `_pickCat`/`_pickQ`,
  and IDs `#pickSearch`/`#pickCats`/`#pickGrid`/`#browseAll`/`#pickModalBack`/`#pickModalCats`/
  `#pickModalGrid`/`#pickModalSearch`/`#pickModalClose`/`#tmplCfg` are used consistently across
  tasks. `renderModal` stub (Task 1 Step 5) replaced in Task 2 before first call.
- **Placeholders:** none — every step has concrete code/edits and exact verification.
