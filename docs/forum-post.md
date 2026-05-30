# Suggestion: Buildable "Large Defenses" — manned AA / Arty / MG-AT / Checkpoints

**The idea (building on the HQ/Factory walls we already have):** let players actually
*fortify* the map. Engineers push **light defensive positions** out into friendly towns;
the **heavy versions** come online late-game (tech-gated) for proper base / strongpoint
defense. Every position spawns **already manned** with its own AI — gun crews plus a few
garrison riflemen — so they fight on their own instead of sitting empty.

## How it works now (walls recap)
Factories already spawn with pre-built H-barrier walls. Those walls aren't part of the
building model — they're a **composition**: a list of `[object, relative-offset, direction]`
placed around the structure. That same system can place *anything*, so we can use it to
build whole weapon positions, not just walls.

## What you'd be able to build
Four position types, each **BLUFOR / OPFOR specific** and laid out to **Cold War doctrine**:

| Position | What it's for |
|---|---|
| **AA Battery** | Anti-air — NATO Stinger / WarPac ZU-23 + Igla |
| **Artillery Battery** | Towed guns — M119 / D-30 (not mortars) |
| **Weapons Emplacement** | MG + AT strongpoint to stop armour |
| **Checkpoint** | Fortify a town entry — chicane, overwatch, guard towers |

Each comes in **Light** and **Heavy**:
- **Light** = engineer-built, forward, *in town*. Smaller footprint.
- **Heavy** = late-game / base tier, unlocked by the **Barracks upgrade**. Bigger, more guns, deeper obstacle belt.

**Doctrine flavour baked in:** NATO positions are **dispersed & concealed** — guns staggered
in depth, camo nets on the valuable stuff, AT missiles on the flanks for side-on shots.
Warsaw Pact positions are **massed & belted** — guns clustered in tight arcs, H-barrier
revetment boxes, and a deep wire + hedgehog obstacle belt out front.

## The balance bit (important)
The crew comes out of the **builder's own AI budget** — the same pool as your recruited squad —
so it's a real trade-off, not free stuff:

- **Light position = 4 AI**
- **Heavy position = 8 AI**

Guns get manned first, then the rest of that budget is filled with **garrison riflemen** holding
the position. Limits keep it sane: **max 2 positions per engineer, 1 per town, friendly towns
only, within 250 m of the town centre**, and Heavy needs the Barracks upgrade. Two heavies =
your entire AI budget, so you're choosing between a fortress and a field army.

## Why it's good for the game
- Gives **engineers** a real job beyond repair/salvage, and a reason to push forward.
- Gives the **commander / late-game** a way to actually *hold* ground, not just take it.
- Makes towns matter defensively — attackers have to break a manned position, not walk in.
- Cheap to tune: every layout is data, so we can adjust guns/spacing/cost without touching code.

## I built a tool for designing these
**WDDM — Warfare Dynamic Defense Manager:** a browser editor where you drag the pieces around
a top-down grid and it spits out the ready-to-paste mission code. Free, runs in the browser,
nothing to install:

▶ **https://rayswaynl.github.io/WDDM/**

The overview below shows all 16 layouts (4 types × Light/Heavy × BLUFOR/OPFOR). Keen to hear
what people think on the loadouts and the 4/8 AI cost before we lock it in.
