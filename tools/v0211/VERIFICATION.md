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
  land 3/3/3/3/4/5, neutral coastal embarked 3/3/3/3/3/3. Ocean fixtures
  grant Astronomy for legal entry and expect 4 for all six; a separate Continental
  coastal case also verifies Astronomy stacking. Names, IDs, owner, promotion set, remaining movement and
  serialized save bytes must remain unchanged through loading.
- Keep `--rerun`: tests must execute, while compiled engine dependencies may cache.
- Existing art verifier and deterministic rebuild; adversarial checks additionally
  reject a missing movement bonus and restoration of the old tall/narrow sprite.
- Strict baseline checks allow exactly the one promotion addition, version metadata,
  six intended sprite regions, build/test tooling and release documentation.
- All other 74 atlas regions, atlas layout, pixels outside the six regions,
  portraits, icons, Rationalism, slavery and unrelated JSON must be preserved.

## Automated results

**PASS — 2026-09-30**, candidate
`949a3a9a32170f356b82d47bd82b60d35208de6b`.
[Successful workflow](https://github.com/ashtonintelligence/Veilfall/actions/runs/36759120157).

- **11 runtime tests passed:** five unchanged semantic/save-load tests plus six
  new movement methods covering 31 Marine movement scenarios.
- All six units calculate land maximums **3/3/3/3/4/5**, neutral coastal embarked
  maximums **3/3/3/3/3/3**, and legal Ocean maximums **4/4/4/4/4/4** with Astronomy.
  A separate coastal Astronomy case also returns 4. These are additive bonuses,
  not fixed caps; no terrain movement cost or naval classification is changed.
- All 12 existing-save fixtures (six units × land/Coast) gain exactly one maximum
  movement point when loaded under the candidate. Names, unit IDs, owners,
  promotions, remaining movement and serialized save bytes are preserved.
- The four original load-order fixtures still reproduce the v0.2.9 exception and
  successfully load under the candidate. The full combined ruleset passes the
  pinned engine's semantic validator with no Error-severity findings.
- **10 deterministic/adversarial tests passed** and both strict preservation
  gates passed. Exactly six map regions change; 74 regions and all outside pixels
  are preserved. Rationalism, portraits, icons, slavery sprites, original source
  art, atlas layout, Units.json and all unrelated gameplay are unchanged.
- The first run failed only its Ocean fixture setup: Optics does not permit Ocean
  entry. The corrected fixture grants Astronomy and includes that technology's
  pre-existing +1 movement in its expected value. No gameplay workaround was added.
- Actual tests executed with `--rerun`; this is not a JSON-only/static result.
  The final documentation commit is also gated before main advances.

[Raw JUnit/HTML evidence](https://github.com/ashtonintelligence/Veilfall/actions/runs/36759120157/artifacts/11116823615)
ZIP SHA-256: `b9e39873a55cad939dda2b3b6ab87316ce583f2abd66d55c08044ca7f16228ff`.
GitHub retains that artifact for 30 days; this report and the test source persist.

### Remaining regression risk and limits

No additional regression was observed in the scoped automated checks. Movement
maximums increase; mid-turn remaining points do not refill. Technology/policy
bonuses can make displayed maximums exceed the neutral values above. Visual QA
covers the packed artifacts, not Paul's device rendering. His actual save and
v0.2.11 appearance still require the narrow manual check below. Water civilian
capture remains unresolved; Special Forces and the larger slavery system remain
out of scope.

### Exact changed files

- `.github/workflows/v021-art-build.yml`
- `ART_VERIFICATION.json`
- `BUILD_STATUS.md`
- `README.md`
- `jsons/ModOptions.json`
- `jsons/UnitPromotions.json`
- `tools/v0210/verify_hotfix.py`
- `tools/v0211/VERIFICATION.md`
- `tools/v0211/VeilfallMovementTest.kt`
- `tools/v0211/preview.py`
- `tools/v0211/proportion-comparison.png`
- `tools/v0211/verify_release.py`
- `tools/v029/build_assets.py`
- `tools/v029/generated/FantasyHex/Continental Marines.png`
- `tools/v029/generated/FantasyHex/Expeditionary Marines.png`
- `tools/v029/generated/HexaRealm/Continental Marines.png`
- `tools/v029/generated/HexaRealm/Expeditionary Marines.png`
- `tools/v029/generated/Minimal/Continental Marines.png`
- `tools/v029/generated/Minimal/Expeditionary Marines.png`
- `tools/v029/test_results.json`
- `tools/v029/test_verification.py`
- `v021.png`

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
