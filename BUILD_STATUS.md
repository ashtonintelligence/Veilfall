# Veilfall v0.2.11 — Build Status

**Version:** **v0.2.11 prerelease**\
**Deployment branch:** `main`\
**Source branch:** `veilfall-v0.2.11-marine-polish`\
**Predecessor:** **v0.2.10**\
**Patch build date:** 2026-09-30

**Current status:** Candidate for exactly two objectives: Marine map-sprite
proportions and one universal Marine movement point. Automated gates are pending;
v0.2.11 manual in-game acceptance is pending. No Special Forces, slavery, civilian
capture or unrelated systems are added.

## Accepted v0.2.10 baseline

Paul confirmed that the previously failing game resumes, the Rationalism city
marker is correct, and sprite sharpness and lateral placement are accepted.
These accepted properties must remain intact. The unsafe adjacent-civilian
CanMoveOnWater rule remains absent. Its original runtime regression test source
is unchanged and continues to run against Unciv 4.22.4 with `--rerun`.

## v0.2.11 implementation

- Add `[+1] Movement` once to Marine Naval Integration, after the existing embarked
  attack unique. Every Marine already receives this promotion. No Units.json
  property or other promotion is changed.
- Expected neutral maximums: Continental / Riflemen / Expeditionary / Fleet
  Marines 3 land, MEU 4 land, Exo-Marine 5 land; all six 3 embarked. Existing
  technology and policy movement bonuses remain additive. Serialized remaining
  movement is preserved during load, not replenished in the middle of a turn.
- Correct only Continental and Expeditionary map sprites in Minimal, HexaRealm
  and FantasyHex. A review against native Infantry found the second unit also
  materially tall/narrow (22×42 versus 25×36). Other Marines did not show that same
  paired defect and remain unchanged. All slavery sprites remain unchanged.
- Keep original canonical character sources, portraits, UnitIcons and atlas
  frames. Render the two corrected silhouettes using independent nearest-neighbor
  pixel dimensions, preserving the v0.2.10 lateral centroid within 0.5 pixel and
  the exact bottom anchor. No softened filtering or character redesign.
- Six atlas regions change; the other 74, including Rationalism, are byte-identical
  as decoded RGBA. Atlas layout is byte-identical; its shared PNG necessarily
  changes because it contains the six corrected regions.

See `tools/v0211/VERIFICATION.md` and its comparison image for release evidence.

## v0.2.10 source diagnosis (historical; fix retained)

Unciv 4.22.4, upstream commit `3318515bfca2609a9edb127b59cfadbab6d58d38`:
`UncivFiles.loadGameFromFile` calls `GameInfo.setTransients`, then
`TileMap.setTransients` / `Tile.setUnitTransients`. Each unit receives its owner
and then calls `MapUnit.setTransients` / `MapUnitCache.updateUniques` sequentially.
The cache queries `CanMoveOnWater`. The removed conditional scans neighboring
units and reads `it.civ` before every neighbor has been assigned its owner.
This explains the reported `lateinit property civ has not been initialized`.
It does not establish corruption of the serialized save.

Removed exactly:
`May travel on Water tiles without embarking <when adjacent to a [Civilian] unit>`.
No exception suppression, engine modification, renamed units, or save mutation.
The same condition also requires a friendly neighbor (`it.civ == relevantCiv`),
so the old workaround did not reliably implement adjacent enemy-civilian capture.

Preserved: all 33 native-derived map sprites, hard alpha, nearest-neighbor atlas,
lateral positioning, bottom anchoring, open-center tint-safe Rationalism marker,
Marine stats and upgrades, all other abilities, exact 50% Slave Raider rule,
Operational Intelligence, Knowledge, beliefs, infrastructure and supernatural units.

## Marine civilian capture — unresolved

`UnitMovement.cannotPassThroughReason` rejects a land unit entering an enemy
civilian's water tile unless `cache.canMoveOnWater` is true. It does not consult
`AttackOnSea` (`May attack when embarked`) at that gate. Converting Marines to
naval units or granting unconditional water movement violates the locked scope.
Terrain-only water-travel conditions would avoid this specific neighbor read but
would change embarkation/classification more broadly; they are not an equivalent
safe civilian-capture exception. No supported unique was found for that exception.
The targeted solution requires an engine entry/capture rule (and matching target
selection behavior) or a separately designed implementation mechanism. Deferred.

## Embarked movement — separately tracked

`MapUnit.getMaxMovement()` starts embarked land units at **2**, then adds matching
`Movement` uniques and finally considers same-tile `TransferMovement` effects.
The safe supported numeric form is `[amount] Movement <when [Embarked]>`, with a
concrete amount chosen by design; global embarkation/technology movement bonuses
can also contribute. It is an additive adjustment, not inheritance of naval unit
stats or recognition by naval filters. No amount is selected by this hotfix.
`Transfer Movement to [mapUnitFilter]` needs a suitable same-tile supporting unit;
it is not automatic naval classification. The locked full naval movement/combat
classification requires engine-level handling. v0.2.11 implements the separately approved universal +1 Movement compensation;
the full naval-classification limitation remains.

## Slavery — separately tracked

Slave currently supplies passive adjacent Worker support and a Worker-transform
prototype. Return / Liberate / Enslave / Execute, provenance, repatriation, Forced
Labor, diminishing support, abolition, revolt and diplomacy remain unfinished.
None is implemented or expanded by v0.2.10.

## Implemented in JSON

### Ashton civilization
- Ashton nation, Paul Ashton leader, St. Paul capital.
- Locked navy/gold civilization colors.
- Full 40-city list.
- Original Veilfall supernatural units reassigned from the America development placeholder to Ashton.

### Knowledge resource
- Stockpiled civilization resource.
- Lump-sum trading supported by native Unciv stockpile trading.
- AI buy value: 8 Gold per Knowledge.
- AI sell value: 12 Gold per Knowledge.
- Ashton recurring generation:
  - Palace +1.
  - Athenaeum +2 total.
  - University +2.
  - Public School +3.
  - Research Lab +5.
  - Strategic Analysis Center +1.
  - Great Archive +5.
- Universal event generation:
  - technology completion = 0.10 SKC, era-scaled;
  - Natural Wonder discovery = 0.25 SKC, current-era-scaled;
  - era entry = 0.50 SKC.
- Great Scientist **Document & Disseminate** action = 1.00 current-era SKC, consuming the Great Scientist.

### Ashton buildings
- Athenaeum:
  - replaces Library;
  - normal Library Science;
  - +1 Culture;
  - +2 Knowledge;
  - 1 maintenance.
- Strategic Analysis Center:
  - replaces Armory;
  - Barracks required;
  - Steel;
  - 20 starting XP for all newly trained military units;
  - +1 Knowledge;
  - destroyed on capture.
- The Great Archive:
  - National Wonder;
  - Scientific Theory;
  - University required in every non-puppet city;
  - base cost 400;
  - native +15 cost per owned city;
  - +5 Knowledge;
  - +2 Culture;
  - +2 Great Scientist points;
  - destroyed on capture.
- Forum of Inquiry:
  - Faith-purchase follower building;
  - +2 Culture;
  - +1 Happiness;
  - +1 Knowledge.

### Marines
- Complete six-unit upgrade chain and locked Strength/Movement/Production values.
- Amphibious combat.
- 1-MP embark and disembark.
- May attack while embarked.
- +50% embarked defense from Continental Marines onward.
- +1 embarked sight from Marine Riflemen onward.
- Additional +50% embarked defense and heal-while-acting from Expeditionary Marines onward.
- Two attacks and move-after-attack from MEU onward.
- Exo-Marine ignores terrain movement costs and Zone of Control.

### Operational Intelligence
Newly trained Ashton units receive hidden formation promotions:
- Sword, Gunpowder, Mounted, Armored -> Operational Frontline.
- Archery, Ranged Gunpowder, Siege -> Operational Support.

Effects:
- Frontline adjacent to Support: +10% attack and +15% defense.
- Support adjacent to Frontline: +15% defense.
- No stacking is intended; current implementation uses presence-based adjacency conditions.

### Slavery — JSON portion
- Slave civilian unit.
- Slave Raider line and upgrade path.
- 50% chance to create a Slave after defeating an eligible military unit.
- Slave Raiders are -25% vs cities and cannot capture cities.
- -1 Happiness per 3 owned Slaves.
- Adjacent Slave reduces improvement construction time by 33%, approximating the locked first-stage 150% Worker rate.
- Slave -> Worker transformation is present as a prototype emancipation action.

### Rationalism — native portion
- Rationalism religion/philosophy entry.
- Education as a Public Good:
  - +1 Science at 4 followers;
  - another +1 at 8;
  - another +1 at 12;
  - maximum +3 per city.
- Human Dignity:
  - +1 Happiness in cities following Rationalism.
- Forums of Inquiry:
  - enables Faith purchase of Forum of Inquiry.
- Open Inquiry:
  - +25% natural religion spread.

### Infrastructure
Locked construction-time rebalance is implemented for Road, Railroad, Farm, Mine, Lumber Mill, Trading Post, Camp, Pasture, Plantation, Quarry, Oil Well, Fort, Remove Forest, Remove Jungle, and Remove Marsh.

## Native approximation / prototype differences

### Scientist specialist Knowledge
Locked design: each Scientist specialist generates +1 Knowledge per turn.

The initial JSON implementation attempted to express this with a specialist-specific countable. Unciv's in-game validator rejects that expression on the deployed game build, so the invalid unique has been removed from v0.2. Scientist Knowledge generation remains a required engine/unique enhancement rather than shipping a broken ruleset.


### Great Archive city scaling
Locked design: +15 Production per **non-puppet** city.

Native Unciv unique currently available: +15 Production per **owned** city.

The JSON build uses the native owned-city rule. Exact non-puppet-only scaling requires a small engine/unique enhancement unless a cleaner native expression is identified during validation.

### Slave labor
Locked target:
- Worker + 1 Slave = 150%;
- +2 Slaves = 180%;
- +3 Slaves = 200% cap.

Current JSON:
- presence of at least one adjacent Slave gives the first-stage -33% construction-time modifier.
- counting multiple adjacent Slaves with the locked diminishing-return curve remains an engine/prototype task.

### Emancipation
Current Slave -> Worker transformation is intentionally only a prototype. It does not yet enforce provenance-based repatriation.

### Operational Intelligence on existing units
The nation grants formation promotions to newly trained units. Units already present in an older save are not automatically migrated in this JSON pass.

### Document & Disseminate presentation
The effect is implemented as an era-scaled stockpile-gain unit action. A custom user-facing action label remains optional UI polish.

## Engine/state/UI work still required

### Marine Naval Integration
The JSON pass implements embarked combat and mobility primitives, but not the complete locked classification:

> While embarked, a Marine counts as a naval combat unit for combat and movement purposes.

Still required:
- naval combat-unit movement filters apply to embarked Marines;
- naval combat Strength bonuses apply;
- Great Admiral/naval support effects apply;
- anti-naval bonuses and penalties recognize them as naval combatants.

### Research Initiative
Locked:
- costs 1 SKC based on target tech era;
- contributes 15% of total target technology Science cost;
- once per technology per civilization;
- no overflow.

Requires research-screen/action state and per-tech usage tracking.

### Technical Assistance
Locked:
- Ashton only;
- costs 0.75 current-era SKC;
- +20 City-State Influence;
- once per City-State every 10 Standard-speed turns;
- game-speed scaled;
- unavailable while at war with that City-State.

Requires City-State interaction UI/state.

### Never Start It. Finish It.
The grievance doctrine requires persistent per-opponent state:
- Minor 30 turns;
- Major 50 turns;
- Severe 100 turns;
- Major: +10% target-specific Strength and +10% military Production;
- Severe: +15% target-specific Strength and +20% military Production;
- refresh/upgrade rules;
- explicit resolution;
- ally/City-State response choices;
- Defensive Pact choice instead of automatic war entry.

### Slavery state system
Still required:
- Return / Liberate / Enslave / Execute captive disposition;
- first-generation provenance fields and 60-turn decay;
- city-conquest Enslave Population action;
- provenance-aware emancipation/repatriation;
- permanent Abolish Slavery action;
- exact Forced Labor action;
- full diminishing-return Worker support;
- revolt logic and rebel spawning;
- Rationalist slavery/execution diplomacy;
- City-State return/liberation Influence rewards.

### Rationalism state/diplomacy
Still required:
- The Examined World founder effect:
  - 0.20 SKC first time Rationalism becomes majority in a new city;
  - additional 0.30 SKC for first Rationalist-majority city in each foreign major civilization;
  - one award per qualifying city/civilization, no reconversion farming.
- Open Inquiry +50% trade-route Rationalist pressure.
- anti-slavery / anti-execution / emancipation diplomatic modifiers.

**The Examined World is deliberately marked Unavailable in the JSON pass until its effect is real.**

### Knowledge intelligence operations
Deferred from the initial playable build:
- Steal Knowledge: attacker +0.75 SKC, victim unchanged.
- Destroy Records: victim -0.50 SKC, capped at 20% stockpile.
- Great Archive capture: captor +1.0 SKC once.

### AI refinements
Later:
- deliberate Operational Intelligence formation behavior;
- Knowledge reserve/demand logic;
- slavery/abolition preferences;
- Rationalist ethical behavior.

## Art integration — v0.2.1
v0.2.1 supplies packed game-ready assets for:
- Ashton Nation icon and portrait;
- Rationalism icon and portrait;
- Knowledge resource icon and portrait;
- Athenaeum, Strategic Analysis Center, The Great Archive, and Forum of Inquiry portraits;
- all six Marine unit portraits, unit icons, and Minimal/FantasyHex/HexaRealm map sprites;
- Slave plus all four Slave Raider-line unit portraits, unit icons, and Minimal/FantasyHex/HexaRealm map sprites;
- Operational Frontline, Operational Support, Marine Naval Integration, Marine Embarked Recon, Marine Expeditionary Endurance, MEU Combat Tempo, Exo-Marine Mobility, and Slave Raider Doctrine promotion icons/portraits.

These assets are packed into the supplemental `v021` atlas, loaded alongside the original `game` atlas.

## v0.2.6 automated release gates

The build recomputes evidence from the packed PNG/atlas rather than only in-memory
source assets, and checks ART_VERIFICATION.json against those bytes. Gates cover
80 exact nonoverlapping keys, 55 rebuilt regions, 25 pixel-identical unrelated
regions, all repository JSON, version 0.2.6, transparent corners/borders,
nonrectangular figure masks, white tint-safe icons, compact sprite bounds, and
11 distinct normalized silhouettes for each asset class. Slave versus Slave
Raider is explicitly compared without relying on color.

The preservation manifest is generated from actual objects at predecessor commit
`cd377c5a2ef04c9447656673e06c6a9fc4d47a97`. Protected gameplay files, the entire legacy
game atlas including game2.png through game6.png, raw supernatural art, and old
source data must remain byte-identical. Only ModOptions version/date metadata
changes. All four capture-line units retain Slave Raider Doctrine and its exact
50% Military-kill rule, with no new Barbarian exclusion.

Original layered figures in tools/v026/artwork.py do not read predecessor unit
crops. Portraits are intentionally stylized and isolated. All 55 source PNGs must
match their packed regions pixel-for-pixel. The dependency is pinned to Pillow
11.3.0 in Actions. The old builder entrypoint delegates to this new implementation.

The verifier is tested against deliberate corruptions; results are recorded in
tools/v026/test_results.json. A full second build must reproduce every generated
source PNG, the supplemental PNG/atlas, and the verification report byte-for-byte.
The build job pushes artifacts to `veilfall-v0.2.6-art-integration`. Main advances
separately after a successful run and artifact inspection. The same workflow
performs a read-only check after main advances.

## In-game acceptance still required

Automated results are not an Unciv runtime test or user art approval. Unciv has not
been launched with these assets in the build environment. After updating, inspect
Civilopedia isolation, Slave versus Raider under nation tint, all six Marine
stages, map scale and mounting in all three tilesets, and the seven legacy
supernatural units. Locate mod errors remains an engine-level check. Screenshots
are only needed for runtime defects not captured in existing automated evidence;
no manual transcription of logs or hashes is required.

## Historical corrective-release context

v0.2.1 added the supplemental atlas; v0.2.3 repaired integration/icons; v0.2.4
established smaller footprints but its generic portraits were not accepted. The
predecessor v0.2.5 restored source-derived portraits that still exposed backgrounds.
v0.2.6 replaces that approach. Broader gameplay implementation and deferred-work
statements above are unchanged by this art-only release.

## v0.2.7 unit-scale/framing corrective pass

The v0.2.6 isolated figures remain the source art. This pass changes only map-sprite scale and transparent-frame placement so custom combat units read like neighboring vanilla units at runtime. FantasyHex assets use the native 32x28 unit frame. HexaRealm infantry uses 64x56 and mounted art uses 64x65. Figures are bottom-anchored with a one-pixel safety margin instead of centered in a 128x128 transparent canvas.


## v0.2.8 dedicated map-sprite rebuild

This patch responds to v0.2.7 runtime evidence that custom map units remained too
soft, centered, and visually small despite corrected frame dimensions. It rebuilds
the actual map sprites for all eleven Marine/slavery-line units rather than
continuing incremental scaling of the v0.2.6 figure renders.

Rebuilt units:
- Slave
- Slave Raider
- Mounted Slave Raider
- Slave Hunter
- Industrial Slaver
- Continental Marines
- Marine Riflemen
- Expeditionary Marines
- Fleet Marine Force
- Marine Expeditionary Unit
- Exo-Marine

Each receives new Minimal, FantasyHex, and HexaRealm map art. The patch preserves
all v0.2.7 portraits and UnitIcons, all unrelated supplemental-atlas regions, and
the original `game` atlas. Verification explicitly checks transparent corners,
native frame sizes, lower/bottom anchoring, distinct sprite hashes and normalized
silhouettes, Slave versus Slave Raider differentiation, mounted differentiation,
all repository JSON, the `["game","v021"]` atlas contract, and the exact 50%
Slave Raider Military-kill capture rule.

The build source is `tools/v028/`. Purpose-built canonical sprite artwork is
retained under `tools/v028/sprite_sources/`; generated tileset images and preview
evidence are produced by the build workflow. Automated pass does not substitute
for final in-game visual acceptance.
