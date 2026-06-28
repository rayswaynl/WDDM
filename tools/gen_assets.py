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
