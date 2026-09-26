"""Build/check the v0.2.7 supplemental atlas without writing legacy game art.
Run from the repository root; --check verifies committed bytes without rebuilding.
"""
from pathlib import Path
from PIL import Image
import argparse
import hashlib
import json
import re
from artwork import UNITS, make_assets

ROOT=Path(__file__).resolve().parents[2]
BASELINE='cd377c5a2ef04c9447656673e06c6a9fc4d47a97'
RULE='Free [Slave] appears <upon defeating a [Military] unit> <with [50]% chance>'
SETS=['Minimal','FantasyHex','HexaRealm']

def require(ok,message):
    if not ok:raise ValueError(message)

def digest(data):return hashlib.sha256(data).hexdigest()
def load_json(p):return json.loads(p.read_text(encoding='utf-8'))

def atlas_read(root):
    lines=(root/'v021.atlas').read_text(encoding='utf-8').splitlines()
    require(lines[:5]==['v021.png','size: 2048, 2048','format: RGBA8888','filter: Nearest, Nearest','repeat: none'],'Atlas page contract changed')
    image=Image.open(root/'v021.png').convert('RGBA')
    require(image.size==(2048,2048),'Unexpected atlas dimensions')
    regions={};boxes={}
    for i in range(5,len(lines),7):
        c=lines[i:i+7];require(len(c)==7,'Incomplete atlas entry');key=c[0]
        require(key not in regions,'Duplicate atlas key: '+key)
        require(c[1]=='  rotate: false' and c[5]=='  offset: 0, 0' and c[6]=='  index: -1','Unsupported atlas transformation: '+key)
        m=re.fullmatch(r'  xy: (\d+), (\d+)',c[2]);s=re.fullmatch(r'  size: (\d+), (\d+)',c[3])
        require(m is not None and s is not None,'Malformed atlas bounds: '+key)
        x,y=map(int,m.groups());w,h=map(int,s.groups())
        require(c[4]==f'  orig: {w}, {h}','Trim/original size changed: '+key)
        require(x>=2 and y>=2 and w>0 and h>0 and x+w<=2046 and y+h<=2046,'Out-of-bounds region: '+key)
        for other,(ox,oy,ow,oh) in boxes.items():
            require(x+w<=ox or ox+ow<=x or y+h<=oy or oy+oh<=y,'Overlapping regions: '+key+' / '+other)
        boxes[key]=(x,y,w,h);regions[key]=image.crop((x,y,x+w,y+h))
    return regions,boxes

def normalized_mask(im):
    a=im.getchannel('A').point(lambda v:255 if v>=128 else 0);box=a.getbbox()
    require(box is not None,'Empty alpha mask')
    return a.crop(box).resize((64,64),Image.Resampling.NEAREST)

def similarity(a,b):
    aa=normalized_mask(a).tobytes();bb=normalized_mask(b).tobytes()
    common=sum(1 for x,y in zip(aa,bb) if x and y)
    union=sum(1 for x,y in zip(aa,bb) if x or y)
    return round(common/union,6)

def image_metrics(im,kind,name):
    a=im.getchannel('A');box=a.getbbox();require(box is not None,kind+' is empty: '+name)
    width=box[2]-box[0];height=box[3]-box[1]
    require(all(a.getpixel(p)==0 for p in [(0,0),(im.width-1,0),(0,im.height-1),(im.width-1,im.height-1)]),kind+' has opaque corners: '+name)
    border=1 if kind=='sprite' else 7
    require(box[0]>=border and box[1]>=border and box[2]<=im.width-border and box[3]<=im.height-border,kind+' touches canvas edge or is cropped: '+name)
    occupied=sum(v>=128 for v in a.tobytes());coverage=occupied/(im.width*im.height);bbox_coverage=occupied/(width*height)
    require(0<coverage<0.78 and bbox_coverage<0.89,kind+' has rectangular/background-like alpha: '+name)
    if kind=='portrait':
        require(im.size==(256,256),'Portrait size: '+name)
        require(150<=height<=240 and (60 if name=='Slave' else 80)<=width<=240,'Portrait does not fill UI appropriately: '+name)
    elif kind=='icon':
        require(im.size==(128,128),'Icon size: '+name)
        require(all((r,g,b)==(255,255,255) for r,g,b,aa in im.getdata() if aa>0),'Icon is not white/tint-safe: '+name)
    else:
        valid_sizes={(32,28),(64,56),(64,65)}
        require(im.size in valid_sizes,'Unexpected native sprite frame size: '+name+' '+repr(im.size))
        if name=='Mounted Slave Raider':
            if im.size==(32,28):
                require(22<=width<=30 and 18<=height<=26 and width/height>=0.8,'Mounted footprint not broad/compact')
            else:
                require(44<=width<=62 and 36<=height<=63 and width/height>=0.8,'Mounted footprint not broad/compact')
        else:
            if im.size==(32,28):
                require(8<=width<=30 and 20<=height<=26,'Sprite scale does not match native FantasyHex infantry: '+name)
            else:
                require(16<=width<=60 and 42<=height<=54,'Sprite scale does not match native HexaRealm infantry: '+name)
        require(box[3]>=im.height-2,'Sprite is not bottom-anchored like native combat units: '+name)
    return {'bbox':list(box),'w':width,'h':height,'coverage':round(coverage,6),'bbox_coverage':round(bbox_coverage,6),'rgba_sha256':digest(im.tobytes()),'alpha_sha256':digest(a.tobytes()),'normalized_alpha_sha256':digest(normalized_mask(im).tobytes())}

def verify(root=ROOT):
    root=Path(root);manifest=load_json(root/'tools/v026/baseline_manifest.json')
    require(manifest['baseline_commit']==BASELINE,'Wrong predecessor baseline')
    for rel,sha in manifest['unchanged_files'].items():
        p=root/rel;require(p.is_file() and digest(p.read_bytes())==sha,'Protected baseline file changed: '+rel)
    for p in root.rglob('*.json'):
        if '.git' not in p.parts:load_json(p)
    opts=load_json(root/'jsons/ModOptions.json');expected=dict(manifest['mod_options'])
    expected.update(modVersion='0.2.7',lastUpdated='2026-09-26')
    require(opts==expected,'ModOptions not limited to release metadata')
    require(load_json(root/'Atlases.json')==['game','v021'],'Atlas list changed')
    promos=load_json(root/'jsons/UnitPromotions.json');doctrine=next(p for p in promos if p['name']=='Slave Raider Doctrine')
    require(RULE in doctrine['uniques'],'Exact 50% Military-kill capture rule missing')
    require(not any('[25]%' in s for s in doctrine['uniques']),'25% capture rule regression')
    units={u['name']:u for u in load_json(root/'jsons/Units.json')}
    require(set(UNITS)<=set(units),'Case-sensitive unit name mismatch')
    for name in ['Slave Raider','Mounted Slave Raider','Slave Hunter','Industrial Slaver']:
        require('Slave Raider Doctrine' in units[name].get('promotions',[]),'Capture doctrine missing: '+name)
    for name in ['README.md','BUILD_STATUS.md']:
        text=(root/name).read_text(encoding='utf-8')
        require('**Predecessor:** **v0.2.6**' in text,'Wrong predecessor in '+name)
        require('v0.2.7' in text.splitlines()[0],'Wrong current version in '+name)
        require('`veilfall-v0.2.7-art-integration`' in text,'Wrong source branch in '+name)
        require('automated' in text and 'in-game' in text,'Acceptance distinction missing in '+name)
    workflow=(root/'.github/workflows/v021-art-build.yml').read_text(encoding='utf-8')
    require('Build and verify Veilfall v0.2.7 art' in workflow,'Wrong workflow release label')
    require('veilfall-v0.2.7-unit-scale' in workflow and 'veilfall-v0.2.7-art-integration' in workflow,'Wrong workflow branches')
    require('v0.2.6' not in workflow,'Stale workflow release label')
    regions,boxes=atlas_read(root);required=set(manifest['required_keys'])
    require(set(regions)==required and len(regions)==80,'Atlas keys missing/extra: '+str(sorted(required^set(regions))))
    for key,sha in manifest['preserved_regions'].items():
        require(digest(regions[key].tobytes())==sha,'Unrelated supplemental art changed: '+key)
    portraits={};icons={};sprites={}
    for name in UNITS:
        for prefix,kind,target in [('UnitPortraits','portrait',portraits),('UnitIcons','icon',icons)]:
            target[name]=image_metrics(regions[f'{prefix}/{name}'],kind,name)
        for ts in SETS:
            key=f'TileSets/{ts}/Units/{name}';m=image_metrics(regions[key],'sprite',name)
            if ts=='HexaRealm':sprites[name]=m
        require(regions[f'TileSets/FantasyHex/Units/{name}'].size==(32,28),'FantasyHex frame mismatch: '+name)
        expected_hr=(64,65) if name=='Mounted Slave Raider' else (64,56)
        require(regions[f'TileSets/HexaRealm/Units/{name}'].size==expected_hr,'HexaRealm frame mismatch: '+name)
        require(regions[f'TileSets/Minimal/Units/{name}'].size==expected_hr,'Minimal frame mismatch: '+name)
    new_keys=set(regions)-set(manifest['preserved_regions'])
    source_assets=make_assets()
    require(set(source_assets)==new_keys,'Generated source assets missing or extraneous')
    for key,src in source_assets.items():
        require(src.size==regions[key].size and src.tobytes()==regions[key].tobytes(),'Packed/source pixel mismatch: '+key)
    distinctness={}
    for kind,prefix,metrics in [('portraits','UnitPortraits',portraits),('icons','UnitIcons',icons),('sprites','TileSets/Minimal/Units',sprites)]:
        require(len({m['rgba_sha256'] for m in metrics.values()})==11,kind+' RGBA duplicates')
        require(len({m['normalized_alpha_sha256'] for m in metrics.values()})==11,kind+' normalized silhouette duplicates')
        pairs=[]
        for i,a in enumerate(UNITS):
            for b in UNITS[i+1:]:
                score=similarity(regions[f'{prefix}/{a}'],regions[f'{prefix}/{b}'])
                require(score<0.965,kind+' nearly recolor-equivalent: '+a+' / '+b);pairs.append((score,a,b))
        pair=max(pairs);slave=similarity(regions[f'{prefix}/Slave'],regions[f'{prefix}/Slave Raider'])
        require(slave<0.80,'Slave and Slave Raider too similar in '+kind)
        distinctness[kind]={'distinct_rgba_count':11,'distinct_normalized_silhouettes':11,'max_pair_iou':pair[0],'closest_pair':list(pair[1:]),'slave_raider_iou':slave}
    return {'release':'v0.2.7','predecessor':'v0.2.6','baseline_commit':BASELINE,
            'status':'automated_checks_passed','manual_in_game_acceptance':'pending',
            'entry_count':80,'replaced_region_count':55,'preserved_region_count':25,
            'required_keys':sorted(required),'missing_keys':[],
            'all_repository_json_valid':True,'gameplay_files_byte_identical':True,
            'legacy_art_byte_identical':True,'protected_file_count':len(manifest['unchanged_files']),
            'atlas_names':['game','v021'],'png_size':[2048,2048],
            'exact_capture_rule':RULE,'capture_chance_percent':50,
            'military_filter_unchanged_no_barbarian_exclusion_added':True,
            'distinct_unit_icon_count':11,'distinctness':distinctness,
            'portrait_metrics':portraits,'icon_metrics':icons,'map_sprite_metrics':sprites,
            'source_asset_count':55,'all_packed_regions_match_sources':True,
            'v021_png_sha256':digest((root/'v021.png').read_bytes()),
            'v021_atlas_sha256':digest((root/'v021.atlas').read_bytes()),
            'legacy_file_sha256':{k:v for k,v in manifest['unchanged_files'].items() if k.startswith('game')},
            'baseline_manifest_sha256':digest((root/'tools/v026/baseline_manifest.json').read_bytes())}

def build():
    old,_=atlas_read(ROOT);manifest=load_json(ROOT/'tools/v026/baseline_manifest.json')
    preserved={k:old[k] for k in manifest['preserved_regions']}
    for k,im in preserved.items():require(digest(im.tobytes())==manifest['preserved_regions'][k],'Pre-build preservation failed: '+k)
    new=make_assets();require(len(new)==55,'Wrong new asset count')
    for key,im in new.items():
        p=ROOT/'tools/v026/generated'/(key+'.png');p.parent.mkdir(parents=True,exist_ok=True);im.save(p,format='PNG',optimize=True)
    assets={**preserved,**new};page=Image.new('RGBA',(2048,2048),(0,0,0,0));positions={};x=y=2;row=0
    for key in sorted(assets,key=lambda k:(-assets[k].height,k)):
        im=assets[key];w,h=im.size
        if x+w+2>2048:x=2;y+=row+2;row=0
        require(y+h+2<=2048,'Atlas overflow')
        page.paste(im,(x,y));positions[key]=(x,y,w,h);x+=w+2;row=max(row,h)
    page.save(ROOT/'v021.png',format='PNG',optimize=True)
    lines=['v021.png','size: 2048, 2048','format: RGBA8888','filter: Nearest, Nearest','repeat: none']
    for key in sorted(positions):
        x,y,w,h=positions[key]
        lines += [key,'  rotate: false',f'  xy: {x}, {y}',f'  size: {w}, {h}',f'  orig: {w}, {h}','  offset: 0, 0','  index: -1']
    (ROOT/'v021.atlas').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    report=verify();(ROOT/'ART_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    if args.check:
        report=verify();require(report==load_json(ROOT/'ART_VERIFICATION.json'),'ART_VERIFICATION does not match deployed bytes')
    else:report=build()
    print(json.dumps({k:report[k] for k in ['release','status','entry_count','replaced_region_count','preserved_region_count','distinctness','gameplay_files_byte_identical','legacy_art_byte_identical','capture_chance_percent','v021_png_sha256']},indent=2))

if __name__=='__main__':main()
