"""Adversarial checks for the v0.2.8 map-sprite verifier."""
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image
import json,shutil
import build_assets as b

ROOT=Path(__file__).resolve().parents[2]
RESULTS=[]

def mutate_region(root,key,operation):
    _,boxes=b.atlas_read(root); x,y,w,h=boxes[key]
    p=root/'v021.png'; page=Image.open(p).convert('RGBA')
    current=page.crop((x,y,x+w,y+h)); changed=operation(current)
    b.require(changed.size==current.size,'Mutation changed dimensions')
    page.paste(changed,(x,y)); page.save(p)
    ts=key.split('/')[1]; name=key.split('/')[-1]
    gp=root/'tools/v028/generated'/ts/(name+'.png')
    if gp.exists(): changed.save(gp)

def reject(name,operation,expected):
    with TemporaryDirectory(prefix='veilfall-v028-') as tmp:
        root=Path(tmp)/'repo'; shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
        operation(root)
        old=b.ROOT
        try:
            b.ROOT=root
            try: b.verify()
            except Exception as e:
                b.require(expected in str(e),f'{name}: wrong rejection: {e}')
                RESULTS.append({'test':name,'result':'PASS','expected_rejection':expected}); print('PASS:',name)
            else: raise AssertionError(name+': corruption accepted')
        finally: b.ROOT=old

def main():
    b.verify(); RESULTS.append({'test':'valid_release','result':'PASS'})
    tests=[]
    tests.append(('capture_probability_regression',lambda r:(r/'jsons/UnitPromotions.json').write_text((r/'jsons/UnitPromotions.json').read_text().replace('with [50]% chance','with [25]% chance')),'Protected baseline file changed'))
    tests.append(('wrong_version',lambda r:(r/'jsons/ModOptions.json').write_text((r/'jsons/ModOptions.json').read_text().replace('0.2.8','0.2.7')),'Wrong modVersion'))
    def duplicate_slave(r):
        regions,_=b.atlas_read(r)
        for ts in b.SETS:
            mutate_region(r,f'TileSets/{ts}/Units/Slave',lambda _,ts=ts:regions[f'TileSets/{ts}/Units/Slave Raider'])
    tests.append(('slave_raider_duplicate',duplicate_slave,'Generated/packed sprite mismatch'))
    def float_sprite(r):
        def op(im):
            box=im.getchannel('A').getbbox(); crop=im.crop(box)
            out=Image.new('RGBA',im.size,(0,0,0,0)); y=max(1,im.height-crop.height-8); out.alpha_composite(crop,((im.width-crop.width)//2,y)); return out
        mutate_region(r,'TileSets/Minimal/Units/Continental Marines',op)
    tests.append(('sprite_not_bottom_anchored',float_sprite,'Sprite not bottom anchored'))
    def alter_portrait(r):
        p=r/'v021.png'; page=Image.open(p).convert('RGBA'); _,boxes=b.atlas_read(r)
        x,y,w,h=boxes['UnitPortraits/Continental Marines']; region=page.crop((x,y,x+w,y+h)); region.putpixel((20,20),(255,0,0,255)); page.paste(region,(x,y)); page.save(p)
    tests.append(('portrait_changed',alter_portrait,'Preserved atlas region changed'))
    for t in tests: reject(*t)

    with TemporaryDirectory(prefix='veilfall-v028-rebuild-') as tmp:
        root=Path(tmp)/'repo'; shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
        old_root,old_source,old_generated=b.ROOT,b.SOURCE_DIR,b.GENERATED
        try:
            b.ROOT=root
            b.SOURCE_DIR=root/'tools/v028/sprite_sources'
            b.GENERATED=root/'tools/v028/generated'
            b.build()
        finally:
            b.ROOT,b.SOURCE_DIR,b.GENERATED=old_root,old_source,old_generated
        for rel in ['v021.png','v021.atlas','ART_VERIFICATION.json']:
            b.require((ROOT/rel).read_bytes()==(root/rel).read_bytes(),'Nondeterministic rebuild: '+rel)
        RESULTS.append({'test':'deterministic_rebuild','result':'PASS'}); print('PASS: deterministic_rebuild')
    report={'release':'v0.2.8','result':'PASS','test_count':len(RESULTS),'negative_test_count':len(tests),'tests':RESULTS}
    (ROOT/'tools/v028/test_results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='tests'},indent=2))

if __name__=='__main__': main()
