# Veilfall v0.2.12-rc1 — drone integration acceptance record

## Baseline and scope

- Source repository: `ashtonintelligence/Veilfall`
- Baseline `main` commit: `aeb740d4fcac310d98e58a73c06bed1b56233bd4`
- Integration branch: `veilfall-drone-integration-20261105`
- Branch-only changes: two additive drone definitions, one additive `Gravitic Drone` unit type, new `drone-review` atlas/image, Ashton colors, full UTC metadata date/version, explanatory documentation and source art.
- The Pale Horseman and Azazel remain unchanged in `jsons/Units.json`, along with the previous Marine, slavery and supernatural roster.

## Source-verified structural assertions

- `jsons/Units.json`: 18 original definitions retained in original order, with two new drone definitions appended (20 total).
- `jsons/UnitTypes.json`: all five original types retained, `Gravitic Drone` appended (six total).
- `jsons/Nations.json`: Ashton nation and existing abilities preserved; only outer/inner RGB changed to `[165, 0, 52]` and `[255, 208, 0]`.
- `Atlases.json`: original `game`, `v021`, `sprite-detail` remain first, followed by `drone-review`.
- `drone-review.png` and `drone-review.atlas` are byte-identical to the approved, Android-tested companion package. The atlas contains 10 regions: six map sprite variants, two icons, and two portraits.
- Source art preserved under `tools/drone/`. Rebuild: `python tools/drone/build_drone_atlas.py`; compare against shipped assets without changing them: `python tools/drone/build_drone_atlas.py --check`.
- The source-art rebuild's 1024 × 1024 RGBA pixel comparison against the accepted atlas **passed** locally, as did the atlas index text comparison.
- `jsons/ModOptions.json` uses full date `2026-11-05T00:00:00Z` to avoid an Android 4.22.17 date-parser crash.

## Scenario

The attached `review-downloads/Crash_Site_Drones_2x2_No_Proxies_Integrated.zip` contains `Crash_Site_Drones_2x2_Integrated.json`, a turn-zero Crash Site save:

- `gameParameters.mods = ["Veilfall"]`
- Exactly two `Horizon-class Recon Drone` plus two `Valkyrie-class Assault Drone` near Crash Site
- The previous `The Pale Horseman` instance (id 33 at 4,12) and `Azazel` instance (id 34 at 4,13) are absent; their unit definitions are NOT deleted
- All other map tiles/units remain unchanged, `lastUnitId` remains 427
- Original turn-18 save and prior companion test save are unmodified

## Test evidence and limits

**User-confirmed on Android (Unciv 4.22.17):** companion package installed, standalone extension validation passed after removal of the redundant Ashton nation override, drone art accepted at gameplay scale, and all reported movement, combat, reconnaissance, concealment and recovery tests passed.

**Locally verified for this integrated candidate:** source-preserving JSON changes, reviewed atlas and pixel-identical rebuild, metadata syntax, and corrected turn-zero scenario unit counts. This is not a claim of fresh Android runtime testing of the integrated branch.

**Remaining acceptance:** install branch with Unciv “Download mod from URL”, check `Veilfall`, confirm both drone types display and act correctly with crimson-and-gold Ashton, and load the integrated-only turn-zero save. Existing Veilfall nation unique validation warnings are inherited and not changed in this release.

**Publishing boundary:** review branch only. Do not merge to `main` without final integrated in-game acceptance.
