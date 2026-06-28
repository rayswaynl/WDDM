# Discord-formatted patch notes (2026-06-28)
# (Discord: no tables, 2000-char limit per message. Post each block as its own message.)

# ===== ALREADY POSTED (first set) =====

================ MESSAGE 1 (posted) ================
# 🛠️ WDDM Update — find pieces fast, build a lot more

Two big upgrades to **WDDM** (the defense-composition editor):

🔍 **New piece picker** — the old dropdown is gone. It's now a **searchable thumbnail grid**: type to filter (e.g. “trench”), click a tile to place it, or hit **Browse all** for the full set in a roomy popup. You can finally *see* every piece while you build.

🧱 **Bigger palette — ~92 → 204 pieces.** Added walls, trenches, castle ramparts, compound gates, faction MG nests, desert camo nets — plus every faction's base buildings (USMC/CDF/RU/INS/GUE/TK-GUE) for base-layout mode.

✅ **Classname validation** — type a custom class and it warns you live if it isn't real (no more silent typos), with autocomplete.

🔒 Existing layouts untouched — the exported mission code is identical to before.

▶ **<https://rayswaynl.github.io/WDDM/>**

================ MESSAGE 2 (posted) ================
# 🎒 New tool: Loadout Lab

A browser **loadout editor** for WASP — the infantry-kit sibling to WDDM. Build a unit's kit visually and export ready-to-paste SQF.

- Pick **faction · role · tier**, then fill slots — primary + mags, sidearm, launcher, throwables, gear — from a searchable thumbnail picker.
- **Export** `WFBE_%1_DefaultGear` (player), `WFBE_%1_AI_Loadout_<tier>` (AI), and buy-menu presets — paste straight into `Root_*.sqf` / `Loadout_*.sqf`.
- **Import** an existing loadout block to edit what's live.
- Live kit preview, classname validation, and share links.

Offline, single-file, free — same as WDDM.

▶ **<https://rayswaynl.github.io/loadout-lab/>**

# ===== TO POST (follow-up — everything since) =====

================ MESSAGE 3 ================
# 🎒 Loadout Lab Update — load real kits, build them faster

A big update to **Loadout Lab** (the WASP loadout editor):

📥 **Load from mission** — pick a faction + role (or AI tier) and load the mission's ACTUAL deployed loadout, then tweak it. No more starting from scratch.

🔫 **Smarter ammo** — selecting a weapon now shows only its **compatible magazines** and **auto-fills** a standard ammo load. One click, no wrong mags.

⚠️ **Kit validation** — warns you live about a weapon with no magazine, a mag that doesn't fit, no primary, or a backpack over capacity.

💾 **Auto-save** — your loadout is saved in the browser and restored on reload, with a **Recent**-picks row in the picker.

🛒 **Gear catalog** — a new panel to add weapons/mags to a faction's shop (price + upgrade tier) → exports the `Gear_*.sqf` registration block.

▶ **<https://rayswaynl.github.io/loadout-lab/>**
