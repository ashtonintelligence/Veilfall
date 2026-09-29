"""Build and verify Veilfall v0.2.8 dedicated map-sprite rebuild.

This patch preserves every v0.2.7 portrait/icon and every unrelated atlas region,
replacing only the 33 map-sprite regions for the eleven Marine/slavery-line units.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image
import argparse, hashlib, json, re, subprocess

ROOT=Path(__file__).resolve().parents[2]
BASELINE='183152c257d7e10fc1b4121059e4dfe6b3b7ff5f'
RELEASE='v0.2.8'
PREDECESSOR='v0.2.7'
RULE='Free [Slave] appears <upon defeating a [Military] unit> <with [50]% chance>'
UNITS=['Slave','Slave Raider','Mounted Slave Raider','Slave Hunter','Industrial Slaver',
       'Continental Marines','Marine Riflemen','Expeditionary Marines','Fleet Marine Force',
       'Marine Expeditionary Unit','Exo-Marine']
SETS=['Minimal','FantasyHex','HexaRealm']
SPRITE_PREFIXES=[f'TileSets/{ts}/Units' for ts in SETS]
REBUILT={f'{prefix}/{name}' for prefix in SPRITE_PREFIXES for name in UNITS}
SOURCE_DIR=ROOT/'tools/v028/sprite_sources'
GENERATED=ROOT/'tools/v028/generated'

def require(ok,msg):
    if not ok: raise ValueError(msg)

def digest(data): return hashlib.sha256(data).hexdigest()
def load_json(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def git_bytes(rel):
    return subprocess.check_output(['git','show',BASELINE+':'+rel],cwd=ROOT)

def baseline_files():
    return subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE],cwd=ROOT,text=True).splitlines()

def atlas_read_from_bytes(atlas_bytes,png_bytes):
    from io import BytesIO
    lines=atlas_bytes.decode('utf-8').splitlines()
    require(lines[:5]==['v021.png','size: 2048, 2048','format: RGBA8888','filter: Nearest, Nearest','repeat: none'],'Atlas header changed')
    image=Image.open(BytesIO(png_bytes)).convert('RGBA')
    require(image.size==(2048,2048),'Unexpected atlas dimensions')
    regions={}; boxes={}
    for i in range(5,len(lines),7):
        c=lines[i:i+7]; require(len(c)==7,'Incomplete atlas entry')
        key=c[0]; require(key not in regions,'Duplicate atlas key: '+key)
        m=re.fullmatch(r'  xy: (\d+), (\d+)',c[2]); s=re.fullmatch(r'  size: (\d+), (\d+)',c[3])
        require(m and s,'Malformed atlas entry: '+key)
        x,y=map(int,m.groups()); w,h=map(int,s.groups())
        require(c[1]=='  rotate: false' and c[4]==f'  orig: {w}, {h}' and c[5]=='  offset: 0, 0' and c[6]=='  index: -1','Unsupported atlas transform: '+key)
        for other,(ox,oy,ow,oh) in boxes.items():
            require(x+w<=ox or ox+ow<=x or y+h<=oy or oy+oh<=y,'Overlapping regions: '+key+' / '+other)
        boxes[key]=(x,y,w,h); regions[key]=image.crop((x,y,x+w,y+h))
    return regions,boxes

def atlas_read(root=ROOT):
    return atlas_read_from_bytes((Path(root)/'v021.atlas').read_bytes(),(Path(root)/'v021.png').read_bytes())

def baseline_regions():
    return atlas_read_from_bytes(git_bytes('v021.atlas'),git_bytes('v021.png'))[0]

def normalized_mask(im):
    a=im.getchannel('A').point(lambda v:255 if v>=128 else 0); box=a.getbbox()
    require(box is not None,'Empty alpha')
    return a.crop(box).resize((64,64),Image.Resampling.NEAREST)

def similarity(a,b):
    aa=normalized_mask(a).tobytes(); bb=normalized_mask(b).tobytes()
    common=sum(1 for x,y in zip(aa,bb) if x and y)
    union=sum(1 for x,y in zip(aa,bb) if x or y)
    return common/union if union else 1.0

def frame_for(name,tileset):
    mounted=name=='Mounted Slave Raider'
    if tileset=='FantasyHex':
        return (32,28),(30,26)
    if mounted:
        return (64,65),(62,63)
    return (64,56),(60,54)

def make_sprite(name,tileset):
    source=Image.open(SOURCE_DIR/(name+'.png')).convert('RGBA')
    box=source.getchannel('A').getbbox(); require(box is not None,'Empty source: '+name)
    crop=source.crop(box)
    frame,maxsize=frame_for(name,tileset)
    scale=min(maxsize[0]/crop.width,maxsize[1]/crop.height)
    wh=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)))
    # NEAREST preserves the purpose-built graphic edge language and avoids soft portrait-like resampling.
    crop=crop.resize(wh,Image.Resampling.NEAREST)
    out=Image.new('RGBA',frame,(0,0,0,0))
    x=(frame[0]-wh[0])//2
    y=frame[1]-wh[1]-1
    out.alpha_composite(crop,(x,y))
    out.putalpha(out.getchannel('A').point(lambda v:0 if v<24 else (255 if v>224 else v)))
    return out

def make_assets():
    assets={}
    for name in UNITS:
        for ts in SETS:
            assets[f'TileSets/{ts}/Units/{name}']=make_sprite(name,ts)
    return assets

def protected_baseline_check():
    allowed={
        'README.md','BUILD_STATUS.md','ART_VERIFICATION.json','v021.atlas','v021.png',
        'jsons/ModOptions.json','.github/workflows/v021-art-build.yml','tools/v021/build_assets.py'
    }
    for rel in baseline_files():
        if rel in allowed or rel.startswith('tools/v028/'): continue
        p=ROOT/rel
        require(p.is_file(),'Protected baseline file missing: '+rel)
        require(p.read_bytes()==git_bytes(rel),'Protected baseline file changed: '+rel)

def sprite_metrics(im,name,tileset):
    a=im.getchannel('A'); box=a.getbbox(); require(box,'Empty sprite: '+name)
    w=box[2]-box[0]; h=box[3]-box[1]
    frame,maxsize=frame_for(name,tileset)
    require(im.size==frame,'Wrong sprite frame: '+tileset+' / '+name)
    require(all(a.getpixel(pt)==0 for pt in [(0,0),(im.width-1,0),(0,im.height-1),(im.width-1,im.height-1)]),'Opaque sprite corner: '+name)
    require(box[3]>=im.height-2,'Sprite not bottom anchored: '+name)
    require(w>=8 and h>=18,'Sprite too small: '+name)
    require(w<=maxsize[0] and h<=maxsize[1],'Sprite exceeds intended footprint: '+name)
    coverage=sum(v>=128 for v in a.tobytes())/(im.width*im.height)
    require(coverage<0.75,'Sprite background-like coverage: '+name)
    return {'frame':list(im.size),'bbox':list(box),'w':w,'h':h,'coverage':round(coverage,6),'rgba_sha256':digest(im.tobytes())}

def verify():
    protected_baseline_check()
    for p in ROOT.rglob('*.json'):
        if '.git' not in p.parts: load_json(p)
    opts=load_json(ROOT/'jsons/ModOptions.json')
    require(opts.get('modVersion')=='0.2.8','Wrong modVersion')
    require(opts.get('lastUpdated')=='2026-09-28','Wrong lastUpdated')
    require(load_json(ROOT/'Atlases.json')==['game','v021'],'Atlases.json changed')
    promos=load_json(ROOT/'jsons/UnitPromotions.json')
    doctrine=next(p for p in promos if p['name']=='Slave Raider Doctrine')
    require(RULE in doctrine.get('uniques',[]),'Exact 50% Slave Raider rule missing')
    require(not any('[25]%' in s for s in doctrine.get('uniques',[])),'25% capture regression')
    units={u['name']:u for u in load_json(ROOT/'jsons/Units.json')}
    require(set(UNITS)<=set(units),'Case-sensitive unit name mismatch')

    current,_=atlas_read(ROOT); baseline=baseline_regions()
    require(set(current)==set(baseline) and len(current)==80,'Atlas key set changed')
    preserved=set(current)-REBUILT
    require(len(REBUILT)==33 and len(preserved)==47,'Unexpected rebuild/preservation counts')
    for key in preserved:
        require(current[key].size==baseline[key].size and current[key].tobytes()==baseline[key].tobytes(),'Preserved atlas region changed: '+key)

    source_hashes={}
    for name in UNITS:
        p=SOURCE_DIR/(name+'.png'); require(p.is_file(),'Missing sprite source: '+name)
        im=Image.open(p).convert('RGBA'); require(im.size==(64,64),'Canonical source must be 64x64: '+name)
        require(im.getchannel('A').getbbox() is not None,'Empty canonical source: '+name)
        source_hashes[name]=digest(p.read_bytes())

    metrics={}
    for name in UNITS:
        metrics[name]={}
        for ts in SETS:
            key=f'TileSets/{ts}/Units/{name}'
            metrics[name][ts]=sprite_metrics(current[key],name,ts)
            gp=GENERATED/ts/(name+'.png')
            require(gp.is_file(),'Missing generated sprite: '+key)
            gi=Image.open(gp).convert('RGBA')
            require(gi.size==current[key].size and gi.tobytes()==current[key].tobytes(),'Generated/packed sprite mismatch: '+key)

    for ts in SETS:
        hashes=[metrics[n][ts]['rgba_sha256'] for n in UNITS]
        require(len(set(hashes))==11,'Duplicate map sprites in '+ts)
        slave=current[f'TileSets/{ts}/Units/Slave']
        raider=current[f'TileSets/{ts}/Units/Slave Raider']
        require(similarity(slave,raider)<0.80,'Slave and Slave Raider too similar in '+ts)
        mounted=current[f'TileSets/{ts}/Units/Mounted Slave Raider']
        require(similarity(mounted,raider)<0.90,'Mounted Raider insufficiently distinct in '+ts)

    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    status=(ROOT/'BUILD_STATUS.md').read_text(encoding='utf-8')
    workflow=(ROOT/'.github/workflows/v021-art-build.yml').read_text(encoding='utf-8')
    require(readme.startswith('# Unciv: Veilfall v0.2.8'),'README version wrong')
    require('**Predecessor:** **v0.2.7**' in readme,'README predecessor wrong')
    require(status.startswith('# Veilfall v0.2.8'),'BUILD_STATUS version wrong')
    require('veilfall-v0.2.8-sprite-rebuild' in workflow and 'veilfall-v0.2.8-art-integration' in workflow,'Workflow branch names wrong')

    return {
        'release':RELEASE,'predecessor':PREDECESSOR,'baseline_commit':BASELINE,
        'status':'automated_checks_passed','manual_in_game_acceptance':'pending',
        'entry_count':80,'rebuilt_map_sprite_region_count':33,'preserved_region_count':47,
        'all_repository_json_valid':True,'gameplay_files_byte_identical':True,
        'legacy_art_byte_identical':True,'portraits_and_icons_preserved_from_v0.2.7':True,
        'atlas_names':['game','v021'],'exact_capture_rule':RULE,'capture_chance_percent':50,
        'military_filter_unchanged_no_barbarian_exclusion_added':True,
        'sprite_source_sha256':source_hashes,'map_sprite_metrics':metrics,
        'v021_png_sha256':digest((ROOT/'v021.png').read_bytes()),
        'v021_atlas_sha256':digest((ROOT/'v021.atlas').read_bytes()),
    }

def build():
    baseline=baseline_regions()
    assets={k:v for k,v in baseline.items() if k not in REBUILT}
    rebuilt=make_assets(); require(set(rebuilt)==REBUILT,'Wrong rebuilt key set')
    assets.update(rebuilt)
    GENERATED.mkdir(parents=True,exist_ok=True)
    for key,im in rebuilt.items():
        _,ts,_,name=key.split('/',3)
        p=GENERATED/ts/(name+'.png'); p.parent.mkdir(parents=True,exist_ok=True); im.save(p,optimize=True)

    page=Image.new('RGBA',(2048,2048),(0,0,0,0)); positions={}; x=y=2; row=0
    for key in sorted(assets,key=lambda k:(-assets[k].height,k)):
        im=assets[key]; w,h=im.size
        if x+w+2>2048: x=2; y+=row+2; row=0
        require(y+h+2<=2048,'Atlas overflow')
        page.paste(im,(x,y)); positions[key]=(x,y,w,h); x+=w+2; row=max(row,h)
    page.save(ROOT/'v021.png',optimize=True)
    lines=['v021.png','size: 2048, 2048','format: RGBA8888','filter: Nearest, Nearest','repeat: none']
    for key in sorted(positions):
        x,y,w,h=positions[key]
        lines += [key,'  rotate: false',f'  xy: {x}, {y}',f'  size: {w}, {h}',f'  orig: {w}, {h}','  offset: 0, 0','  index: -1']
    (ROOT/'v021.atlas').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    report=verify()
    (ROOT/'ART_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--check',action='store_true'); args=ap.parse_args()
    report=verify() if args.check else build()
    if args.check:
        require(report==load_json(ROOT/'ART_VERIFICATION.json'),'ART_VERIFICATION does not match deployed bytes')
    print(json.dumps({k:report[k] for k in ['release','status','entry_count','rebuilt_map_sprite_region_count','preserved_region_count','gameplay_files_byte_identical','legacy_art_byte_identical','capture_chance_percent','v021_png_sha256']},indent=2))

if __name__=='__main__': main()
