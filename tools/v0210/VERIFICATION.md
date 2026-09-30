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
Local Gradle execution was blocked by the environment's Java network access;
GitHub Actions provides the runtime execution path. Results are pending until
recorded below; the presence of the test source is not evidence of execution.

## Results

Pending automated execution. Do not deploy on the strength of this document alone.

## Manual acceptance (pending)

Update Veilfall, then Resume Paul's existing failing save. Confirm that the map
loads before testing anything else. Only then inspect Continental Marine sprites,
the Rationalism marker on a non-Ashton city, ordinary embark/disembark and unrelated
units. Enemy-civilian capture on water remains unsupported; no positive capture
acceptance is claimed. The headless fixtures do not establish acceptance of the
user's particular save or rendered game UI.
