> **Deprecated branch alias:** This branch name was created with incorrect versioning. Veilfall's current prerelease is **v0.2**. Use `veilfall-v0.2-build` for all further development and validation. The deployed predecessor remains **v0.1.1** on `main`.

# Veilfall

**Development branch:** `ashton-vnext-v1-build`  
**Status:** Ashton vNext v1 implementation in progress  
**Base ruleset:** Civ V - Gods & Kings

Veilfall is an Unciv extension mod combining the supernatural Veilfall roster with the Ashton civilization and its knowledge, expeditionary-warfare, and institutional systems.

## Ashton

**Leader:** Paul Ashton  
**Capital:** St. Paul  
**Motto:** *Wisdom in Peace, Fury in Defense*  
**Civilization ability:** **Evidence Before Confidence**

The current vNext content pass adds:

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

Knowledge is a civilization-wide stockpiled resource distinct from Science. Ashton generates it systematically from institutions and Scientist specialists; all civilizations can also gain Knowledge from technology completion, Natural Wonder discovery, era advancement, trade, and the Great Scientist **Document & Disseminate** action.

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

## Slavery v1

The JSON pass includes:

- Slave civilian unit;
- Slave Raider -> Mounted Slave Raider -> Slave Hunter -> Industrial Slaver;
- 25% prisoner-generation chance after eligible military victories;
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

## Installation during development

Use the `ashton-vnext-v1-build` branch for the current development build. The branch is intentionally separate from `main` until the vNext content pass has been validated in Unciv and the gameplay baseline is accepted.
