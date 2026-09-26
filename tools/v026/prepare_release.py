"""Prepare release metadata and preservation manifest from the pinned Git baseline.
This script runs on the working branch only, before any generated art is committed.
It reads actual predecessor objects, not recollected hashes or current output files.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import io
import json
import subprocess
from build_assets import ROOT,BASELINE,atlas_read,digest,require
from artwork import UNITS


def git_bytes(rel):
    return subprocess.check_output(['git','show',BASELINE+':'+rel],cwd=ROOT)


def main():
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE],cwd=ROOT,text=True).splitlines()
    changed={'README.md','BUILD_STATUS.md','ART_VERIFICATION.json','v021.atlas','v021.png','jsons/ModOptions.json','.github/workflows/v021-art-build.yml','tools/v021/build_assets.py'}
    protected={rel:digest(git_bytes(rel)) for rel in names if rel not in changed}
    with TemporaryDirectory() as tmp:
        base=Path(tmp)
        for rel in ['v021.atlas','v021.png']:(base/rel).write_bytes(git_bytes(rel))
        regions,_=atlas_read(base)
    rebuilt={f'{prefix}/{u}' for u in UNITS for prefix in ['UnitPortraits','UnitIcons','TileSets/Minimal/Units','TileSets/FantasyHex/Units','TileSets/HexaRealm/Units']}
    require(rebuilt<=set(regions) and len(regions)==80,'Baseline atlas contract differs')
    retained={k:digest(v.tobytes()) for k,v in regions.items() if k not in rebuilt}
    require(len(retained)==25,'Wrong preservation count')
    options=json.loads(git_bytes('jsons/ModOptions.json'))
    manifest={'baseline_commit':BASELINE,'mod_options':options,'unchanged_files':protected,'required_keys':sorted(regions),'preserved_regions':retained}
    (ROOT/'tools/v026/baseline_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    new_options=dict(options);new_options.update(modVersion='0.2.6',lastUpdated='2026-09-26')
    (ROOT/'jsons/ModOptions.json').write_text(json.dumps(new_options,indent=2)+'\n')
    readme=git_bytes('README.md').decode('utf-8').split('## Installation')[0]
    readme=readme.replace('# Unciv: Veilfall v0.2.5','# Unciv: Veilfall v0.2.6').replace('**v0.2.5 prerelease**','**v0.2.6 prerelease**').replace('`veilfall-v0.2.5-art-integration`','`veilfall-v0.2.6-art-integration`').replace('**Predecessor:** **v0.2.4**','**Predecessor:** **v0.2.5**').replace('**Status:** v0.2.5 source-portrait corrective patch deployed for in-game acceptance','**Status:** v0.2.6 corrective art release; automated evidence in ART_VERIFICATION.json; in-game visual acceptance pending')
    readme+='''## Installation

Install or update Veilfall from the repository's default `main` branch. The v0.2.6
release source is `veilfall-v0.2.6-art-integration`. The main ref is advanced only
after the integration workflow and independent artifact verification succeed.

## v0.2.6 isolated-character art rebuild

This corrective release rebuilds all eleven Marine/slavery-line figures from
original, layered game-asset illustrations, not crops of predecessor concept-art
cards. The style is intentionally stylized and silhouette-led. Each unit receives
a 256-pixel transparent portrait, white tint-safe UnitIcon, and compact transparent
map sprite under Minimal, FantasyHex, and HexaRealm. The three tilesets deliberately
share each unit's sprite. No scenery, card border, or text is part of a unit asset.

The Slave is unarmed and narrow, with close arms and no combat equipment. Slave
Raider has a lunging sword-and-net pose; Mounted Slave Raider has a horse/lance;
Slave Hunter has a wide-brim hat, split coat, and long firearm; Industrial Slaver
has a heavy coat, armored vest, cap, and shotgun. Marine silhouettes progress from
tricorn/musket through a kneeling kepi rifleman, campaign-hat expedition kit, steel
helmet/webbing, modern plate carrier/antenna, and broad powered armor with an
energy weapon. Exo-Marine retains navy, black, gold, and scarlet accents.

`Atlases.json` remains `["game","v021"]`. The 25 unrelated supplemental regions
are pixel-identical to the predecessor. All legacy game atlas pages and source
assets remain byte-identical. Gameplay JSON is unchanged except ModOptions
version/date metadata. The capture rule remains exactly:

```text
Free [Slave] appears <upon defeating a [Military] unit> <with [50]% chance>
```

The Military filter is unchanged and no Barbarian exclusion has been added.
This is preservation of the implementation, not a new engine-level probability test.

## Rebuild and acceptance evidence

The workflow `.github/workflows/v021-art-build.yml` uses Pillow 11.3.0 and readable
sources in `tools/v026/`. The legacy `tools/v021/build_assets.py` entrypoint now
delegates to the new builder, not the retired crop pipeline. Old `tools/v022`
inputs remain only as historical data and are not read by the new unit builder.

Run `python3 tools/v026/build_assets.py` to rebuild, then
`python3 tools/v026/build_assets.py --check` to verify files actually on disk.
`ART_VERIFICATION.json` records the automated results and hashes, transparency,
size bounds, normalized silhouette comparisons, and baseline preservation.
`tools/v026/test_results.json` records adversarial tests of the verifier itself.
The 55 source PNGs and packed-asset QA sheets are retained under `tools/v026/`.
An automated pass does not establish manual in-game visual acceptance.

After updating, inspect all eleven portraits and tinted icons in Civilopedia,
check small-scale sprites in each tileset, and spot-check the original supernatural
units. Runtime observations are the remaining evidence; build logs, hashes, and
rule text already exist in the automated record and need not be transcribed.

## Historical art lineage

v0.2.1 introduced the supplemental atlas. v0.2.2/v0.2.3 revised artwork and
integration. v0.2.4 reduced map scale, but its generic portraits were not accepted.
The predecessor v0.2.5 restored source-art crops; runtime screenshots still showed
background and scenery/card remnants. v0.2.6 supersedes that crop pipeline while
retaining small map footprints. These are historical notes, not current deployment
claims. Actual deployment is established by Git refs and successful workflow runs.
'''
    (ROOT/'README.md').write_text(readme,encoding='utf-8')
    status=git_bytes('BUILD_STATUS.md').decode('utf-8').split('## Validation performed')[0]
    status=status.replace('# Veilfall v0.2.5','# Veilfall v0.2.6').replace('**v0.2.5 prerelease**','**v0.2.6 prerelease**').replace('`veilfall-v0.2.5-art-integration`','`veilfall-v0.2.6-art-integration`').replace('**Predecessor:** **v0.2.4**','**Predecessor:** **v0.2.5**').replace('**Patch build date:** 2026-09-25','**Patch build date:** 2026-09-26').replace('**Current status:** v0.2.5 source-portrait repair passed automated verification and is deployed to `main` for in-game acceptance.','**Current status:** v0.2.6 corrective art release. Automated status is recorded in ART_VERIFICATION.json; in-game acceptance remains pending. Deployment is established by Git refs and the workflow, not this document alone.')
    status+='''## v0.2.6 automated release gates

The build recomputes evidence from the packed PNG/atlas rather than only in-memory
source assets, and checks ART_VERIFICATION.json against those bytes. Gates cover
80 exact nonoverlapping keys, 55 rebuilt regions, 25 pixel-identical unrelated
regions, all repository JSON, version 0.2.6, transparent corners/borders,
nonrectangular figure masks, white tint-safe icons, compact sprite bounds, and
11 distinct normalized silhouettes for each asset class. Slave versus Slave
Raider is explicitly compared without relying on color.

The preservation manifest is generated from actual objects at predecessor commit
`cd377c5a2ef04c9447656673e06c6a9fc4d47a97`. Protected gameplay files, the entire legacy
game atlas including game2.png through game6.png, raw supernatural art, and old
source data must remain byte-identical. Only ModOptions version/date metadata
changes. All four capture-line units retain Slave Raider Doctrine and its exact
50% Military-kill rule, with no new Barbarian exclusion.

Original layered figures in tools/v026/artwork.py do not read predecessor unit
crops. Portraits are intentionally stylized and isolated. All 55 source PNGs must
match their packed regions pixel-for-pixel. The dependency is pinned to Pillow
11.3.0 in Actions. The old builder entrypoint delegates to this new implementation.

The verifier is tested against deliberate corruptions; results are recorded in
tools/v026/test_results.json. A full second build must reproduce every generated
source PNG, the supplemental PNG/atlas, and the verification report byte-for-byte.
The build job pushes artifacts to `veilfall-v0.2.6-art-integration`. Main advances
separately after a successful run and artifact inspection. The same workflow
performs a read-only check after main advances.

## In-game acceptance still required

Automated results are not an Unciv runtime test or user art approval. Unciv has not
been launched with these assets in the build environment. After updating, inspect
Civilopedia isolation, Slave versus Raider under nation tint, all six Marine
stages, map scale and mounting in all three tilesets, and the seven legacy
supernatural units. Locate mod errors remains an engine-level check. Screenshots
are only needed for runtime defects not captured in existing automated evidence;
no manual transcription of logs or hashes is required.

## Historical corrective-release context

v0.2.1 added the supplemental atlas; v0.2.3 repaired integration/icons; v0.2.4
established smaller footprints but its generic portraits were not accepted. The
predecessor v0.2.5 restored source-derived portraits that still exposed backgrounds.
v0.2.6 replaces that approach. Broader gameplay implementation and deferred-work
statements above are unchanged by this art-only release.
'''
    (ROOT/'BUILD_STATUS.md').write_text(status,encoding='utf-8')
    (ROOT/'tools/v021/build_assets.py').write_text('''"""Compatibility entrypoint for the v021 atlas; current release is v0.2.6."""
from pathlib import Path
import runpy
import sys
source=Path(__file__).resolve().parents[1]/'v026'
sys.path.insert(0,str(source))
runpy.run_path(str(source/'build_assets.py'),run_name='__main__')
''')
    (ROOT/'tools/v026/.gitignore').write_text('__pycache__/\n*.py[cod]\n')
    print('Prepared v0.2.6; protected baseline files:',len(protected),'preserved regions:',len(retained))

if __name__=='__main__':main()
