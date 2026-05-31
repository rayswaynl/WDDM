# WDDM sprite prompt pack (ChatGPT / DALL·E image-gen)

Generate top-down equipment sprites for the WDDM editor. Each becomes
`assets/sprites/<classname>.png`. The editor falls back to procedural glyphs for
any missing file, so you can generate these in any order and drop them in as you go.

## How to use
1. Paste the **STYLE PREAMBLE** once at the top of a ChatGPT image request.
2. Append **one ASSET line** under it. Generate. Download as PNG.
3. Save as the exact **filename** shown (case-sensitive).
4. Drop into `WDDM/assets/sprites/`. Refresh the editor — it appears automatically.

> Start with the **3 PILOT** sprites, eyeball them in the editor at real scale,
> and tell me if the style holds before generating the rest. If they come out
> upside-down or too zoomed, we tweak the preamble once and regenerate — cheaper
> to fix on 3 than on 24.

---

## STYLE PREAMBLE (paste verbatim, every time)

> Top-down (plan view), straight 90° bird's-eye view of a single piece of military
> equipment, centred on a **fully transparent background**. Semi-realistic but
> slightly stylised "game counter" look — clean readable shapes, subtle shading,
> NOT photoreal, NOT cartoon, no outline border. Soft contact shadow directly
> beneath the object only. Even neutral lighting from the top-left. Muted military
> palette. **The equipment's firing direction / barrel points toward the TOP of
> the image.** No text, no labels, no grid, no scale bar, no base ring or platform
> unless it is physically part of the object. The object is trimmed to fill ~85% of
> the frame with small even padding. Square image with alpha (unless told otherwise).

**Faction tint:** US/WEST = olive drab + tan, dark gunmetal barrels. Soviet/EAST =
darker Soviet green, amber/brown Bakelite where noted. Concrete = neutral grey.
Sandbags/HESCO = tan-khaki.

---

## ⭐ 3 PILOT SPRITES (do these first)

**1 — `M2StaticMG.png`** (square)
> [STYLE PREAMBLE] + A US **M2 Browning .50 calibre heavy machine gun mounted on an M3 tripod**, seen from directly above. Three tripod legs form a dark triangle with the apex pointing toward the bottom of the frame; a long thin barrel projects forward to the top, past the front leg. Compact dark-grey receiver box at the centre over the tripod hub. Olive drab and gunmetal. Front/barrel points UP.

**2 — `D30_TK_EP1.png`** (square)
> [STYLE PREAMBLE] + A Soviet **D-30 122mm towed howitzer in firing position**, seen from directly above. Its **three trail legs are splayed at 120° apart forming a distinctive Y / three-pointed star** around a central round firing jack. A long gun barrel extends from the centre over one of the legs toward the top of the frame. Soviet green, gunmetal barrel. The three-leg star shape must be clearly readable. Barrel points UP.

**3 — `Land_fort_bagfence_long.png`** (wide, ~3:1 — tell ChatGPT "wide 3:1 image, transparent")
> [STYLE PREAMBLE, but **wide 3:1 image**] + A **straight section of stacked sandbag wall / parapet**, seen from directly above. A thick horizontal tan-khaki strip running left-to-right, made of individual sandbags in a staggered brickwork pattern, slightly irregular. Subtle soft shadow along the lower edge. No weapons, no people. Earthy tan colour.

---

## FULL SET (after the pilot is approved)

### WEST / US weapons (square unless noted)
- **`MK19_TriPod_US_EP1.png`** — US **Mk19 40mm automatic grenade launcher on an M3 tripod**, top-down. Same triangular tripod as the M2 but a squatter, boxier receiver and a short stubby barrel; a rectangular ammo can sits to one side. Olive drab. Barrel points UP.
- **`TOW_TriPod_US_EP1.png`** — US **BGM-71 TOW anti-tank missile launcher on an M220 tripod**, top-down. A folding tripod carrying a thick stubby square launch tube pointing up, with a prominent rectangular optical sight block beside it. Chunkier and boxier than a machine gun. Olive drab, dark optics. Tube points UP.
- **`Stinger_Pod_US_EP1.png`** — A US **Stinger / Avenger-style static anti-air missile pod**, top-down. A small turntable base carrying two slim rectangular missile-launcher boxes side by side, each showing 2–4 round tube mouths facing up/forward. Olive drab. Tube mouths point UP.
- **`M119_US_EP1.png`** — US **M119 105mm towed howitzer in firing position**, top-down. A split-trail carriage: **two trail legs splay rearward in a V** toward the bottom; two road wheels at the hips mid-body; a thin gun barrel with a small muzzle brake extends forward to the top. Olive drab / tan. Barrel points UP. *(tall, ~3:4 portrait OK)*
- **`M252_US_EP1.png`** — US **M252 81mm mortar**, top-down. A small round baseplate with a thin tube angled up from centre and a two-legged bipod V straddling it. Tiny footprint, dark metal/olive. Tube points UP.

### EAST / Soviet weapons
- **`DSHKM_TK_INS_EP1.png`** — Soviet **DShKM 12.7mm heavy machine gun on a wheeled mount**, top-down. A central gun body with a finned barrel and large oval muzzle brake pointing up; **two small road wheels on either side at the base**; a folded tail-boom leg trailing to the bottom; optional small rectangular gun-shield forward. Soviet green. Barrel points UP.
- **`AGS_TK_EP1.png`** — Soviet **AGS-17 30mm automatic grenade launcher on a small tripod**, top-down. A squat round drum-fed body on a compact three-leg tripod with a short barrel up. Soviet green. Barrel points UP.
- **`Metis_TK_EP1.png`** — Soviet **9K115 Metis anti-tank missile launcher on a small tripod**, top-down. A very compact tripod carrying one thin launch tube pointing up and a small control/sight box beside it. Noticeably smaller and lighter than the TOW. Olive green. Tube points UP.
- **`SPG9_TK_INS_EP1.png`** — Soviet **SPG-9 73mm recoilless gun on a low tripod**, top-down. A long, very slender barrel pointing up, with a distinctive flared/bulbous venturi nozzle at the rear (bottom), on a small three-leg tripod. Almost all barrel. Dark green with amber-brown heat shielding at the breech. *(tall, ~3:4 portrait OK)*
- **`Igla_AA_pod_TK_EP1.png`** — Soviet **Igla (Dzhigit) static anti-air missile pod**, top-down. A small pedestal/tripod carrying two parallel cylindrical launch tubes pointing up/forward. Lighter and simpler than the ZU-23. Olive green. Tubes point UP.
- **`ZU23_TK_EP1.png`** — Soviet **ZU-23-2 twin 23mm anti-aircraft autocannon, towed mount in firing position**, top-down. **Two long parallel barrels point up** from a central boxy gunner's seat; two rectangular ammunition boxes stick out sideways (one each side); two road wheels at the sides. Wide, symmetrical. Soviet green. Barrels point UP. *(wide, ~3:2 OK)*

### Fortifications / props
- **`Land_HBarrier_large.png`** *(wide 4:1)* — A long **HESCO bastion barrier wall**, top-down: a row of connected open-topped square cells filled with brown earth, tan-grey geotextile walls, wire-mesh grid visible at the rim. Straight wall running left-to-right.
- **`Land_HBarrier3.png`** *(wide 2.5:1)* — Same HESCO bastion but a **short 3-cell section**.
- **`Land_HBarrier_corner.png`** *(square)* — A **HESCO bastion L-corner** (two short runs meeting at 90°), top-down.
- **`Land_fort_bagfence_corner.png`** *(square)* — A **sandbag wall L-corner**, top-down; tan staggered bags forming a right angle.
- **`Land_fort_bagfence_round.png`** *(square)* — A **circular sandbag parapet / gun-pit ring**, top-down; a ring of tan sandbags enclosing a small open centre.
- **`Land_fortified_nest_small_EP1.png`** *(square)* — A **small sandbagged weapons nest**, top-down; a square sandbag ring with a gap/entrance on one side, open centre. Tan.
- **`Land_fort_watchtower_EP1.png`** *(square)* — A **wooden guard watchtower**, top-down; a small square observation platform with four corner posts and a simple roof. Timber brown.
- **`Land_CamoNetVar_NATO.png`** *(square, semi-transparent)* — A **camouflage net**, top-down; an irregular polygon of disruptive-pattern netting, partly see-through, soft drooping edges. Olive/tan disruptive pattern.
- **`Land_Razorwire.png`** *(wide 5:1)* — A **concertina / razor wire coil**, top-down; a straight line of overlapping silver-grey wire loops running left-to-right.
- **`Hedgehog.png`** *(square)* — A **Czech hedgehog anti-tank obstacle**, top-down; a six-pointed steel asterisk (crossed I-beams) with a small centre hub. Rusty dark steel.
- **`Land_CncBlock_Stripes.png`** *(~1.5:1)* — A **concrete Jersey barrier with hazard stripes**, top-down; an elongated grey concrete block, narrow on top widening at the base, yellow-black diagonal stripe markings.
- **`RoadCone_L_EP1.png`** *(square)* — A **traffic cone**, top-down; concentric rings — bright orange outer ring, dark square base, small top circle.
- **`USBasicAmmunitionBox_EP1.png`** *(~1.4:1)* — A **military ammunition crate**, top-down; an olive-drab rectangular box with latches and a centre seam, faint stencil marks (no readable text).

---

## Notes
- **Orientation is critical:** barrel/front = TOP of the image. If a sprite looks
  rotated 180° in the editor, regenerate emphasising "barrel points toward the top".
- **Trim tight:** big transparent margins make the equipment look too small on the
  grid (the editor scales the *image* to the object's metre span). Crop close.
- **Aspect:** square is the default; the editor letterboxes (fit-contain) so a
  slightly-off aspect won't distort — but for genuinely long items (walls, wire,
  ZU-23) ask ChatGPT for the wide/tall ratio noted so detail isn't wasted.
- **Consistency tip:** generate a faction's weapons in one session so ChatGPT keeps
  the palette and rendering style coherent across them.
