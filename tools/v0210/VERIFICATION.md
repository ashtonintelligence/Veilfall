# v0.2.10 save-load verification

- Source baseline: `75331685057bcdb676c72a1a622c93912ed2c096` (v0.2.9).
- Development branch: `veilfall-v0.2.10-save-load-hotfix`.
- Target runtime: Unciv 4.22.4, commit `3318515bfca2609a9edb127b59cfadbab6d58d38`.
- Gameplay delta: remove only the conditional CanMoveOnWater unique from Marine
  Naval Integration. ModOptions version/date are metadata changes.
- No unit, promotion or civilization is renamed; save files are not edited.

## Automated gates

1. `python3 tools/v029/build_assets.py --check`: original deterministic sprite and
   Rationalism checks, updated release metadata and rejection of the unsafe rule.
2. `python3 tools/v029/test_verification.py`: valid release, adversarial version,
   unsafe-rule reintroduction, centered sprite, soft interpolation, filled religion
   center, altered portrait, and deterministic rebuild checks.
3. `python3 tools/v0210/verify_hotfix.py`: exact comparison against v0.2.9; all art
   and unrelated files unchanged, exact promotion removal, exact metadata changes,
   existing adjacency unique review. This script does not execute Unciv.
4. `VeilfallSaveLoadTest.kt`, copied into the pinned upstream tests project:
   full combined-ruleset semantic validation and four actual save-load cases
   (land/water, friendly/foreign neighbor). Each uses a Marine ordered before its
   neighboring Worker, serializes once, and calls `UncivFiles.loadGameFromFile`.
   The exact v0.2.9 rules must throw the reported uninitialized `civ` exception
   through Conditionals / MapUnitCache; the candidate must load the same file,
   preserving units, ownership, promotions and expected embarkation.

The repository workflow runs these gates on the development branch and main.
It has read-only contents permission and never rebuilds/commits art on main.
The test task uses `--rerun` so runtime results cannot be reused from Gradle cache
when external mod JSON changes; compiled engine dependencies can still be cached.
Local Gradle execution was blocked by the environment's Java network access;
GitHub Actions executed the actual runtime tests successfully, as recorded below.

## Static load-safety review

The pinned source queries `CanMoveOnWater` directly in
`MapUnitCache.updateUniques()` (line 83); its neighbor conditional reaches
`Conditionals.kt` line 315. `Tile.setUnitTransients()` (lines 862–868) assigns
owners and initializes one unit at a time. No engine code is patched here.

The remaining four adjacent-unit conditions are the three Operational Intelligence
Strength modifiers and the Slave Worker construction-time modifier. Their unique
types are not evaluated by the reviewed MapUnitCache initialization queries.
The pre-existing Celestial unit type has unconditional water travel, which has no
adjacent-unit/transient dependency; it is preserved. Marine water travel is not
made unconditional. The strict baseline comparison prevents any additional
ruleset changes from entering this hotfix.

## Results

**PASS — 2026-09-30.** Tested candidate:
`e30cb963cabfe7e47308c51faff2ce267fd53f26`.
[Successful complete workflow](https://github.com/ashtonintelligence/Veilfall/actions/runs/36753858104).

- All repository JSON parses; the full combined Veilfall / Gods & Kings ruleset
  passes the pinned engine's semantic validator with no Error-severity findings.
- All four save-load cases pass. Each reproduces v0.2.9's exact uninitialized `civ`
  exception from Conditionals / MapUnitCache, then loads the same serialized bytes
  successfully with v0.2.10. Unit count, owner, promotions and expected embarkation
  are preserved; no permanent water movement is granted.
- Eight deterministic/adversarial verifier tests pass, including rejection of
  reintroduced unsafe adjacency, softened/centered sprites, filled Rationalism
  center, portrait alteration, wrong version, and exact deterministic rebuilding.
- Strict v0.2.9 preservation and static load-safety review pass.
- All deployed art/source PNG and atlas files remain byte-identical to v0.2.9.
- Exact 50% Slave Raider rule and all other gameplay JSON are unchanged apart
  from the one removed unique and ModOptions version/date metadata.
- The first CI attempt failed a fixture precondition (the upstream helper does
  not grant base-unit promotions). The test now explicitly grants them; no engine
  or extra gameplay modification was needed. The corrected run above is green.

[Raw JUnit/HTML artifact](https://github.com/ashtonintelligence/Veilfall/actions/runs/36753858104/artifacts/11115962723),
ZIP SHA-256 `159d58601e7a1b3fbc6bc6db37cb294597aa7fa0883b9df5bc63d944f4221fb2`.
GitHub retains that artifact for 30 days; this report and the reproducible test
source persist in the repository. The release-documentation commit is also gated
by the same workflow before main advances.

### Remaining limitations and regression risk

The known behavior change is removal of v0.2.9's conditional non-embarked movement
around friendly civilians. Marines now keep normal embarkation there; enemy-civilian
capture on water remains unresolved. Embarked movement remains the engine's base
2 plus any already-applicable bonuses. Full naval classification and the unfinished
slavery systems are deferred. No additional regression was observed in the scoped
automated tests. Paul's actual save and rendered UI still require manual acceptance.

### Exact release files changed

- `.github/workflows/v021-art-build.yml`
- `ART_VERIFICATION.json`
- `BUILD_STATUS.md`
- `README.md`
- `jsons/ModOptions.json`
- `jsons/UnitPromotions.json`
- `tools/v0210/VERIFICATION.md`
- `tools/v0210/VeilfallSaveLoadTest.kt`
- `tools/v0210/verify_hotfix.py`
- `tools/v029/build_assets.py`
- `tools/v029/test_results.json`
- `tools/v029/test_verification.py`

## Manual acceptance (pending)

Update Veilfall, then Resume Paul's existing failing save. Confirm that the map
loads before testing anything else. Only then inspect Continental Marine sprites,
the Rationalism marker on a non-Ashton city, ordinary embark/disembark and unrelated
units. Enemy-civilian capture on water remains unsupported; no positive capture
acceptance is claimed. The headless fixtures do not establish acceptance of the
user's particular save or rendered game UI.
