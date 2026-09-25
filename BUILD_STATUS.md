# Veilfall v0.2.1 — Build Status

**Version:** **v0.2.1 prerelease**  
**Deployment branch:** `main`  
**Source branch:** `veilfall-v0.2.1-build`  
**Predecessor:** **v0.1.1**  
**Patch build date:** 2026-09-25

This file is the implementation truth for the current build. A design being locked does not imply that every part of it can be expressed by an Unciv extension ruleset without engine/state/UI changes.

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

## Validation performed
- All current mod JSON files on the development branch parse successfully.
- No duplicate custom unit, promotion, building, or belief names were found.
- Ashton, Knowledge, Rationalism, all six Marine units, all five slavery units, and the seven original supernatural Ashton units are present and cross-referenced.
- Native Unciv unique syntax used in this pass was checked against the current Unciv source/documentation during implementation.

## Validation still required
A real Unciv ruleset-validator/game load has **not yet been run** in this environment. The next acceptance gate is:

1. install/load this development branch in Unciv;
2. run **Locate mod errors**;
3. start a new Gods & Kings game with Veilfall enabled;
4. confirm Ashton appears and can found a city;
5. inspect Knowledge in the resource UI;
6. verify build menus, upgrade paths, promotions, Rationalism beliefs, and improvement times;
7. capture any validator/runtime errors before proceeding into the engine hooks.
