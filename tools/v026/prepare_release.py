"""Prepare Veilfall v0.2.7 metadata using the pinned v0.2.5 preservation baseline."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess
from build_assets import ROOT, BASELINE, atlas_read, digest, require
from artwork import UNITS

RELEASE='v0.2.7'
PREDECESSOR='v0.2.6'

def git_bytes(rel):
    return subprocess.check_output(['git','show',BASELINE+':'+rel],cwd=ROOT)

def main():
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE],cwd=ROOT,text=True).splitlines()
    changed={
        'README.md','BUILD_STATUS.md','ART_VERIFICATION.json','v021.atlas','v021.png',
        'jsons/ModOptions.json','.github/workflows/v021-art-build.yml','tools/v021/build_assets.py'
    }
    protected={rel:digest(git_bytes(rel)) for rel in names if rel not in changed and not rel.startswith('tools/v026/')}
    with TemporaryDirectory() as tmp:
        base=Path(tmp)
        for rel in ('v021.atlas','v021.png'):
            (base/rel).write_bytes(git_bytes(rel))
        regions,_=atlas_read(base)
    rebuilt={f'{prefix}/{u}' for u in UNITS for prefix in (
        'UnitPortraits','UnitIcons','TileSets/Minimal/Units','TileSets/FantasyHex/Units','TileSets/HexaRealm/Units')}
    require(rebuilt<=set(regions) and len(regions)==80,'Baseline atlas contract differs')
    retained={k:digest(v.tobytes()) for k,v in regions.items() if k not in rebuilt}
    require(len(retained)==25,'Wrong preservation count')
    options=json.loads(git_bytes('jsons/ModOptions.json'))
    manifest={'baseline_commit':BASELINE,'mod_options':options,'unchanged_files':protected,
              'required_keys':sorted(regions),'preserved_regions':retained}
    (ROOT/'tools/v026/baseline_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    new_options=dict(options);new_options.update(modVersion='0.2.7',lastUpdated='2026-09-26')
    (ROOT/'jsons/ModOptions.json').write_text(json.dumps(new_options,indent=2)+'\n')
    print('Prepared',RELEASE,'from',PREDECESSOR,'protected files:',len(protected),'preserved regions:',len(retained))

if __name__=='__main__':
    main()
