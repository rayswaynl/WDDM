#!/usr/bin/env python3
"""Generate WDDM editor data from the arma2-co-config-reference items repo.
Dependency-free (stdlib only). Idempotent. See docs/superpowers/plans/2026-06-27-wddm-items-repo-integration.md."""
from __future__ import annotations
import argparse, json, re, shutil
from pathlib import Path

_FWD   = re.compile(r'^class\s+([A-Za-z0-9_]+)\s*(?::\s*[A-Za-z0-9_]+)?\s*;\s*$')
_HEAD  = re.compile(r'^class\s+([A-Za-z0-9_]+)\s*(?::\s*[A-Za-z0-9_]+)?\s*(\{)?\s*$')
_DN    = re.compile(r'\bdisplayName\s*=\s*"((?:[^"\\]|\\.)*)"')

def parse_cfg_classes(text: str) -> dict:
    """Return {classname: displayName} for every class block in a CfgVehicles dump.
    Captures the displayName declared directly inside each class body; forward
    declarations (`class X;`) are recorded with an empty displayName. First
    displayName wins for a given name.

    Parser notes (real CfgVehicles.txt quirks):
    - All top-level vehicle classes sit one tab deep inside CfgVehicles{}.
    - Sub-object / array fields like `typicalCargo[] = {` open a brace block on
      the SAME line (not a class header), so they need a dummy stack frame to
      prevent the next `}` from popping the real class frame.  We push
      {'name': None} for any non-class, non-bare line that ends with '{'.
    """
    classes: dict[str, str] = {}
    stack: list[dict] = []          # open '{' frames: {'name': str|None}
    pending = None                  # class header awaiting its '{'
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Forward declaration: class X; or class X : Y;
        m = _FWD.match(line)
        if m:
            classes.setdefault(m.group(1), '')
            continue
        # Class header (with optional inline '{')
        m = _HEAD.match(line)
        if m:
            pending = m.group(1)
            classes.setdefault(pending, '')
            if m.group(2) == '{':
                stack.append({'name': pending}); pending = None
            continue
        # Bare open brace on its own line (class body opener)
        if line == '{':
            stack.append({'name': pending}); pending = None
            continue
        # Any other line ending with '{' (array/sub-object opener, e.g. `typicalCargo[] = {`)
        if line.endswith('{'):
            stack.append({'name': None}); pending = None
            continue
        # Close brace (handles `};` or `}` alone)
        if line.startswith('}'):
            if stack:
                stack.pop()
            pending = None
            continue
        # Capture displayName for the innermost named class frame
        if stack and stack[-1]['name']:
            dn = _DN.search(line)
            if dn and not classes.get(stack[-1]['name']):
                classes[stack[-1]['name']] = dn.group(1)
    return classes

_CATALOG_CLS = re.compile(r"\bcls\s*:\s*'([A-Za-z0-9_]+)'")
_PRESET_CLS  = re.compile(r"\[\s*'([A-Za-z0-9_]+)'\s*,\s*\[")

def extract_classnames(html: str) -> set:
    """Union of every classname referenced in index.html: CATALOG `cls:'X'`
    entries plus PRESET object arrays `['X',[...`. These are the classes whose
    thumbnails the editor can render, so these are the images we copy."""
    return set(_CATALOG_CLS.findall(html)) | set(_PRESET_CLS.findall(html))

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

def load_extra_classnames(text: str) -> dict:
    """Parse the allowlist text (one classname per line; `#` starts a comment;
    blank lines and comment-only lines are ignored). Returns {classname: ''}
    for each valid name. Inline `# ...` comments are stripped before processing."""
    result: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.split('#', 1)[0].strip()   # strip inline comments, then whitespace
        if line:
            result[line] = ''
    return result

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
    ap.add_argument('--ref', default='../arma2-co-config-reference',
                    help='path to the arma2-co-config-reference repo')
    ap.add_argument('--wddm', default='.', help='path to the WDDM repo root')
    args = ap.parse_args(argv)
    ref, wddm = Path(args.ref), Path(args.wddm)

    cfg = (ref / 'Config' / 'CfgVehicles.txt').read_text(encoding='utf-8', errors='replace')
    classes = parse_cfg_classes(cfg)

    extra_path = wddm / 'tools' / 'extra-valid-classnames.txt'
    if extra_path.exists():
        extra = load_extra_classnames(extra_path.read_text(encoding='utf-8'))
        for k, v in extra.items():
            classes.setdefault(k, v)   # config wins if name already present
        print(f"extra allowlist merged: {len(extra)}")

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
