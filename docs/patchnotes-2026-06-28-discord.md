# Discord-formatted patch notes — WASP tooling update (2026-06-28)
# (Discord: no tables, 2000-char limit per message. Post each block as its own
#  message, in order. Links kept in <angle brackets> so they don't double-embed.)

================ MESSAGE 1 ================
# 🛠️ WDDM Update — find pieces fast, build a lot more

Two big upgrades to **WDDM** (the defense-composition editor):

🔍 **New piece picker** — the old dropdown is gone. It's now a **searchable thumbnail grid**: type to filter (e.g. “trench”), click a tile to place it, or hit **Browse all** for the full set in a roomy popup. You can finally *see* every piece while you build.

🧱 **Bigger palette — ~92 → 204 pieces.** Added walls, trenches, castle ramparts, compound gates, faction MG nests, desert camo nets — plus every faction's base buildings (USMC/CDF/RU/INS/GUE/TK-GUE) for base-layout mode.

✅ **Classname validation** — type a custom class and it warns you live if it isn't real (no more silent typos), with autocomplete.

🔒 Existing layouts untouched — the exported mission code is identical to before.

▶ **<https://rayswaynl.github.io/WDDM/>**

================ MESSAGE 2 ================
# 🎒 New tool: Loadout Lab

A browser **loadout editor** for WASP — the infantry-kit sibling to WDDM. Build a unit's kit visually and export ready-to-paste SQF.

- Pick **faction · role · tier**, then fill slots — primary + mags, sidearm, launcher, throwables, gear — from a searchable thumbnail picker.
- **Export** `WFBE_%1_DefaultGear` (player) and `WFBE_%1_AI_Loadout_<tier>` (AI) — paste straight into `Root_*.sqf`.
- **Import** an existing loadout block to edit what's live.
- Live kit preview, classname validation, and share links.

Offline, single-file, free — same as WDDM.

▶ **<https://rayswaynl.github.io/loadout-lab/>**
