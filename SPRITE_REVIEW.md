# Veilfall sprite detail repair — review candidate

Branch: `veilfall-sprite-detail-repair`.
Baseline: v0.2.11, `de02479f97a367e8a12c40a8feb14beb9428ba27`.
This is an isolated artwork candidate. It is **not deployed or visually accepted**.
The release version and gameplay JSON remain unchanged pending approval.

## Cause supported by the artifacts

The released pipeline in `tools/v029/build_assets.py` reads 64×64 canonical
sources and resamples cropped figures using nearest-neighbor into native-size
frames. Continental Marines in FantasyHex occupy only **12×17 pixels** inside
a 32×28 frame. v0.2.11 also independently changes width and height for two
Marines, distorting their proportions. Increasing map zoom enlarges those coarse
samples; it cannot restore detail. The automated zero-soft-alpha test measures
hard edges, not coherent anatomy or visual quality. These explain the blocky
appearance in Paul's screenshots. They do not prove which mod bytes were
installed on his device; no device-installation claim is made here.

The earlier Continental Marine proof was recovered from an uncommitted local
development checkout, not from deployed main. Its selected source SHA-256 is
`942f335c05cfb5eca784d1a315cfe89c87a96b83db5128937a9ad6690bcb6326`.
That exact source is reused. The proof's integration files are not blindly copied.

The original `Images/TileSets/HexaRealm/Units/Veilwarden.png` was inspected as a
detail/style reference. Its oversized footprint is not reproduced or altered.

## Repair

All eleven units share the problematic processing path and receive repaired
sprites in Minimal, HexaRealm and FantasyHex: **33 effective map regions**.

| Marine line | Slavery line |
| --- | --- |
| Continental Marines | Slave |
| Marine Riflemen | Slave Raider |
| Expeditionary Marines | Mounted Slave Raider |
| Fleet Marine Force | Slave Hunter |
| Marine Expeditionary Unit | Industrial Slaver |
| Exo-Marine | |

The new sources preserve clothing, equipment and palette cues from the existing
unit identities. Ten source figures were generated with the built-in image tool;
the Continental source was recovered. Riflemen and the mounted raider received
targeted pose refinements after their first wide poses proved unsuitable for the
available map area. All generation prompts include recommended model and effort
and are retained under `tools/sprite_detail_repair/`.

Sources are reduced directly once to **256-pixel-wide texture frames**, with
proportional fitting, final-resolution alpha cleanup and transparent margins.
Frames are 256×224, except the taller HexaRealm/Minimal mounted frame, 256×264.
They are **not enlarged versions of the released coarse sprites**.
Final occupied widths/heights never exceed the released units' dimensions, and
heights are capped at 105% of comparable native figures. Native lateral centroids
are used, except Continental Marines retain the recovered proof's predecessor
anchor. The frame edge no longer cuts into the figure or its equipment.

Unciv 4.22.4, pinned at `3318515bfca2609a9edb127b59cfadbab6d58d38`, scales a
unit's full image width to the hex width in `TileLayer.setHexagonSize()`.
Therefore texture density and displayed footprint are independent. Its
`ImageGetter.loadModAtlases()` processes the listed atlases in insertion order,
overwriting matching drawable names. The final `sprite-detail` atlas replaces
only the intended 33 map regions. The production `TileSetStrings` resolver is
covered by the new headless runtime test.

## Review comparisons

Every comparison reads candidate figures back from the **packed texture**.
They show equal full-frame widths of 192 pixels and 96 pixels against native
grassland and desert, with preserved unit icons. Badge positions follow default
engine geometry; badge decoration is approximate.

These are **CPU texture-sampling simulations, not screenshots from a running
game**. There is no local graphical Unciv session or Android-device access.
Headless loader tests use mock OpenGL and do not establish visual acceptance.

- [Two reported units](tools/sprite_detail_repair/review/key-unit-comparison.png)
- [HexaRealm Marines](tools/sprite_detail_repair/review/hexarealm-marines.png)
- [HexaRealm slavery line](tools/sprite_detail_repair/review/hexarealm-slavery.png)
- [FantasyHex Marines](tools/sprite_detail_repair/review/fantasyhex-marines.png)
- [FantasyHex slavery line](tools/sprite_detail_repair/review/fantasyhex-slavery.png)

Minimal uses the same candidate pixels as HexaRealm and is separately included in
all 33 region checks and runtime selection tests. Native Minimal has no combat
sprite roster, so HexaRealm is explicitly used as its visual reference.

## Verification and boundaries

Local deterministic packing and preservation checks passed. The generated
`tools/sprite_detail_repair/verification.json` records source hashes, exact
packed hashes, every region's geometry and native-height ratios.

- Exactly 33 replacement regions; all other **47 v021 regions** remain effective
  and unchanged. All original game atlas pages remain unchanged.
- **187 predecessor files are byte-identical**, including every gameplay JSON,
  movement bonus, portrait, circular icon, Rationalism asset and prior test.
- Atlas bounds/non-overlap, source-to-packed reproduction, no clipping, binary
  alpha, unit uniqueness, grounding, physical size and lateral placement pass.
- A branch workflow verifies reproducibility and runs Unciv's real atlas loader
  and unit-name resolver for all 33 selections, plus the eleven inherited
  semantic/save-load/movement tests. See the branch's Actions run for its status;
  the workflow source alone is not execution evidence.

The existing root release notes and `ART_VERIFICATION.json` describe v0.2.11;
they are preserved historical baseline files, **not acceptance evidence for this
candidate**. This review and its verification report are the candidate record.

The additional 2048×2048 RGBA atlas costs approximately 16 MiB of uncompressed
texture memory. Actual Android performance and final visual acceptance remain
unverified. Generic embarked ship art and external third-party unitset overrides
are unchanged; there are no custom era/nation/embark sprite variants in this mod
requiring separate replacement.

## Files and reproduction

Runtime changes are exactly `Atlases.json`, `sprite-detail.atlas`, and
`sprite-detail.png`. Source, reference, review and verification files are under
`tools/sprite_detail_repair/`; CI is `.github/workflows/sprite-detail-review.yml`.

With Pillow 11.3.0 and repository history:

```sh
python3 tools/sprite_detail_repair/build.py --check
python3 tools/sprite_detail_repair/build.py
git diff --exit-code
```

Do not run the old release builder to integrate this candidate: that builder
asserts the old atlas list. Deploy only after Paul's explicit approval, using
the complete reviewed branch, then verify main and packed hashes remotely and
report the exact release commit. Publication does not prove device installation.
