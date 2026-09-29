"""Build and verify Veilfall v0.2.9 corrective release.

v0.2.9 preserves v0.2.8 portraits/icons and unrelated artwork while correcting:
- native-derived lateral map-sprite anchoring and crisp pixel treatment,
- the Rationalism city-map icon's opaque filled-disc behavior,
- Marine capture of adjacent embarked civilian units via a narrowly scoped Unciv workaround.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from collections import Counter
from io import BytesIO
from urllib.request import Request, urlopen
from PIL import Image
import argparse, hashlib, json, math, re, subprocess

ROOT=Path(__file__).resolve().parents[2]
GIT_ROOT=ROOT
BASELINE='a4cc93578b92a75844eafde6ff605b5303a61630'
RELEASE='v0.2.9'
PREDECESSOR='v0.2.8'
UNCIV_REF='eba5356202ea101c696f34be1cffee8373eb109a'
UNCIV_BASE=f'https://raw.githubusercontent.com/yairm210/Unciv/{UNCIV_REF}/android/assets'
RULE='Free [Slave] appears <upon defeating a [Military] unit> <with [50]% chance>'
MARINE_CAPTURE_WORKAROUND='May travel on Water tiles without embarking <when adjacent to a [Civilian] unit>'
UNITS=['Slave','Slave Raider','Mounted Slave Raider','Slave Hunter','Industrial Slaver',
       'Continental Marines','Marine Riflemen','Expeditionary Marines','Fleet Marine Force',
       'Marine Expeditionary Unit','Exo-Marine']
SETS=['Minimal','FantasyHex','HexaRealm']
SPRITE_PREFIXES=[f'TileSets/{ts}/Units' for ts in SETS]
MAP_REBUILT={f'{prefix}/{name}' for prefix in SPRITE_PREFIXES for name in UNITS}
RELIGION_KEY='ReligionIcons/Rationalism'
CHANGED_KEYS=MAP_REBUILT|{RELIGION_KEY}
SOURCE_DIR=ROOT/'tools/v028/sprite_sources'
GENERATED=ROOT/'tools/v029/generated'

REFERENCE_CANDIDATES={
    'Slave':['Worker','Settler','Great Prophet'],
    'Slave Raider':['Warrior','Swordsman','Spearman'],
    'Mounted Slave Raider':['Cavalry','Horseman','Knight'],
    'Slave Hunter':['Rifleman','Infantry','Marine'],
    'Industrial Slaver':['Infantry','Marine','Mechanized Infantry'],
    'Continental Marines':['Musketman','Rifleman','Marine','Infantry'],
    'Marine Riflemen':['Rifleman','Marine','Infantry','Musketman'],
    'Expeditionary Marines':['Infantry','Marine','Rifleman'],
    'Fleet Marine Force':['Marine','Infantry','Mechanized Infantry'],
    'Marine Expeditionary Unit':['Marine','Mechanized Infantry','Infantry'],
    'Exo-Marine':['Mechanized Infantry','Marine','Infantry'],
}

def require(ok,msg):
    if not ok: raise ValueError(msg)

def digest(data): return hashlib.sha256(data).hexdigest()
def load_json(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def git_bytes(rel):
    return subprocess.check_output(['git','show',BASELINE+':'+rel],cwd=GIT_ROOT)

def baseline_files():
    return subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE],cwd=GIT_ROOT,text=True).splitlines()

def parse_atlas(atlas_bytes,png_bytes,expected_page=None):
    lines=atlas_bytes.decode('utf-8').splitlines()
    if lines and lines[0]=='':
        lines=lines[1:]
    require(len(lines)>=5,'Atlas header missing')
    if expected_page:
        require(lines[0]==expected_page,'Unexpected atlas page')
    image=Image.open(BytesIO(png_bytes)).convert('RGBA')
    msize=re.fullmatch(r'size: (\d+), (\d+)',lines[1])
    require(msize,'Malformed atlas size')
    require(image.size==tuple(map(int,msize.groups())),'Atlas PNG dimensions mismatch')
    regions={}; boxes={}
    i=5
    while i < len(lines):
        c=lines[i:i+7]
        require(len(c)==7,'Incomplete atlas entry')
        key=c[0]
        require(key and key not in regions,'Duplicate/empty atlas key: '+key)
        m=re.fullmatch(r'  xy: (\d+), (\d+)',c[2]); s=re.fullmatch(r'  size: (\d+), (\d+)',c[3])
        require(m and s,'Malformed atlas entry: '+key)
        x,y=map(int,m.groups()); w,h=map(int,s.groups())
        require(c[1]=='  rotate: false','Rotated atlas entries unsupported: '+key)
        boxes[key]=(x,y,w,h)
        regions[key]=image.crop((x,y,x+w,y+h))
        i+=7
    return regions,boxes

def atlas_read(root=ROOT):
    return parse_atlas((Path(root)/'v021.atlas').read_bytes(),(Path(root)/'v021.png').read_bytes(),'v021.png')

def baseline_regions():
    return parse_atlas(git_bytes('v021.atlas'),git_bytes('v021.png'),'v021.png')[0]

def fetch_url(url):
    req=Request(url,headers={'User-Agent':'Veilfall-v0.2.9-builder'})
    with urlopen(req,timeout=45) as r:
        return r.read()

_NATIVE_CACHE=None
def native_regions():
    global _NATIVE_CACHE
    if _NATIVE_CACHE is None:
        atlas=fetch_url(UNCIV_BASE+'/Tilesets.atlas')
        png=fetch_url(UNCIV_BASE+'/Tilesets.png')
        regions,_=parse_atlas(atlas,png,'Tilesets.png')
        _NATIVE_CACHE=regions
    return _NATIVE_CACHE

def alpha_stats(im):
    a=im.getchannel('A')
    box=a.getbbox()
    require(box is not None,'Empty alpha')
    pts=[]
    soft=0; nz=0
    raw=list(a.getdata())
    for y in range(im.height):
        for x in range(im.width):
            v=raw[y*im.width+x]
            if v:
                nz+=1
                if v not in (0,255): soft+=1
            if v>=128:
                pts.append((x+0.5,y+0.5))
    require(pts,'No readable alpha')
    cx=sum(x for x,_ in pts)/len(pts)
    cy=sum(y for _,y in pts)/len(pts)
    return {
        'bbox':box,
        'w':box[2]-box[0],
        'h':box[3]-box[1],
        'centroid_x':cx,
        'centroid_y':cy,
        'center_delta_x':cx-im.width/2,
        'soft_alpha_ratio':soft/nz if nz else 0.0,
    }

def ref_tileset(ts):
    # Upstream Minimal has no native combat-unit sprites; HexaRealm is the native-sized fallback reference.
    return 'HexaRealm' if ts=='Minimal' else ts

def choose_native_reference(name,ts):
    regions=native_regions(); rts=ref_tileset(ts)
    options=[]
    for order,candidate in enumerate(REFERENCE_CANDIDATES[name]):
        key=f'TileSets/{rts}/Units/{candidate}'
        if key not in regions: continue
        im=regions[key]
        st=alpha_stats(im)
        # Prefer a clearly offset native example; preserve listed semantic preference as tie-break.
        score=(abs(st['center_delta_x']),-order)
        options.append((score,candidate,im,st,key))
    require(options,'No native reference for '+ts+' / '+name)
    options.sort(key=lambda x:x[0],reverse=True)
    _,candidate,im,st,key=options[0]
    min_offset=max(0.70,im.width*0.018)
    require(abs(st['center_delta_x'])>=min_offset,
            f'Native reference insufficiently off-center: {ts} / {name} / {candidate} ({st["center_delta_x"]:.3f})')
    return candidate,im,st,key

def normalized_mask(im):
    a=im.getchannel('A').point(lambda v:255 if v>=128 else 0); box=a.getbbox()
    require(box is not None,'Empty alpha')
    return a.crop(box).resize((64,64),Image.Resampling.NEAREST)

def similarity(a,b):
    aa=normalized_mask(a).tobytes(); bb=normalized_mask(b).tobytes()
    common=sum(1 for x,y in zip(aa,bb) if x and y)
    union=sum(1 for x,y in zip(aa,bb) if x or y)
    return common/union if union else 1.0

def make_sprite(name,ts):
    source=Image.open(SOURCE_DIR/(name+'.png')).convert('RGBA')
    sbox=source.getchannel('A').getbbox(); require(sbox is not None,'Empty source: '+name)
    crop=source.crop(sbox)
    ref_name,ref,refst,_=choose_native_reference(name,ts)
    frame=ref.size
    target_h=refst['h']
    scale=min(target_h/crop.height,(frame[0]-2)/crop.width,(frame[1]-2)/crop.height)
    wh=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)))
    crop=crop.resize(wh,Image.Resampling.NEAREST)
    # Fully quantize alpha after nearest-neighbor scaling: no interpolation halo survives.
    crop.putalpha(crop.getchannel('A').point(lambda v:255 if v>=96 else 0))
    cst=alpha_stats(crop)
    x=round(refst['centroid_x']-cst['centroid_x'])
    y=round(refst['bbox'][3]-cst['bbox'][3])
    x=max(0,min(frame[0]-crop.width,x))
    y=max(0,min(frame[1]-crop.height,y))
    out=Image.new('RGBA',frame,(0,0,0,0))
    out.alpha_composite(crop,(x,y))
    # Integer placement cannot always reproduce a fractional native centroid exactly.
    # Nudge one pixel toward the native centroid when that improves the match and remains in frame.
    st=alpha_stats(out)
    if abs(st['center_delta_x']-refst['center_delta_x'])>0.9:
        step=1 if st['center_delta_x']<refst['center_delta_x'] else -1
        nx=x+step
        if 0<=nx<=frame[0]-crop.width:
            candidate=Image.new('RGBA',frame,(0,0,0,0)); candidate.alpha_composite(crop,(nx,y))
            if abs(alpha_stats(candidate)['center_delta_x']-refst['center_delta_x']) < abs(st['center_delta_x']-refst['center_delta_x']):
                out=candidate
    return out

def make_rationalism_city_icon(base):
    """Turn the full-color opaque badge into a tint-safe transparent line/emblem mask."""
    im=base.convert('RGBA')
    opaque=[px[:3] for px in im.getdata() if px[3]>=200]
    require(opaque,'Rationalism icon unexpectedly empty')
    bg=Counter(opaque).most_common(1)[0][0]
    out=Image.new('RGBA',im.size,(255,255,255,0))
    src=list(im.getdata()); dst=[]
    for r,g,b,a in src:
        d=math.sqrt((r-bg[0])**2+(g-bg[1])**2+(b-bg[2])**2)
        keep=a>=48 and d>=34
        dst.append((255,255,255,255 if keep else 0))
    out.putdata(dst)
    # Ensure the city icon is never a solid badge: center/background must remain transparent.
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
        'jsons/ModOptions.json','jsons/UnitPromotions.json',
        '.github/workflows/v021-art-build.yml','tools/v021/build_assets.py',
        'tools/v029/build_assets.py','tools/v029/preview_assets.py','tools/v029/test_verification.py',
        'tools/v029/test_results.json'
    }
    for rel in baseline_files():
        if rel in allowed: continue
        p=ROOT/rel
        require(p.is_file(),'Protected baseline file missing: '+rel)
        require(p.read_bytes()==git_bytes(rel),'Protected baseline file changed: '+rel)

def sprite_metrics(im,name,ts):
    a=im.getchannel('A'); box=a.getbbox(); require(box,'Empty sprite: '+name)
    ref_name,ref,refst,refkey=choose_native_reference(name,ts)
    st=alpha_stats(im)
    require(im.size==ref.size,'Wrong native-derived sprite frame: '+ts+' / '+name)
    require(all(a.getpixel(pt)==0 for pt in [(0,0),(im.width-1,0),(0,im.height-1),(im.width-1,im.height-1)]),
            'Opaque sprite corner: '+name)
    require(abs(box[3]-refst['bbox'][3])<=1,'Sprite baseline not native-aligned: '+ts+' / '+name)
    tol=1.35 if im.width<=32 else 1.8
    require(st['center_delta_x']*refst['center_delta_x']>0,
            'Sprite lateral offset is on the wrong side of native reference: '+ts+' / '+name)
    require(abs(st['center_delta_x'])>=max(0.65,im.width*0.015),
            'Sprite still visually centered: '+ts+' / '+name)
    require(abs(st['center_delta_x'])>=abs(refst['center_delta_x'])*0.45,
            'Sprite lateral offset is too weak relative to native reference: '+ts+' / '+name)
    require(0.84<=st['h']/refst['h']<=1.16,'Sprite perceived height not native-comparable: '+ts+' / '+name)
    require(st['soft_alpha_ratio']==0.0,'Interpolation softness detected: '+ts+' / '+name)
    coverage=sum(v>=128 for v in a.getdata())/(im.width*im.height)
    require(coverage<0.72,'Sprite background-like coverage: '+name)
    return {
        'frame':list(im.size),'bbox':list(box),'w':st['w'],'h':st['h'],
        'coverage':round(coverage,6),'center_delta_x':round(st['center_delta_x'],3),
        'soft_alpha_ratio':round(st['soft_alpha_ratio'],6),
        'native_reference':ref_name,'native_reference_key':refkey,
        'native_bbox':list(refst['bbox']),
        'native_center_delta_x':round(refst['center_delta_x'],3),
        'rgba_sha256':digest(im.tobytes())
    }

def verify_rationalism_icon(im):
    a=im.getchannel('A'); box=a.getbbox(); require(box,'Rationalism city icon empty')
    require(all(a.getpixel(pt)==0 for pt in [(0,0),(127,0),(0,127),(127,127)]),
            'Rationalism icon corners not transparent')
    for pt in [(64,64),(60,64),(68,64),(64,60),(64,68)]:
        require(a.getpixel(pt)==0,'Rationalism icon center not transparent')
    coverage=sum(v>=128 for v in a.getdata())/(im.width*im.height)
    require(0.03<coverage<0.45,'Rationalism icon opacity coverage invalid')
    return {'bbox':list(box),'coverage':round(coverage,6),'center_alpha':a.getpixel((64,64)),
            'rgba_sha256':digest(im.tobytes())}

def verify():
    protected_baseline_check()
    for p in ROOT.rglob('*.json'):
        if '.git' not in p.parts: load_json(p)
    opts=load_json(ROOT/'jsons/ModOptions.json')
    require(opts.get('modVersion')=='0.2.9','Wrong modVersion')
    require(opts.get('lastUpdated')=='2026-09-28','Wrong lastUpdated')
    require(load_json(ROOT/'Atlases.json')==['game','v021'],'Atlases.json changed')

    promos=load_json(ROOT/'jsons/UnitPromotions.json')
    doctrine=next(p for p in promos if p['name']=='Slave Raider Doctrine')
    require(RULE in doctrine.get('uniques',[]),'Exact 50% Slave Raider rule missing')
    require(not any('[25]%' in s for s in doctrine.get('uniques',[])),'25% capture regression')
    marine=next(p for p in promos if p['name']=='Marine Naval Integration')
    mus=marine.get('uniques',[])
    require('May attack when embarked' in mus,'Marine embarked attack unique missing')
    require(MARINE_CAPTURE_WORKAROUND in mus,'Marine civilian-at-sea capture workaround missing')
    require('May travel on Water tiles without embarking' not in mus,
            'Marine water-travel workaround became unconditional')

    current,_=atlas_read(ROOT); baseline=baseline_regions()
    require(set(current)==set(baseline) and len(current)==80,'Atlas key set changed')
    preserved=set(current)-CHANGED_KEYS
    require(len(MAP_REBUILT)==33 and len(CHANGED_KEYS)==34 and len(preserved)==46,
            'Unexpected changed/preserved counts')
    for key in preserved:
        require(current[key].size==baseline[key].size and current[key].tobytes()==baseline[key].tobytes(),
                'Preserved atlas region changed: '+key)

    source_hashes={}
    for name in UNITS:
        p=SOURCE_DIR/(name+'.png'); require(p.is_file(),'Missing sprite source: '+name)
        im=Image.open(p).convert('RGBA'); require(im.size==(64,64),'Canonical source must be 64x64: '+name)
        source_hashes[name]=digest(p.read_bytes())

    metrics={}; native_refs={}
    for name in UNITS:
        metrics[name]={}; native_refs[name]={}
        for ts in SETS:
            key=f'TileSets/{ts}/Units/{name}'
            expected=make_sprite(name,ts)
            require(current[key].size==expected.size and current[key].tobytes()==expected.tobytes(),
                    'Packed sprite differs from native-derived build: '+key)
            metrics[name][ts]=sprite_metrics(current[key],name,ts)
            native_refs[name][ts]=metrics[name][ts]['native_reference']
            gp=GENERATED/ts/(name+'.png')
            require(gp.is_file(),'Missing generated sprite: '+key)
            gi=Image.open(gp).convert('RGBA')
            require(gi.size==current[key].size and gi.tobytes()==current[key].tobytes(),
                    'Generated/packed sprite mismatch: '+key)

    for ts in SETS:
        hashes=[metrics[n][ts]['rgba_sha256'] for n in UNITS]
        require(len(set(hashes))==11,'Duplicate map sprites in '+ts)
        slave=current[f'TileSets/{ts}/Units/Slave']
        raider=current[f'TileSets/{ts}/Units/Slave Raider']
        require(similarity(slave,raider)<0.80,'Slave and Slave Raider too similar in '+ts)
        mounted=current[f'TileSets/{ts}/Units/Mounted Slave Raider']
        require(similarity(mounted,raider)<0.90,'Mounted Raider insufficiently distinct in '+ts)

    expected_icon=make_rationalism_city_icon(baseline[RELIGION_KEY])
    require(current[RELIGION_KEY].tobytes()==expected_icon.tobytes(),
            'Packed Rationalism city icon differs from corrective mask')
    religion=verify_rationalism_icon(current[RELIGION_KEY])

    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    status=(ROOT/'BUILD_STATUS.md').read_text(encoding='utf-8')
    workflow=(ROOT/'.github/workflows/v021-art-build.yml').read_text(encoding='utf-8')
    require(readme.startswith('# Unciv: Veilfall v0.2.9'),'README version wrong')
    require('**Predecessor:** **v0.2.8**' in readme,'README predecessor wrong')
    require(status.startswith('# Veilfall v0.2.9'),'BUILD_STATUS version wrong')
    require('veilfall-v0.2.9-corrective' in workflow and 'veilfall-v0.2.9-art-integration' in workflow,
            'Workflow branch names wrong')

    return {
        'release':RELEASE,'predecessor':PREDECESSOR,'baseline_commit':BASELINE,
        'status':'automated_checks_passed','manual_in_game_acceptance':'pending',
        'entry_count':80,'rebuilt_map_sprite_region_count':33,'corrected_religion_icon_region_count':1,
        'changed_region_count':34,'preserved_region_count':46,
        'all_repository_json_valid':True,'legacy_art_byte_identical':True,
        'portraits_and_unit_icons_preserved_from_v0.2.8':True,
        'atlas_names':['game','v021'],'exact_capture_rule':RULE,'capture_chance_percent':50,
        'military_filter_unchanged_no_barbarian_exclusion_added':True,
        'marine_capture_workaround':MARINE_CAPTURE_WORKAROUND,
        'native_reference_repo':'yairm210/Unciv','native_reference_commit':UNCIV_REF,
        'native_reference_selection':native_refs,
        'sprite_source_sha256':source_hashes,'map_sprite_metrics':metrics,
        'rationalism_city_icon':religion,
        'v021_png_sha256':digest((ROOT/'v021.png').read_bytes()),
        'v021_atlas_sha256':digest((ROOT/'v021.atlas').read_bytes()),
    }

def build():
    baseline=baseline_regions()
    assets={k:v for k,v in baseline.items() if k not in CHANGED_KEYS}
    rebuilt=make_assets(); require(set(rebuilt)==MAP_REBUILT,'Wrong rebuilt key set')
    assets.update(rebuilt)
    assets[RELIGION_KEY]=make_rationalism_city_icon(baseline[RELIGION_KEY])
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
        lines += [key,'  rotate: false',f'  xy: {x}, {y}',f'  size: {w}, {h}',
                  f'  orig: {w}, {h}','  offset: 0, 0','  index: -1']
    (ROOT/'v021.atlas').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    report=verify()
    (ROOT/'ART_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--check',action='store_true'); args=ap.parse_args()
    report=verify() if args.check else build()
    if args.check:
        require(report==load_json(ROOT/'ART_VERIFICATION.json'),'ART_VERIFICATION does not match deployed bytes')
    print(json.dumps({k:report[k] for k in [
        'release','status','entry_count','rebuilt_map_sprite_region_count',
        'corrected_religion_icon_region_count','preserved_region_count',
        'capture_chance_percent','marine_capture_workaround','v021_png_sha256'
    ]},indent=2))

if __name__=='__main__': main()
