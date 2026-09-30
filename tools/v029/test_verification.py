"""Adversarial checks for preserved v0.2.9 art and the v0.2.10 hotfix."""
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image,ImageDraw,ImageFilter
import json,shutil
import build_assets as b

ROOT=Path(__file__).resolve().parents[2]
RESULTS=[]

def mutate_region(root,key,operation,update_generated=True):
    _,boxes=b.atlas_read(root); x,y,w,h=boxes[key]
    p=root/'v021.png'; page=Image.open(p).convert('RGBA')
    current=page.crop((x,y,x+w,y+h)); changed=operation(current)
    b.require(changed.size==current.size,'Mutation changed dimensions')
    page.paste(changed,(x,y)); page.save(p)
    if update_generated and key.startswith('TileSets/'):
        ts=key.split('/')[1]; name=key.split('/')[-1]
        gp=root/'tools/v029/generated'/ts/(name+'.png')
        if gp.exists(): changed.save(gp)

def reject(name,operation,expected):
    with TemporaryDirectory(prefix='veilfall-v029-') as tmp:
        root=Path(tmp)/'repo'; shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
        operation(root)
        old_root,old_generated=b.ROOT,b.GENERATED
        try:
            b.ROOT=root
            b.GENERATED=root/'tools/v029/generated'
            try: b.verify()
            except Exception as e:
                b.require(expected in str(e),f'{name}: wrong rejection: {e}')
                RESULTS.append({'test':name,'result':'PASS','expected_rejection':expected}); print('PASS:',name)
            else: raise AssertionError(name+': corruption accepted')
        finally:
            b.ROOT,b.GENERATED=old_root,old_generated

def main():
    b.verify(); RESULTS.append({'test':'valid_release','result':'PASS'})

    tests=[]
    tests.append(('wrong_version',
        lambda r:(r/'jsons/ModOptions.json').write_text((r/'jsons/ModOptions.json').read_text().replace('0.2.10','0.2.9')),
        'Wrong modVersion'))

    def restore_marine_workaround(r):
        p=r/'jsons/UnitPromotions.json'
        data=json.loads(p.read_text())
        marine=next(x for x in data if x['name']=='Marine Naval Integration')
        marine['uniques'].append(b.MARINE_CAPTURE_WORKAROUND)
        p.write_text(json.dumps(data,indent=2)+'\n')
    tests.append(('unsafe_marine_capture_workaround_reintroduced',restore_marine_workaround,
                  'Unsafe Marine capture workaround reintroduced'))

    def center_sprite(r):
        def op(im):
            box=im.getchannel('A').getbbox(); crop=im.crop(box)
            out=Image.new('RGBA',im.size,(0,0,0,0))
            out.alpha_composite(crop,((im.width-crop.width)//2,im.height-crop.height-1))
            return out
        mutate_region(r,'TileSets/HexaRealm/Units/Continental Marines',op)
    tests.append(('centered_sprite',center_sprite,'Packed sprite differs from native-derived build'))

    def soften_sprite(r):
        def op(im):
            box=im.getchannel('A').getbbox(); crop=im.crop(box)
            small=crop.resize((max(2,crop.width//2),max(2,crop.height//2)),Image.Resampling.BILINEAR)
            blur=small.resize(crop.size,Image.Resampling.BILINEAR)
            out=Image.new('RGBA',im.size,(0,0,0,0)); out.alpha_composite(blur,(box[0],box[1]))
            return out
        mutate_region(r,'TileSets/HexaRealm/Units/Marine Riflemen',op)
    tests.append(('soft_interpolation',soften_sprite,'Packed sprite differs from native-derived build'))

    def fill_religion_center(r):
        def op(im):
            out=im.copy(); d=ImageDraw.Draw(out); d.ellipse((48,48,80,80),fill=(255,255,255,255)); return out
        mutate_region(r,b.RELIGION_KEY,op,update_generated=False)
    tests.append(('rationalism_solid_center',fill_religion_center,'Packed Rationalism city icon differs from corrective mask'))

    def alter_portrait(r):
        p=r/'v021.png'; page=Image.open(p).convert('RGBA'); _,boxes=b.atlas_read(r)
        x,y,w,h=boxes['UnitPortraits/Continental Marines']
        region=page.crop((x,y,x+w,y+h)); region.putpixel((20,20),(255,0,0,255)); page.paste(region,(x,y)); page.save(p)
    tests.append(('portrait_changed',alter_portrait,'Preserved atlas region changed'))

    for t in tests: reject(*t)

    with TemporaryDirectory(prefix='veilfall-v029-rebuild-') as tmp:
        root=Path(tmp)/'repo'; shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
        old_root,old_generated=b.ROOT,b.GENERATED
        try:
            b.ROOT=root; b.GENERATED=root/'tools/v029/generated'
            b.build()
        finally:
            b.ROOT,b.GENERATED=old_root,old_generated
        for rel in ['v021.png','v021.atlas','ART_VERIFICATION.json']:
            b.require((ROOT/rel).read_bytes()==(root/rel).read_bytes(),'Nondeterministic rebuild: '+rel)
        RESULTS.append({'test':'deterministic_rebuild','result':'PASS'}); print('PASS: deterministic_rebuild')

    report={'release':'v0.2.10','result':'PASS','test_count':len(RESULTS),
            'negative_test_count':len(tests),'tests':RESULTS}
    (ROOT/'tools/v029/test_results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='tests'},indent=2))

if __name__=='__main__': main()
