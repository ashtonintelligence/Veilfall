# Unciv: Veilfall v0.1.1

Veilfall is an extension mod for the **Civ V – Gods & Kings** ruleset in Unciv 4.21.13.

## Included units

- The Pale Horseman — concealed celestial executioner
- Azazel — possessing fallen celestial
- The First Blood — primordial vampire sovereign
- Moonfang Alpha — regenerating Moonborn predator
- The Frost Sovereign — ranged ruler of the frozen dead
- Rimebound Wight — producible undead infantry
- Veilwarden — producible human supernatural hunter

## Installation

### Install directly from Unciv

1. Open **Unciv → Mods → Download mod from URL**.
2. Enter `https://github.com/ashtonintelligence/Veilfall`.
3. Restart Unciv after the download finishes.
4. Import and open the accompanying Veilfall-enabled save.

If Veilfall was already installed, use the mod manager's **Update** action. If
the update is not offered, delete the installed copy and download it again from
the same URL. Version 0.1.1 corrects the packed-artwork location required by
Unciv on Android.

### Manual installation

Extract the `Veilfall` folder into Unciv's `mods` folder and keep the folder name exactly `Veilfall`.

The revised save already lists `Veilfall` as an active extension. It cannot load unless this mod is installed.

## Design notes

Celestials ignore political borders, ordinary terrain costs, zones of control, water barriers, and impassable terrain. They remain invisible until they attack and are revealed for one round afterward.

Possession uses Unciv's native defeated-unit capture mechanic. A successfully possessed unit returns under the possessor's owner at 50 health with no movement that turn. The engine caps the success probability at 80 percent.

Named sovereign units are limited to one per civilization. Rimebound Wights and Veilwardens may be produced normally.
