# Veilfall v0.2.11 verification

Baseline: `29ab0a98eb8443810b91d41a07ad221f2b1f953e` (v0.2.10).
Branch: `veilfall-v0.2.11-marine-polish`.
Engine: Unciv 4.22.4, `3318515bfca2609a9edb127b59cfadbab6d58d38`.
Native art reference: `eba5356202ea101c696f34be1cffee8373eb109a` (unchanged).

## Authorized implementation

One `[+1] Movement` unique added to Marine Naval Integration; no per-unit base
movement changes. All unit definitions, strength, cost, upgrades and other abilities
remain unchanged. The unsafe adjacent-civilian water rule stays absent. Marine
capture of enemy civilians on water remains unresolved and is not attempted here.

Only Continental and Expeditionary Marine map-sprite geometry changes. Expeditionary
Marines met the same tall/narrow criterion in the required audit. Native Infantry's
Minimal/HexaRealm fallback silhouette is 25×36 and FantasyHex is 11×15.

| Unit / tilesets | Old occupied pixels | New occupied pixels | Lateral centroid shift |
| --- | --- | --- | ---: |
| Continental / Minimal, HexaRealm | 18×41 | 24×35 | +0.472 px |
| Continental / FantasyHex | 9×21 | 12×17 | −0.397 px |
| Expeditionary / Minimal, HexaRealm | 22×42 | 25×36 | −0.194 px |
| Expeditionary / FantasyHex | 11×19 | 12×16 | −0.424 px |

The exact bottom anchor and frame dimensions are retained. Half-pixel-or-less
centroid differences are from integer pixel placement, not recentering. Binary
alpha and nearest-neighbor rendering remain. Source character artwork is unchanged.

The remaining Marine audit: Riflemen are broad (36×34); Fleet Marines are 26×35;
MEU 25×37; Exo-Marine 28×36 in Minimal/HexaRealm. They do not exhibit the same
materially tall-and-narrow pair of defects. Their corresponding FantasyHex sprites
are also preserved. No slavery sprite is changed.

[Packed before/after/native comparison](proportion-comparison.png) includes
actual-size insets and nearest-neighbor zooms. Visual QA of this sheet is complete;
that does not substitute for Paul's final in-game acceptance.

## Gates

- Retain the original five Unciv semantic/save-load tests without changing their
  source. Four cases still reproduce the v0.2.9 crash and load the candidate.
- Add six runtime test methods: all six Marine units on land, Coast and Ocean;
  all six Marines serialized under v0.2.10 on land and Coast loaded unchanged
  under v0.2.11; and additive stacking with Astronomy.
- Exercise actual `MapUnit.getMaxMovement()`. Expected neutral maximums:
  land 3/3/3/3/4/5, embarked 3/3/3/3/3/3; Astronomy yields 4 for the tested
  Continental Marine. Names, IDs, owner, promotion set, remaining movement and
  serialized save bytes must remain unchanged through loading.
- Keep `--rerun`: tests must execute, while compiled engine dependencies may cache.
- Existing art verifier and deterministic rebuild; adversarial checks additionally
  reject a missing movement bonus and restoration of the old tall/narrow sprite.
- Strict baseline checks allow exactly the one promotion addition, version metadata,
  six intended sprite regions, build/test tooling and release documentation.
- All other 74 atlas regions, atlas layout, pixels outside the six regions,
  portraits, icons, Rationalism, slavery and unrelated JSON must be preserved.

## Automated results

Pending. No deployment until all available gates pass.

## Manual acceptance

v0.2.10 Resume, Rationalism, sharpness and lateral placement are accepted by Paul.
v0.2.11 acceptance remains pending:

1. Update Veilfall and Resume the existing save.
2. Inspect a Continental Marine on land: maximum movement increases by one
   (3 before other bonuses); check crispness, offset, stance and proportions.
3. Embark: maximum movement is 3 before other applicable bonuses.
4. Confirm the Rationalism city marker remains correct.

A mid-turn save retains its remaining movement points. Use the displayed maximum
or the next turn's replenishment to assess the bonus. It does not make Marines
naval units and does not solve enemy-civilian capture on water.
