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
    protected={rel:digest(git_bytes(rel)) for rel in names if rel not in changed and not rel.startswith('tools/v026/')}
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
    new_options=dict(options);new_options.update(modVersion='0.2.7',lastUpdated='2026-09-26')
    (ROOT/'jsons/ModOptions.json').write_text(json.dumps(new_options,indent=2)+'\n')
    readme=git_bytes('README.md').decode('utf-8')
    readme=readme.replace('# Unciv: Veilfall v0.2.6','# Unciv: Veilfall v0.2.7',1)
    readme=readme.replace('**v0.2.6 prerelease**','**v0.2.7 prerelease**',1)
    readme=readme.replace('\`veilfall-v0.2.6-art-integration\`','\`veilfall-v0.2.7-art-integration\`',1)
    readme=readme.replace('**Predecessor:** **v0.2.5**','**Predecessor:** **v0.2.6**',1)
    readme=readme.replace('**Status:** v0.2.6 corrective art release; automated evidence in ART_VERIFICATION.json; in-game visual acceptance pending','**Status:** v0.2.7 unit-scale/framing correction; automated evidence in ART_VERIFICATION.json; in-game visual acceptance pending',1)
    readme += """\n## v0.2.7 native-scale map-unit framing\n\nRuntime screenshots from v0.2.6 showed the rebuilt figures were too small inside their map-sprite frames compared with adjacent vanilla combat units. v0.2.7 keeps the accepted character designs and transparent portraits/icons, but rescales and bottom-anchors map sprites to native Unciv tileset frames. FantasyHex uses 32x28 frames; HexaRealm uses 64x56 infantry frames and a taller 64x65 mounted frame. Minimal uses the HexaRealm-sized framing for consistent readability.\n\nThe Continental Marines calibration target is the adjacent vanilla Spearman shown in the acceptance screenshot: comparable apparent height, grounded foot position, and native in-frame placement. Infantry is normalized against infantry; Mounted Slave Raider is normalized against mounted-unit framing. No gameplay rules change.\n"""
    (ROOT/'README.md').write_text(readme,encoding='utf-8')

    status=git_bytes('BUILD_STATUS.md').decode('utf-8')
    status=status.replace('# Veilfall v0.2.6','# Veilfall v0.2.7',1)
    status=status.replace('**v0.2.6 prerelease**','**v0.2.7 prerelease**',1)
    status=status.replace('\`veilfall-v0.2.6-art-integration\`','\`veilfall-v0.2.7-art-integration\`',1)
    status=status.replace('**Predecessor:** **v0.2.5**','**Predecessor:** **v0.2.6**',1)
    status=status.replace('**Current status:** v0.2.6 corrective art release. Automated status is recorded in ART_VERIFICATION.json; in-game acceptance remains pending. Deployment is established by Git refs and the workflow, not this document alone.','**Current status:** v0.2.7 unit-scale/framing correction. Automated status is recorded in ART_VERIFICATION.json; in-game acceptance remains pending. Deployment is established by Git refs and the workflow, not this document alone.',1)
    status += """\n## v0.2.7 unit-scale/framing corrective pass\n\nThe v0.2.6 isolated figures remain the source art. This pass changes only map-sprite scale and transparent-frame placement so custom combat units read like neighboring vanilla units at runtime. FantasyHex assets use the native 32x28 unit frame. HexaRealm infantry uses 64x56 and mounted art uses 64x65. Figures are bottom-anchored with a one-pixel safety margin instead of centered in a 128x128 transparent canvas. The verification suite checks native frame sizes, scale bounds, bottom anchoring, preserved gameplay JSON, the exact 50% Slave Raider rule, and unchanged legacy art.\n"""
    (ROOT/'BUILD_STATUS.md').write_text(status,encoding='utf-8')
    (ROOT/'tools/v021/build_assets.py').write_text('''"""Compatibility entrypoint for the v021 atlas; current release is v0.2.7."""\nfrom pathlib import Path\nimport runpy\nimport sys\nsource=Path(__file__).resolve().parents[1]/"v026"\nsys.path.insert(0,str(source))\nrunpy.run_path(str(source/"build_assets.py"),run_name="__main__")\n''')
    (ROOT/'tools/v026/.gitignore').write_text('__pycache__/\\n*.py[cod]\\n')
    print('Prepared v0.2.7; protected baseline files:',len(protected),'preserved regions:',len(retained))

if __name__=='__main__':main()
