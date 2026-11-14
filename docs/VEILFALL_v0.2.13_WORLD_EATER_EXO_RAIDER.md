# Veilfall 0.2.13 - World-Eater and Exo Slave Raider

November 14, 2026.

* Integrate **The World-Eater** from the archived Veilfall World Eater Devastation Test v0.1.2 release into the main mod. Preserve prototype properties, but increase movement from 3 to **5** hexes per turn.
* Add original World-Eater custom packed atlas sprite and its UI icon and portrait.
* Add a new final slaver line upgrade **Exo Slave Raider** (movement **5**, strength **110**, required Future Tech), using alias artwork from the existing Exo-Marine atlas regions until distinct character art is produced.
* Extend progression: Slave Raider -> Mounted Slave Raider -> Slave Hunter -> Industrial Slaver -> Exo Slave Raider.
* Raise **Slave Raider Doctrine**'s slave spawn chance to **67%** after a military kill.
* Unit appears on qualifying defeat as a triggered free Slave. It does not capture and convert the defeated military unit directly. The 67% trigger must still satisfy an available placement.
* World-Eater's standard-mod city attacks cannot automatically halve population or destroy buildings individually; these are engine-level design goals and not included in this release.
* Save-game handoff: the separate turn-125 edited save retains `mods: ["Veilfall"]` and adds a single Ashton World-Eater in Australia; upgrades existing five Ashton Slave Raiders to Exo Slave Raiders; grants +1,000,000 gold, +20,000 overflow Science and +10,000 stored Culture.

## Compatibility and tests
JSON syntax and declared Unciv unique strings are checked against source. Archived World-Eater atlas sprites from v0.1.2 are preserved. Artwork for Exo Slave Raider is an explicit fallback alias to the Exo-Marine image. No Android runtime test has been performed. Update Veilfall to v0.2.13 and restart Unciv before loading the edited save.
