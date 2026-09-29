# Unciv: Veilfall v0.2.9

**Version:** **v0.2.9 prerelease**  
**Deployment branch:** `main`  
**Development/source branch:** `veilfall-v0.2.9-corrective`  
**Predecessor:** **v0.2.8**  
**Status:** v0.2.9 corrective patch for native-comparable map-sprite placement, Rationalism city-map rendering, and Marine capture of adjacent embarked civilians; automated verification required before deployment; in-game acceptance pending  
**Base ruleset:** Civ V - Gods & Kings

Veilfall is an Unciv extension mod combining the supernatural Veilfall roster with the Ashton civilization and its knowledge, expeditionary-warfare, and institutional systems.

## Version lineage

- **v0.1** — initial prerelease build.
- **v0.1.1** — patch release correcting the packed-artwork location required by Unciv on Android.
- **v0.2** — substantive prerelease adding Ashton and the broader systems overhaul.
- **v0.2.1** — art-completion and gameplay-tuning patch: game-ready Ashton/Rationalism/Knowledge/building/unit/promotion assets plus 50% Slave Raider capture chance.

## Ashton

**Leader:** Paul Ashton  
**Capital:** St. Paul  
**Motto:** *Wisdom in Peace, Fury in Defense*  
**Civilization ability:** **Evidence Before Confidence**

The v0.2/v0.2.1 content set includes:

- the Ashton civilization and 40-city name list;
- a stockpiled, tradeable **Knowledge** resource;
- the **Athenaeum**, **Strategic Analysis Center**, and **The Great Archive**;
- the six-stage Marine lineage from **Continental Marines** through **Exo-Marine**;
- **Operational Intelligence** frontline/support formations;
- **Rationalism** and its first playable belief/building components;
- the **Slave** civilian and four-stage Slave Raider line;
- initial Slave labor and instability mechanics;
- the global infrastructure construction-time rebalance;
- the original Veilfall supernatural roster reassigned from the development America placeholder to Ashton.

## Marine lineage

| Unit | Tech | Strength | Movement | Cost |
| --- | --- | ---: | ---: | ---: |
| Continental Marines | Gunpowder | 27 | 2 | 140 |
| Marine Riflemen | Rifling | 38 | 2 | 208 |
| Expeditionary Marines | Replaceable Parts | 55 | 2 | 298 |
| Fleet Marine Force | Plastics | 77 | 2 | 361 |
| Marine Expeditionary Unit | Mobile Tactics | 100 | 3 | 425 |
| Exo-Marine | Future Tech | 125 | 4 | 553 |

Marine abilities accumulate through the upgrade chain. The JSON pass includes amphibious combat, rapid embark/disembark, embarked attacks, embarked defense, embarked reconnaissance, healing while acting, MEU combat tempo, and Exo-Marine mobility. Full conditional naval-combat classification while embarked is an engine-level follow-up.

## Knowledge

Knowledge is a civilization-wide stockpiled resource distinct from Science. Ashton generates it systematically from institutions; all civilizations can also gain Knowledge from technology completion, Natural Wonder discovery, era advancement, trade, and the Great Scientist **Document & Disseminate** action.

Standard Knowledge Cost (SKC):

| Era | Knowledge |
| --- | ---: |
| Ancient | 20 |
| Classical | 30 |
| Medieval | 45 |
| Renaissance | 65 |
| Industrial | 90 |
| Modern | 120 |
| Atomic | 160 |
| Information | 200 |
| Future | 250 |

AI trade valuation is currently centered around 10 Gold per Knowledge: AI buys at 8 and sells at 12.

## Slavery — v0.2 implementation

The JSON pass includes:

- Slave civilian unit;
- Slave Raider -> Mounted Slave Raider -> Slave Hunter -> Industrial Slaver;
- 50% prisoner-generation chance after eligible military victories;
- -25% city attack strength and inability to capture cities for the raider line;
- -1 Happiness per 3 Slaves;
- first-stage Worker augmentation while adjacent to a Slave;
- prototype emancipation by transforming a Slave into a Worker.

The full captive disposition, provenance, emancipation/repatriation, abolition, city-population enslavement, Forced Labor, and revolt systems require the state/UI implementation described in `BUILD_STATUS.md`.

## Infrastructure rebalance

Standard-speed construction times:

- Road 2
- Railroad 2
- Farm 5
- Mine 5
- Lumber Mill 5
- Trading Post 5
- Camp 5
- Pasture 6
- Plantation 4
- Quarry 6
- Oil Well 6
- Fort 5
- Remove Forest 3
- Remove Jungle 5
- Remove Marsh 4

Unlisted improvements retain their base Gods & Kings values.

## Build status

See **BUILD_STATUS.md** for the exact division between implemented JSON behavior, prototype behavior, and features that still require Unciv engine/state/UI work.

## Installation

Install or update Veilfall from the repository's default `main` branch. The v0.2.8
release source is `veilfall-v0.2.8-sprite-rebuild`; verified generated outputs are
staged on `veilfall-v0.2.8-art-integration` before `main` advances.

## v0.2.9 corrective patch

- Rebuilds all 33 Marine/slavery-line map sprites against actual upstream Unciv unit-sprite canvases and native reference silhouettes, with native-derived baseline and lateral placement rather than geometric centering.
- Uses nearest-neighbor sprite resampling and binary alpha to eliminate interpolation softness/halo artifacts.
- Replaces the packed `ReligionIcons/Rationalism` opaque full-color badge with a transparent tint-safe mask so the city-map religion marker cannot collapse into a solid disc.
- Adds a narrowly scoped Marine water-capture compatibility workaround: Marines may temporarily be treated as water-capable only while adjacent to a civilian. This bypasses Unciv's explicit prohibition on embarked land units capturing civilians on water while preserving normal embarkation away from civilians.
- The existing `May attack when embarked` behavior and all other Marine abilities remain in place.

## v0.2.6 isolated-character art rebuild

This corrective release rebuilds all eleven Marine/slavery-line figures from
original, layered game-asset illustrations, not crops of predecessor concept-art
cards. The style is intentionally stylized and silhouette-led. Each unit receives
a 256-pixel transparent portrait, white tint-safe UnitIcon, and compact transparent
map sprite under Minimal, FantasyHex, and HexaRealm. The three tilesets deliberately
share each unit's sprite. No scenery, card border, or text is part of a unit asset.

The Slave is unarmed and narrow, with close arms and no combat equipment. Slave
Raider has a lunging sword-and-net pose; Mounted Slave Raider has a horse/lance;
Slave Hunter has a wide-brim hat, split coat, and long firearm; Industrial Slaver
has a heavy coat, armored vest, cap, and shotgun. Marine silhouettes progress from
tricorn/musket through a kneeling kepi rifleman, campaign-hat expedition kit, steel
helmet/webbing, modern plate carrier/antenna, and broad powered armor with an
energy weapon. Exo-Marine retains navy, black, gold, and scarlet accents.

`Atlases.json` remains `["game","v021"]`. The 25 unrelated supplemental regions
are pixel-identical to the predecessor. All legacy game atlas pages and source
assets remain byte-identical. Gameplay JSON is unchanged except ModOptions
version/date metadata. The capture rule remains exactly:

```text
Free [Slave] appears <upon defeating a [Military] unit> <with [50]% chance>
```

The Military filter is unchanged and no Barbarian exclusion has been added.
This is preservation of the implementation, not a new engine-level probability test.

## Rebuild and acceptance evidence

The workflow `.github/workflows/v021-art-build.yml` uses Pillow 11.3.0 and readable
sources in `tools/v026/`. The legacy `tools/v021/build_assets.py` entrypoint now
delegates to the new builder, not the retired crop pipeline. Old `tools/v022`
inputs remain only as historical data and are not read by the new unit builder.

Run `python3 tools/v026/build_assets.py` to rebuild, then
`python3 tools/v026/build_assets.py --check` to verify files actually on disk.
`ART_VERIFICATION.json` records the automated results and hashes, transparency,
size bounds, normalized silhouette comparisons, and baseline preservation.
`tools/v026/test_results.json` records adversarial tests of the verifier itself.
The 55 source PNGs and packed-asset QA sheets are retained under `tools/v026/`.
An automated pass does not establish manual in-game visual acceptance.

After updating, inspect all eleven portraits and tinted icons in Civilopedia,
check small-scale sprites in each tileset, and spot-check the original supernatural
units. Runtime observations are the remaining evidence; build logs, hashes, and
rule text already exist in the automated record and need not be transcribed.

## Historical art lineage

v0.2.1 introduced the supplemental atlas. v0.2.2/v0.2.3 revised artwork and
integration. v0.2.4 reduced map scale, but its generic portraits were not accepted.
The predecessor v0.2.5 restored source-art crops; runtime screenshots still showed
background and scenery/card remnants. v0.2.6 supersedes that crop pipeline while
retaining small map footprints. These are historical notes, not current deployment
claims. Actual deployment is established by Git refs and successful workflow runs.

## v0.2.7 native-scale map-unit framing

Runtime screenshots from v0.2.6 showed the rebuilt figures were too small inside their map-sprite frames compared with adjacent vanilla combat units. v0.2.7 keeps the accepted character designs and transparent portraits/icons, but rescales and bottom-anchors map sprites to native Unciv tileset frames. FantasyHex uses 32x28 frames; HexaRealm uses 64x56 infantry frames and a taller 64x65 mounted frame. Minimal uses the HexaRealm-sized framing for consistent readability.

The Continental Marines calibration target is the adjacent vanilla Spearman shown in the acceptance screenshot: comparable apparent height, grounded foot position, and native in-frame placement. Infantry is normalized against infantry; Mounted Slave Raider is normalized against mounted-unit framing. No gameplay rules change.


## v0.2.8 dedicated map-sprite rebuild

Runtime acceptance of v0.2.7 showed that native frame dimensions alone did not
produce acceptable custom map units: figures still read too softly, too centrally,
and too weakly at normal map scale. v0.2.8 therefore replaces the actual map-sprite
art for all eleven Marine/slavery-line units with purpose-built, transparent,
silhouette-led game sprites. The improved v0.2.7 portraits and UnitIcons are
preserved byte-for-byte.

The rebuild covers Slave, Slave Raider, Mounted Slave Raider, Slave Hunter,
Industrial Slaver, Continental Marines, Marine Riflemen, Expeditionary Marines,
Fleet Marine Force, Marine Expeditionary Unit, and Exo-Marine in Minimal,
FantasyHex, and HexaRealm: 33 atlas regions total. Figures are larger, lower in
their frames, and rendered with simplified high-contrast forms intended to survive
small-scale display. Slave is explicitly civilian/unarmed; Slave Raider is an
armed raider; Mounted Slave Raider is unmistakably mounted; later slavery-line
units use distinct later-era equipment. The Marine line retains a clear era
progression through the futuristic Exo-Marine.

No gameplay rule changes are part of this patch. The exact 50% Slave Raider
capture rule remains unchanged. Automated evidence is recorded in
`ART_VERIFICATION.json`; packed-asset preview output is retained under
`tools/v028/previews/`. Final visual acceptance remains an in-game check.
