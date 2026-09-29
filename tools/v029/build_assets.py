"""Build and verify Veilfall v0.2.9 sprite/native-rendering and Rationalism city-icon correction.

v0.2.9 leaves the v0.2.8 supplemental atlas byte-identical and adds a new v029
atlas loaded after v021. The later atlas overrides only the eleven custom map-unit
sprites plus ReligionIcons/Rationalism. It also supplies AbsoluteUnits variants so
the default Unciv unit set no longer falls back to the 32x28 FantasyHex sprites.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import argparse, hashlib, io, json, math, re, subprocess, sys, urllib.request

ROOT = Path(__file__).resolve().parents[2]
GIT_ROOT = ROOT
BASELINE = 'a4cc93578b92a75844eafde6ff605b5303a61630'
RELEASE = 'v0.2.9'
PREDECESSOR = 'v0.2.8'
RULE = 'Free [Slave] appears <upon defeating a [Military] unit> <with [50]% chance>'
UNCIV_REF = 'eba5356202ea101c696f34be1cffee8373eb109a'
UNITS = [
    'Slave','Slave Raider','Mounted Slave Raider','Slave Hunter','Industrial Slaver',
    'Continental Marines','Marine Riflemen','Expeditionary Marines','Fleet Marine Force',
    'Marine Expeditionary Unit','Exo-Marine'
]
SETS = ['AbsoluteUnits','Minimal','FantasyHex','HexaRealm']
NATIVE_SETS = ['AbsoluteUnits','FantasyHex','HexaRealm']
REFERENCE_POOLS = {
    'Slave': ['Worker','Settler'],
    'Slave Raider': ['Warrior','Spearman','Swordsman'],
    'Mounted Slave Raider': ['Horseman','Cavalry'],
    'Slave Hunter': ['Musketman','Rifleman','Infantry'],
    'Industrial Slaver': ['Rifleman','Infantry','Marine'],
    'Continental Marines': ['Musketman','Rifleman','Marine'],
    'Marine Riflemen': ['Rifleman','Musketman','Infantry'],
    'Expeditionary Marines': ['Infantry','Marine','Paratrooper'],
    'Fleet Marine Force': ['Marine','Infantry','Paratrooper'],
    'Marine Expeditionary Unit': ['Marine','Paratrooper','Infantry'],
    'Exo-Marine': ['Paratrooper','Marine','Infantry'],
}
REF_DIR = ROOT/'tools/v029/native_reference'
GENERATED = ROOT/'tools/v029/generated'
PREVIEWS = ROOT/'tools/v029/previews'
MAP_KEYS = {f'TileSets/{ts}/Units/{name}' for ts in SETS for name in UNITS}
OVERRIDE_KEYS = MAP_KEYS | {'ReligionIcons/Rationalism'}

sys.path.insert(0, str(ROOT/'tools/v026'))
import artwork as highres_art  # noqa: E402


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def git_bytes(rel):
    return subprocess.check_output(['git','show',BASELINE+':'+rel], cwd=GIT_ROOT)


def baseline_files():
    return subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE], cwd=GIT_ROOT, text=True).splitlines()


def parse_atlas_bytes(atlas_bytes, png_bytes):
    lines = atlas_bytes.decode('utf-8').splitlines()
    require(len(lines) >= 5, 'Atlas too short')
    image = Image.open(io.BytesIO(png_bytes)).convert('RGBA')
    regions = {}
    boxes = {}
    i = 5
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        key = lines[i]
        require(i+6 < len(lines), 'Incomplete atlas entry: '+key)
        c = lines[i:i+7]
        m = re.fullmatch(r'  xy: (\d+), (\d+)', c[2])
        s = re.fullmatch(r'  size: (\d+), (\d+)', c[3])
        require(m and s, 'Malformed atlas entry: '+key)
        x,y = map(int,m.groups()); w,h = map(int,s.groups())
        require(c[1] == '  rotate: false', 'Rotated atlas region unsupported: '+key)
        require(key not in regions, 'Duplicate atlas key: '+key)
        boxes[key] = (x,y,w,h)
        regions[key] = image.crop((x,y,x+w,y+h))
        i += 7
    return regions, boxes, lines[:5]


def atlas_read(path_prefix):
    return parse_atlas_bytes((ROOT/(path_prefix+'.atlas')).read_bytes(), (ROOT/(path_prefix+'.png')).read_bytes())


def alpha_metrics(im):
    a = im.getchannel('A')
    box = a.getbbox()
    require(box is not None, 'Empty alpha image')
    total = 0
    sx = sy = 0.0
    opaque = soft = 0
    for y in range(im.height):
        for x in range(im.width):
            v = a.getpixel((x,y))
            if v:
                total += v; sx += x*v; sy += y*v
                if v == 255: opaque += 1
                else: soft += 1
    require(total > 0, 'Zero alpha mass')
    count = opaque + soft
    return {
        'frame': [im.width, im.height],
        'bbox': list(box),
        'bbox_w': box[2]-box[0],
        'bbox_h': box[3]-box[1],
        'centroid': [round(sx/total,4), round(sy/total,4)],
        'centroid_norm': [round((sx/total)/im.width,6), round((sy/total)/im.height,6)],
        'coverage': round(count/(im.width*im.height),6),
        'soft_alpha_fraction': round(soft/count,6),
    }


def download(url):
    req = urllib.request.Request(url, headers={'User-Agent':'Veilfall-v0.2.9-builder'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def _native_source_files():
    base = f'https://raw.githubusercontent.com/yairm210/Unciv/{UNCIV_REF}/android/assets/'
    return {
        'AbsoluteUnits': (base+'AbsoluteUnits.atlas', base+'AbsoluteUnits.png'),
        'Tilesets': (base+'Tilesets.atlas', base+'Tilesets.png'),
    }


def ensure_native_reference():
    """Vendor only the small native crops needed for deterministic comparison.

    If the crops already exist (as they do on the integration/main commit), no
    network access is used. The source branch's first build downloads pinned
    upstream atlas pages and commits only the selected native regions/manifest.
    """
    manifest_path = REF_DIR/'manifest.json'
    if manifest_path.is_file():
        manifest = load_json(manifest_path)
        if manifest.get('unciv_commit') == UNCIV_REF:
            expected = []
            for ts in NATIVE_SETS:
                for name in sorted({n for pool in REFERENCE_POOLS.values() for n in pool}):
                    expected.append(REF_DIR/ts/(name+'.png'))
            if all(p.is_file() for p in expected):
                return manifest

    REF_DIR.mkdir(parents=True, exist_ok=True)
    urls = _native_source_files()
    abs_atlas = download(urls['AbsoluteUnits'][0]); abs_png = download(urls['AbsoluteUnits'][1])
    tile_atlas = download(urls['Tilesets'][0]); tile_png = download(urls['Tilesets'][1])
    abs_regions,_,_ = parse_atlas_bytes(abs_atlas, abs_png)
    tile_regions,_,_ = parse_atlas_bytes(tile_atlas, tile_png)
    names = sorted({n for pool in REFERENCE_POOLS.values() for n in pool})
    manifest = {'unciv_commit':UNCIV_REF, 'sources':urls, 'sets':{}}
    for ts in NATIVE_SETS:
        manifest['sets'][ts] = {}
        for name in names:
            key = f'TileSets/{ts}/Units/{name}'
            regions = abs_regions if ts == 'AbsoluteUnits' else tile_regions
            require(key in regions, 'Pinned native reference missing: '+key)
            im = regions[key]
            p = REF_DIR/ts/(name+'.png'); p.parent.mkdir(parents=True,exist_ok=True)
            im.save(p,optimize=True)
            manifest['sets'][ts][name] = {'key':key,'metrics':alpha_metrics(im),'png_sha256':digest(p.read_bytes())}
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest


def native_set_for(ts):
    return 'HexaRealm' if ts == 'Minimal' else ts


def load_native(ts, name):
    return Image.open(REF_DIR/native_set_for(ts)/(name+'.png')).convert('RGBA')


def choose_reference(name, ts):
    candidates=[]
    for ref in REFERENCE_POOLS[name]:
        im=load_native(ts,ref); m=alpha_metrics(im)
        offset=abs(m['centroid_norm'][0]-0.5)
        candidates.append((offset,ref,im,m))
    candidates.sort(key=lambda v:(v[0],v[1]), reverse=True)
    return candidates[0][1], candidates[0][2], candidates[0][3]


def simplify_for_map(src, target_wh):
    """Reduce high-resolution illustration to crisp game-scale art."""
    w,h = target_wh
    resized = src.resize((max(1,w),max(1,h)), Image.Resampling.LANCZOS)
    resized = resized.filter(ImageFilter.UnsharpMask(radius=0.65, percent=180, threshold=2))
    alpha = resized.getchannel('A').point(lambda v: 0 if v < 96 else 255)
    rgb = resized.convert('RGB').quantize(colors=24, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')
    out = rgb.convert('RGBA'); out.putalpha(alpha)
    return out


def make_sprite(name, ts):
    ref_name, ref, refm = choose_reference(name, ts)
    frame = ref.size
    src = highres_art.ARTISTS[name]().convert('RGBA')
    box = src.getchannel('A').getbbox(); require(box is not None, 'Empty high-res source: '+name)
    crop = src.crop(box)

    target_h = min(frame[1]-2, max(18, refm['bbox_h']))
    scale = target_h/crop.height
    target_w = max(1, round(crop.width*scale))
    if target_w > frame[0]-2:
        scale = (frame[0]-2)/crop.width
        target_w = frame[0]-2
        target_h = max(1, round(crop.height*scale))
    fig = simplify_for_map(crop,(target_w,target_h))
    fm = alpha_metrics(fig)

    target_bottom = min(frame[1]-1, refm['bbox'][3])
    y = round(target_bottom - fm['bbox'][3])
    target_cx = refm['centroid'][0]
    x = round(target_cx - fm['centroid'][0])

    x = max(1-fm['bbox'][0], min(x, frame[0]-1-fm['bbox'][2]))
    y = max(1-fm['bbox'][1], min(y, frame[1]-1-fm['bbox'][3]))
    out = Image.new('RGBA', frame, (0,0,0,0)); out.alpha_composite(fig,(x,y))
    om = alpha_metrics(out)
    require(om['bbox'][3] >= frame[1]-3, 'Custom sprite not grounded: '+ts+' / '+name)
    require(om['soft_alpha_fraction'] == 0, 'Custom sprite has soft alpha halo: '+ts+' / '+name)
    return out, ref_name, refm, om


def rationalism_icon(size=128):
    """Tint-safe transparent city glyph; portrait remains in v021 unchanged."""
    scale=4; s=size*scale
    im=Image.new('RGBA',(s,s),(0,0,0,0)); d=ImageDraw.Draw(im)
    white=(255,255,255,255); cx=cy=s/2; r=s*0.31; width=max(8,round(s*0.085))
    box=(cx-r,cy-r,cx+r,cy+r)
    d.arc(box,28,202,fill=white,width=width)
    d.arc(box,208,382,fill=white,width=width)
    def head(angle):
        a=math.radians(angle); x=cx+math.cos(a)*r; y=cy+math.sin(a)*r
        ux,uy=math.cos(a),math.sin(a); px,py=-uy,ux; q=s*0.055
        return [(x+ux*q*1.2,y+uy*q*1.2),(x-px*q,y-py*q),(x+px*q,y+py*q)]
    d.polygon(head(28),fill=white); d.polygon(head(208),fill=white)
    pts=[]
    for i in range(16):
        a=-math.pi/2+i*math.pi/8; rr=s*(0.065 if i%2==0 else 0.025)
        pts.append((cx+rr*math.cos(a),cy+rr*math.sin(a)))
    d.polygon(pts,fill=white)
    im=im.resize((size,size),Image.Resampling.LANCZOS)
    return im


def make_assets():
    ensure_native_reference()
    assets={}; comparisons={}
    for name in UNITS:
        comparisons[name]={}
        for ts in SETS:
            im,ref_name,refm,om=make_sprite(name,ts)
            key=f'TileSets/{ts}/Units/{name}'
            assets[key]=im
            comparisons[name][ts]={'native_reference':ref_name,'native_metrics':refm,'custom_metrics':om}
    assets['ReligionIcons/Rationalism']=rationalism_icon(128)
    return assets,comparisons


def pack_assets(assets):
    size=1024
    page=Image.new('RGBA',(size,size),(0,0,0,0)); positions={}; x=y=2; row=0
    for key in sorted(assets,key=lambda k:(-assets[k].height,k)):
        im=assets[key]; w,h=im.size
        if x+w+2>size: x=2; y+=row+2; row=0
        require(y+h+2<=size,'v029 atlas overflow')
        page.alpha_composite(im,(x,y)); positions[key]=(x,y,w,h); x+=w+2; row=max(row,h)
    page.save(ROOT/'v029.png',optimize=True)
    lines=['v029.png',f'size: {size}, {size}','format: RGBA8888','filter: MipMapLinearLinear, MipMapLinearLinear','repeat: none']
    for key in sorted(positions):
        x,y,w,h=positions[key]
        lines += [key,'  rotate: false',f'  xy: {x}, {y}',f'  size: {w}, {h}',f'  orig: {w}, {h}','  offset: 0, 0','  index: -1']
    (ROOT/'v029.atlas').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def protected_baseline_check():
    allowed={
        'README.md','BUILD_STATUS.md','ART_VERIFICATION.json','Atlases.json','jsons/ModOptions.json',
        '.github/workflows/v021-art-build.yml'
    }
    for rel in baseline_files():
        if rel in allowed or rel.startswith('tools/v029/'):
            continue
        p=ROOT/rel
        require(p.is_file(),'Protected baseline file missing: '+rel)
        require(p.read_bytes()==git_bytes(rel),'Protected baseline file changed: '+rel)
    require((ROOT/'v021.png').read_bytes()==git_bytes('v021.png'),'v021.png changed')
    require((ROOT/'v021.atlas').read_bytes()==git_bytes('v021.atlas'),'v021.atlas changed')


def verify():
    protected_baseline_check()
    ensure_native_reference()
    for p in ROOT.rglob('*.json'):
        if '.git' not in p.parts: load_json(p)
    opts=load_json(ROOT/'jsons/ModOptions.json')
    require(opts.get('modVersion')=='0.2.9','Wrong modVersion')
    require(opts.get('lastUpdated')=='2026-09-28','Wrong lastUpdated')
    require(load_json(ROOT/'Atlases.json')==['game','v021','v029'],'Atlases.json must load v029 after v021')
    promos=load_json(ROOT/'jsons/UnitPromotions.json')
    doctrine=next(p for p in promos if p['name']=='Slave Raider Doctrine')
    require(RULE in doctrine.get('uniques',[]),'Exact 50% Slave Raider rule missing')
    require(not any('[25]%' in s for s in doctrine.get('uniques',[])),'25% capture regression')

    current,_,header=atlas_read('v029')
    require(header==['v029.png','size: 1024, 1024','format: RGBA8888','filter: MipMapLinearLinear, MipMapLinearLinear','repeat: none'],'v029 atlas filter/header mismatch')
    require(set(current)==OVERRIDE_KEYS and len(current)==45,'v029 override key set wrong')

    comparisons={}
    for name in UNITS:
        comparisons[name]={}
        for ts in SETS:
            key=f'TileSets/{ts}/Units/{name}'
            im=current[key]; m=alpha_metrics(im)
            ref_name,ref,refm=choose_reference(name,ts)
            require(im.size==ref.size,'Frame mismatch vs native reference: '+key)
            require(m['soft_alpha_fraction']==0,'Soft alpha halo: '+key)
            require(m['bbox'][3]>=im.height-3,'Sprite not grounded: '+key)
            require(abs(m['centroid'][0]-refm['centroid'][0])<=2.1,'Sprite lateral anchor differs from native reference: '+key)
            require(m['bbox_h']>=max(18,refm['bbox_h']-3),'Sprite too small vs native reference: '+key)
            gp=GENERATED/ts/(name+'.png')
            require(gp.is_file(),'Missing generated sprite: '+key)
            gi=Image.open(gp).convert('RGBA')
            require(gi.size==im.size and gi.tobytes()==im.tobytes(),'Generated/packed sprite mismatch: '+key)
            comparisons[name][ts]={'native_reference':ref_name,'native_metrics':refm,'custom_metrics':m}

    def normalized_mask(im):
        a=im.getchannel('A').point(lambda v:255 if v>=128 else 0); box=a.getbbox(); require(box,'Empty mask')
        return a.crop(box).resize((64,64),Image.Resampling.NEAREST)
    def similarity(a,b):
        aa=normalized_mask(a).tobytes(); bb=normalized_mask(b).tobytes()
        common=sum(1 for x,y in zip(aa,bb) if x and y); union=sum(1 for x,y in zip(aa,bb) if x or y)
        return common/union if union else 1.0
    for ts in SETS:
        hashes=[digest(current[f'TileSets/{ts}/Units/{n}'].tobytes()) for n in UNITS]
        require(len(set(hashes))==11,'Duplicate map sprites in '+ts)
        slave=current[f'TileSets/{ts}/Units/Slave']; raider=current[f'TileSets/{ts}/Units/Slave Raider']; mounted=current[f'TileSets/{ts}/Units/Mounted Slave Raider']
        require(similarity(slave,raider)<0.80,'Slave and Slave Raider too similar in '+ts)
        require(similarity(mounted,raider)<0.90,'Mounted Raider insufficiently distinct in '+ts)

    icon=current['ReligionIcons/Rationalism']; rm=alpha_metrics(icon)
    icon_file=GENERATED/'ReligionIcons'/'Rationalism.png'
    require(icon_file.is_file(),'Missing generated Rationalism city icon')
    icon_generated=Image.open(icon_file).convert('RGBA')
    require(icon_generated.size==icon.size and icon_generated.tobytes()==icon.tobytes(),'Generated/packed Rationalism icon mismatch')
    require(icon.size==(128,128),'Rationalism icon wrong size')
    require(rm['coverage']<0.34,'Rationalism icon is too filled / disc-like')
    corners=[(0,0),(127,0),(0,127),(127,127)]
    require(all(icon.getpixel(p)[3]==0 for p in corners),'Rationalism icon corners must be transparent')
    alpha=icon.getchannel('A')
    transparent_inside=sum(1 for y in range(28,100) for x in range(28,100) if alpha.getpixel((x,y))<16)
    require(transparent_inside>1800,'Rationalism icon lacks transparent internal negative space')

    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    status=(ROOT/'BUILD_STATUS.md').read_text(encoding='utf-8')
    workflow=(ROOT/'.github/workflows/v021-art-build.yml').read_text(encoding='utf-8')
    require(readme.startswith('# Unciv: Veilfall v0.2.9'),'README version wrong')
    require('**Predecessor:** **v0.2.8**' in readme[:500],'README predecessor wrong')
    require(status.startswith('# Veilfall v0.2.9'),'BUILD_STATUS version wrong')
    require('veilfall-v0.2.9-sprite-rationalism-fix' in workflow and 'veilfall-v0.2.9-art-integration' in workflow,'Workflow branch names wrong')

    return {
        'release':RELEASE,'predecessor':PREDECESSOR,'baseline_commit':BASELINE,
        'status':'automated_checks_passed','manual_in_game_acceptance':'pending',
        'unciv_native_reference_commit':UNCIV_REF,
        'override_atlas':'v029','override_region_count':45,'map_sprite_region_count':44,
        'absolute_units_runtime_variants_added':True,
        'v021_byte_identical':True,'gameplay_files_byte_identical':True,'portraits_and_unit_icons_preserved':True,
        'atlas_names':['game','v021','v029'],'exact_capture_rule':RULE,'capture_chance_percent':50,
        'military_filter_unchanged_no_barbarian_exclusion_added':True,
        'native_comparisons':comparisons,
        'rationalism_city_icon':{'transparent_tint_safe':True,'metrics':rm,'portrait_preserved_in_v021':True},
        'v029_png_sha256':digest((ROOT/'v029.png').read_bytes()),
        'v029_atlas_sha256':digest((ROOT/'v029.atlas').read_bytes()),
        'v021_png_sha256':digest((ROOT/'v021.png').read_bytes()),
        'v021_atlas_sha256':digest((ROOT/'v021.atlas').read_bytes()),
    }


def build():
    assets,comparisons=make_assets()
    GENERATED.mkdir(parents=True,exist_ok=True)
    for key,im in assets.items():
        if key.startswith('TileSets/'):
            _,ts,_,name=key.split('/',3)
            p=GENERATED/ts/(name+'.png'); p.parent.mkdir(parents=True,exist_ok=True); im.save(p,optimize=True)
        else:
            p=GENERATED/'ReligionIcons'/'Rationalism.png'; p.parent.mkdir(parents=True,exist_ok=True); im.save(p,optimize=True)
    pack_assets(assets)
    report=verify()
    (ROOT/'ART_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--check',action='store_true'); args=ap.parse_args()
    report=verify() if args.check else build()
    if args.check:
        require(report==load_json(ROOT/'ART_VERIFICATION.json'),'ART_VERIFICATION does not match deployed bytes')
    print(json.dumps({k:report[k] for k in ['release','status','override_region_count','map_sprite_region_count','absolute_units_runtime_variants_added','v021_byte_identical','capture_chance_percent','v029_png_sha256']},indent=2))

if __name__=='__main__':
    main()
