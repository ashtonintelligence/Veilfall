"""Positive, corruption, and deterministic-rebuild tests of the release verifier."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
from PIL import Image
import build_assets as b

ROOT=Path(__file__).resolve().parents[2]
RESULTS=[]

def verify_report(root):
    result=b.verify(root)
    b.require(result==b.load_json(root/'ART_VERIFICATION.json'),'ART_VERIFICATION does not match deployed bytes')
    return result

def mutate_region(root,key,operation):
    _,boxes=b.atlas_read(root);x,y,w,h=boxes[key]
    path=root/'v021.png';page=Image.open(path).convert('RGBA')
    current=page.crop((x,y,x+w,y+h));changed=operation(current)
    b.require(changed.size==current.size,'Test mutation changed region dimensions')
    page.paste(changed,(x,y));page.save(path)
    source=root/'tools/v026/generated'/(key+'.png')
    if source.exists():changed.save(source)

def replace_json(root,rel,change):
    path=root/rel;data=b.load_json(path);change(data);path.write_text(json.dumps(data))

def plain_rect(im):
    out=Image.new('RGBA',im.size,(0,0,0,0))
    out.paste((40,50,60,255),(10,10,im.width-10,im.height-10));return out

def recolored(im):
    out=Image.new('RGBA',im.size,(130,160,180,0));out.putalpha(im.getchannel('A'));return out

def test_rejection(name,operation,expected):
    with TemporaryDirectory(prefix='veilfall-negative-') as tmp:
        root=Path(tmp)/'repo';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
        operation(root)
        try:verify_report(root)
        except (ValueError,KeyError,AssertionError,FileNotFoundError) as error:
            b.require(expected in str(error),f'{name}: rejected for unexpected reason: {error}')
            RESULTS.append({'test':name,'result':'PASS','expected_rejection':expected});print('PASS:',name)
        else:raise AssertionError(name+': corruption was accepted')

def main():
    verify_report(ROOT);RESULTS.append({'test':'valid_release','result':'PASS'});tests=[]
    tests.append(('capture_probability_regression',lambda r:(r/'jsons/UnitPromotions.json').write_text((r/'jsons/UnitPromotions.json').read_text().replace('with [50]% chance','with [25]% chance')),'Protected baseline file changed: jsons/UnitPromotions.json'))
    tests.append(('legacy_second_atlas_page_changed',lambda r:(r/'game2.png').write_bytes((r/'game2.png').read_bytes()+b'corruption'),'Protected baseline file changed: game2.png'))
    tests.append(('wrong_version',lambda r:replace_json(r,'jsons/ModOptions.json',lambda d:d.update(modVersion='0.2.6')),'ModOptions not limited'))
    tests.append(('wrong_atlas_list',lambda r:(r/'Atlases.json').write_text('["game"]'),'Protected baseline file changed: Atlases.json'))
    tests.append(('wrong_current_readme',lambda r:(r/'README.md').write_text((r/'README.md').read_text().replace('# Unciv: Veilfall v0.2.7','# Unciv: Veilfall v0.2.6')),'Wrong current version'))
    tests.append(('malformed_auxiliary_json',lambda r:(r/'broken.json').write_text('{invalid'),'Expecting property name'))
    tests.append(('missing_case_sensitive_key',lambda r:(r/'v021.atlas').write_text((r/'v021.atlas').read_text().replace('UnitPortraits/Slave\n','UnitPortraits/slave\n')),'Atlas keys missing/extra'))
    def overlap(r):
        text=(r/'v021.atlas').read_text();_,boxes=b.atlas_read(r)
        x,y,_,_=boxes['UnitPortraits/Slave Raider'];ox,oy,_,_=boxes['UnitPortraits/Slave']
        text=text.replace(f'UnitPortraits/Slave\n  rotate: false\n  xy: {ox}, {oy}',f'UnitPortraits/Slave\n  rotate: false\n  xy: {x}, {y}')
        (r/'v021.atlas').write_text(text)
    tests.append(('overlapping_regions',overlap,'Overlapping regions'))
    def corner(im):im.putpixel((0,0),(255,255,255,255));return im
    tests.append(('opaque_portrait_corner',lambda r:mutate_region(r,'UnitPortraits/Slave',corner),'portrait has opaque corners'))
    tests.append(('rectangular_portrait_background',lambda r:mutate_region(r,'UnitPortraits/Slave',plain_rect),'rectangular/background-like alpha'))
    def duplicate_portrait(r):
        regions,_=b.atlas_read(r);mutate_region(r,'UnitPortraits/Slave',lambda _:regions['UnitPortraits/Slave Raider'])
    tests.append(('slave_uses_raider_portrait',duplicate_portrait,'Packed/source pixel mismatch: UnitPortraits/Slave'))
    def duplicate_icon(r):
        regions,_=b.atlas_read(r);mutate_region(r,'UnitIcons/Slave',lambda _:regions['UnitIcons/Slave Raider'])
    tests.append(('duplicate_icons',duplicate_icon,'Packed/source pixel mismatch: UnitIcons/Slave'))
    tests.append(('colored_non_tint_safe_icon',lambda r:mutate_region(r,'UnitIcons/Slave',recolored),'Icon is not white/tint-safe'))
    def recolor_sprite(r):
        regions,_=b.atlas_read(r)
        for ts in b.SETS:mutate_region(r,f'TileSets/{ts}/Units/Slave',lambda _:recolored(regions[f'TileSets/{ts}/Units/Slave Raider']))
    tests.append(('slave_is_recolored_raider_sprite',recolor_sprite,'Packed/source pixel mismatch: TileSets/Minimal/Units/Slave'))
    def foot_mounted(r):
        regions,_=b.atlas_read(r)
        for ts in b.SETS:
            key=f'TileSets/{ts}/Units/Mounted Slave Raider'
            slave=regions[f'TileSets/{ts}/Units/Slave']
            def as_mounted_frame(current, src=slave):
                out=Image.new('RGBA',current.size,(0,0,0,0))
                crop=src.crop(src.getchannel('A').getbbox())
                scale=min((current.width-2)/crop.width,(current.height-2)/crop.height)
                wh=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)))
                crop=crop.resize(wh)
                out.paste(crop,((current.width-wh[0])//2,current.height-wh[1]-1),crop)
                return out
            mutate_region(r,key,as_mounted_frame)
    tests.append(('mounted_unit_replaced_by_infantry',foot_mounted,'Mounted footprint not broad/compact'))
    def oversized(im):
        crop=im.crop(im.getchannel('A').getbbox()).resize((61,54))
        out=Image.new('RGBA',im.size,(0,0,0,0))
        out.paste(crop,(1,1))
        return out
    tests.append(('oversized_map_sprite',lambda r:mutate_region(r,'TileSets/Minimal/Units/Slave Raider',oversized),'Sprite scale does not match native HexaRealm infantry'))
    tests.append(('unrelated_building_region_modified',lambda r:mutate_region(r,'BuildingPortraits/Athenaeum',corner),'Unrelated supplemental art changed'))
    tests.append(('fabricated_verification_report',lambda r:replace_json(r,'ART_VERIFICATION.json',lambda d:d.update(entry_count=81)),'ART_VERIFICATION does not match'))
    for name,operation,expected in tests:test_rejection(name,operation,expected)
    with TemporaryDirectory(prefix='veilfall-rebuild-') as tmp:
        root=Path(tmp)/'repo';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
        original=b.ROOT
        try:b.ROOT=root;b.build()
        finally:b.ROOT=original
        paths=['v021.png','v021.atlas','ART_VERIFICATION.json']
        paths += [p.relative_to(ROOT).as_posix() for p in (ROOT/'tools/v026/generated').rglob('*.png')]
        for rel in paths:b.require((ROOT/rel).read_bytes()==(root/rel).read_bytes(),'Nondeterministic rebuild: '+rel)
        RESULTS.append({'test':'second_build_byte_identical_58_files','result':'PASS'});print('PASS: second_build_byte_identical_58_files')
    report={'release':'v0.2.7','result':'PASS','test_count':len(RESULTS),'negative_test_count':len(tests),'tests':RESULTS}
    (ROOT/'tools/v026/test_results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='tests'},indent=2))

if __name__=='__main__':main()
