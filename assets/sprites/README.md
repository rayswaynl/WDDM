# WDDM sprites

Drop top-down PNG sprites here, named **exactly** `<classname>.png` (case-sensitive,
matching the catalog `cls` in `index.html`). Missing files fall back to the editor's
procedural glyph automatically — so you can add sprites incrementally.

Generate them from `docs/sprite-prompts.md` (ChatGPT image-gen). Contract:
- Transparent background PNG.
- Top-down (plan view); the weapon's **front/barrel points UP** in the image.
- Trim to the equipment's bounding box (no big margins).
- Square canvas unless the asset is long (walls/wire) — the editor letterboxes
  (fit-contain) so imperfect aspect never distorts.

Aliased classes (share one file): M2HD_mini_TripodCamo_US→M2StaticMG,
KORD_high_TK_EP1→DSHKM_TK_INS_EP1, Land_HBarrier5→Land_HBarrier_large,
Land_fortified_nest_small→Land_fortified_nest_small_EP1,
Land_fort_watchtower→Land_fort_watchtower_EP1, Land_CamoNetVar_EAST→Land_CamoNetVar_NATO,
Land_CncBlock→Land_CncBlock_Stripes, Land_BagFenceLong/Short→Land_fort_bagfence_long,
USLaunchersBox_EP1/TKVehicleBox_EP1/TKBasicAmmunitionBox_EP1→USBasicAmmunitionBox_EP1.
