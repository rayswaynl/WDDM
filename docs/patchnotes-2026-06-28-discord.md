# Discord-formatted patch notes — WDDM items-repo update (2026-06-28)
# (Discord: no tables, 2000-char limit per message. Post each block as its own
#  message, in order. Link kept in <angle brackets> so it doesn't auto-embed twice.)

================ MESSAGE 1 ================
# 🛠️ WDDM Update — see your pieces, catch typos, build a lot more

Quality-of-life pass on **WDDM** (the Warfare Dynamic Defense Manager — the browser tool for designing buildable defense layouts that export straight to mission code):

🖼️ **Thumbnails everywhere** — every palette piece now shows its real in-game reference image, in the picker **and** the inspector. On the top-down canvas, pieces that don't have a dedicated top-down sprite now fall back to a dimmed reference image instead of a plain coloured box, so a layout reads at a glance.

✅ **Classname validation** — the editor now knows every Arma 2 base-game classname. Type a custom class and it **warns you live if it isn't real** — no more silent typos (the classic `Land_Razorwire` vs `Fort_RazorWire` trap) — with **autocomplete** from the full class list. A badge flags any unverified piece in the palette.

================ MESSAGE 2 ================
## 🧱 A much bigger palette — ~92 → 204 pieces

New defensive kit to build with:
- **Trenches** (big / small) · **Castle ramparts** · **Compound gates**
- **Faction MG nests** (M240 + PK variants) · **Desert camo nets** (NATO / East)
- Extra **walls & barriers** — stone wall, dam barrier, tall HESCO, road barriers — plus **hedgehogs** and **barricades**

And for **base-layout mode**, every faction's base buildings — **USMC, CDF, RU, INS, GUE, TK-GUE** (factories, radars, barracks, hospitals, construction sites, UAV terminals, vehicle service points).

🔒 **Your existing layouts are untouched** — this is all editor-side. The exported mission code is byte-for-byte identical to before, so nothing you've already built changes.

▶ Try it: **<https://rayswaynl.github.io/WDDM/>**
