"""Exact v0.2.10 preservation gate for the two authorized v0.2.11 objectives."""
from pathlib import Path
from io import BytesIO
import json, subprocess, sys
from PIL import Image, ImageChops, ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v029'))
import build_assets as b

BASELINE='29ab0a98eb8443810b91d41a07ad221f2b1f953e'
EXPECTED_NAMES={'Continental Marines','Expeditionary Marines'}
EXPECTED_KEYS={f'TileSets/{ts}/Units/{n}' for ts in b.SETS for n in EXPECTED_NAMES}
ALLOWED={
    '.github/workflows/v021-art-build.yml','README.md','BUILD_STATUS.md',
    'ART_VERIFICATION.json','jsons/ModOptions.json','jsons/UnitPromotions.json','v021.png',
    'tools/v029/build_assets.py','tools/v029/test_verification.py','tools/v029/test_results.json',
    'tools/v0210/verify_hotfix.py', 'tools/v0211/verify_release.py',
    'tools/v0211/VeilfallMovementTest.kt','tools/v0211/preview.py',
    'tools/v0211/proportion-comparison.png','tools/v0211/VERIFICATION.md',
} | {f'tools/v029/generated/{ts}/{name}.png' for ts in b.SETS for name in EXPECTED_NAMES}

def old(path): return subprocess.check_output(['git','show',BASELINE+':'+path],cwd=b.ROOT)

def verify():
    files=subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE],cwd=b.ROOT,text=True).splitlines()
    for rel in files:
        if rel not in ALLOWED:
            b.require((b.ROOT/rel).read_bytes()==old(rel),'Protected v0.2.10 file changed: '+rel)
    tracked=subprocess.check_output(['git','ls-files'],cwd=b.ROOT,text=True).splitlines()
    untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=b.ROOT,text=True).splitlines()
    for rel in (set(tracked+untracked)-set(files)):
        if '__pycache__' not in Path(rel).parts:
            b.require(rel in ALLOWED,'Unexpected added file: '+rel)
    expected=json.loads(old('jsons/UnitPromotions.json'))
    promotion=next(x for x in expected if x['name']=='Marine Naval Integration')
    index=promotion['uniques'].index('May attack when embarked')+1
    promotion['uniques'].insert(index,'[+1] Movement')
    b.require(expected==b.load_json(b.ROOT/'jsons/UnitPromotions.json'),'Only one shared Movement unique may change')
    expected_options=json.loads(old('jsons/ModOptions.json'))
    expected_options['modVersion']='0.2.11'
    b.require(expected_options==b.load_json(b.ROOT/'jsons/ModOptions.json'),'Unexpected ModOptions delta')
    before,boxes=b.parse_atlas(old('v021.atlas'),old('v021.png'),'v021.png')
    current,current_boxes=b.atlas_read(b.ROOT)
    b.require(boxes==current_boxes,'Atlas frames/packing changed')
    changed={k for k in before if before[k].tobytes()!=current[k].tobytes()}
    b.require(changed==EXPECTED_KEYS,'Unexpected atlas region delta: '+str(changed^EXPECTED_KEYS))
    rows=[]
    for key in sorted(changed):
        prev,now=b.alpha_stats(before[key]),b.alpha_stats(current[key])
        b.require(current[key].size==before[key].size,'Frame size changed: '+key)
        b.require(now['w']>prev['w'] and now['h']<prev['h'],'Proportion correction missing: '+key)
        b.require(now['bbox'][3]==prev['bbox'][3],'Bottom anchor moved: '+key)
        b.require(abs(now['centroid_x']-prev['centroid_x'])<=0.5,'Accepted lateral anchor moved: '+key)
        b.require(now['soft_alpha_ratio']==0,'Nonbinary alpha: '+key)
        rows.append({'region':key,'before_bbox':prev['bbox'],'after_bbox':now['bbox'],
            'lateral_shift_pixels':round(now['centroid_x']-prev['centroid_x'],3)})
    # Check transparent page padding too; region checks alone would miss that.
    prior=Image.open(BytesIO(old('v021.png'))).convert('RGBA')
    page=Image.open(b.ROOT/'v021.png').convert('RGBA')
    for key in changed:
        x,y,w,h=boxes[key]
        prior.paste((0,0,0,0),(x,y,x+w,y+h)); page.paste((0,0,0,0),(x,y,x+w,y+h))
    b.require(prior.tobytes()==page.tobytes(),'Pixels outside intended regions changed')
    workflow=(b.ROOT/'.github/workflows/v021-art-build.yml').read_text()
    b.require(':tests:test --rerun ' in workflow,'Fresh runtime gate removed')
    b.require('com.unciv.logic.VeilfallSaveLoadTest' in workflow,'Save-load regression gate removed')
    b.require('com.unciv.logic.VeilfallMovementTest' in workflow,'Movement runtime gate removed')
    b.require('3318515bfca2609a9edb127b59cfadbab6d58d38' in workflow,'Pinned runtime changed')
    return {'release':'v0.2.11','result':'PASS','baseline':BASELINE,'changed_atlas_regions':6,
            'preserved_atlas_regions':74,'rationalism_region_byte_identical':True,
            'units_json_byte_identical':True,'movement_unique_added_once':True,
            'existing_save_load_test_source_byte_identical':True,'proportions':rows}

if __name__=='__main__': print(json.dumps(verify(),indent=2))
