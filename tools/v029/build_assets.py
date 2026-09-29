"""Build and verify Veilfall v0.2.9 runtime-art corrective patch.

v0.2.9 fixes three runtime-art issues without altering gameplay rules:
1) adds custom AbsoluteUnits map sprites at native-comparable frames;
2) anchors custom sprites laterally using measured, pinned native AbsoluteUnits examples;
3) replaces the opaque Rationalism city icon with a transparent tint-safe glyph.

The Continental Marine civilian-capture report is verified separately as an Unciv
engine behavior: embarked land units cannot capture civilians on water. This
builder therefore does not silently change Marine gameplay semantics.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import argparse, hashlib, json, re, subprocess, statistics

ROOT=Path(__file__).resolve().parents[2]
GIT_ROOT=ROOT
BASELINE='a4cc93578b92a75844eafde6ff605b5303a61630'
RELEASE='v0.2.9'
PREDECESSOR='v0.2.8'
RULE='Free [Slave] appears <upon defeating a [Military] unit> <with [50]% chance>'
UNITS=['Slave','Slave Raider','Mounted Slave Raider','Slave Hunter','Industrial Slaver',
       'Continental Marines','Marine Riflemen','Expeditionary Marines','Fleet Marine Force',
       'Marine Expeditionary Unit','Exo-Marine']
SETS=['Minimal','FantasyHex','HexaRealm','AbsoluteUnits']
LEGACY_SETS=['Minimal','FantasyHex','HexaRealm']
SPRITE_PREFIXES=[f'TileSets/{ts}/Units' for ts in SETS]
REBUILT={f'{prefix}/{name}' for prefix in SPRITE_PREFIXES for name in UNITS}
EXISTING_REBUILT={f'TileSets/{ts}/Units/{name}' for ts in LEGACY_SETS for name in UNITS}
RELIGION_ICON='ReligionIcons/Rationalism'
SOURCE_DIR=ROOT/'tools/v028/sprite_sources'
GENERATED=ROOT/'tools/v029/generated'
PREVIEWS=ROOT/'tools/v029/previews'

NATIVE_COMMIT='eba5356202ea101c696f34be1cffee8373eb109a'
NATIVE_BASE=f'https://raw.githubusercontent.com/yairm210/Unciv/{NATIVE_COMMIT}/android/assets'
NATIVE_ATLAS_URL=NATIVE_BASE+'/AbsoluteUnits.atlas'
NATIVE_PNG_URL=NATIVE_BASE+'/AbsoluteUnits.png'
INFANTRY_CANDIDATES=['Warrior','Spearman','Swordsman','Musketman','Rifleman','Infantry','Marine','Paratrooper']
MOUNTED_CANDIDATES=['Horseman','Cavalry']
UNIT_CLASS={name:('mounted' if name=='Mounted Slave Raider' else 'infantry') for name in UNITS}

def require(ok,msg):
    if not ok: raise ValueError(msg)

def digest(data): return hashlib.sha256(data).hexdigest()
def load_json(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def git_bytes(rel):
    return subprocess.check_output(['git','show',BASELINE+':'+rel],cwd=GIT_ROOT)

def baseline_files():
    return subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE],cwd=GIT_ROOT,text=True).splitlines()

def atlas_read_from_bytes(atlas_bytes,png_bytes,expected_name=None):
    lines=atlas_bytes.decode('utf-8').splitlines()
    require(len(lines)>=5,'Atlas too short')
    if expected_name: require(lines[0]==expected_name,'Unexpected atlas PNG name')
    image=Image.open(BytesIO(png_bytes)).convert('RGBA')
    regions={}; boxes={}
    i=5
    while i < len(lines):
        c=lines[i:i+7]; require(len(c)==7,'Incomplete atlas entry')
        key=c[0]
        m=re.fullmatch(r'  xy: (\d+), (\d+)',c[2]); s=re.fullmatch(r'  size: (\d+), (\d+)',c[3])
        require(m and s,'Malformed atlas entry: '+key)
        x,y=map(int,m.groups()); w,h=map(int,s.groups())
        regions[key]=image.crop((x,y,x+w,y+h)); boxes[key]=(x,y,w,h)
        i+=7
    return regions,boxes

def atlas_read(root=ROOT):
    return atlas_read_from_bytes((Path(root)/'v021.atlas').read_bytes(),(Path(root)/'v021.png').read_bytes(),'v021.png')

def baseline_regions():
    return atlas_read_from_bytes(git_bytes('v021.atlas'),git_bytes('v021.png'),'v021.png')[0]

def alpha_stats(im):
    a=im.getchannel('A'); box=a.getbbox(); require(box is not None,'Empty alpha')
    pts=[]; total=0.0; sx=0.0; sy=0.0
    for y in range(im.height):
        for x in range(im.width):
            v=a.getpixel((x,y))
            if v:
                w=v/255.0; total+=w; sx+=(x+0.5)*w; sy+=(y+0.5)*w
    require(total>0,'Empty alpha weight')
    return {'bbox':box,'cx':sx/total,'cy':sy/total,'cx_ratio':(sx/total)/im.width,'cy_ratio':(sy/total)/im.height}

def fetch_native():
    atlas=urlopen(NATIVE_ATLAS_URL,timeout=30).read()
    png=urlopen(NATIVE_PNG_URL,timeout=30).read()
    regions,_=atlas_read_from_bytes(atlas,png,'AbsoluteUnits.png')
    return regions, digest(atlas), digest(png)

def choose_native_anchors(regions):
    def choose(names):
        rows=[]
        for name in names:
            key='TileSets/AbsoluteUnits/Units/'+name
            require(key in regions,'Pinned native reference missing: '+name)
            im=regions[key]; st=alpha_stats(im)
            rows.append((abs(st['cx_ratio']-.5),name,im,st))
        rows.sort(reverse=True,key=lambda r:r[0])
        # Choose a clearly off-center native example rather than averaging opposite offsets away.
        return rows[0]
    inf=choose(INFANTRY_CANDIDATES)
    mnt=choose(MOUNTED_CANDIDATES)
    return {
        'infantry': {'name':inf[1],'image':inf[2],'stats':inf[3]},
        'mounted': {'name':mnt[1],'image':mnt[2],'stats':mnt[3]},
    }

def normalized_mask(im):
    a=im.getchannel('A').point(lambda v:255 if v>=128 else 0); box=a.getbbox()
    require(box is not None,'Empty alpha')
    return a.crop(box).resize((64,64),Image.Resampling.NEAREST)

def similarity(a,b):
    aa=normalized_mask(a).tobytes(); bb=normalized_mask(b).tobytes()
    common=sum(1 for x,y in zip(aa,bb) if x and y); union=sum(1 for x,y in zip(aa,bb) if x or y)
    return common/union if union else 1.0

def frame_for(name,tileset,anchors=None):
    mounted=name=='Mounted Slave Raider'
    if tileset=='FantasyHex': return (32,28),(30,26)
    if tileset in ('Minimal','HexaRealm'):
        return ((64,65),(62,63)) if mounted else ((64,56),(60,54))
    require(anchors is not None,'AbsoluteUnits requires native anchors')
    ref=anchors[UNIT_CLASS[name]]['image']
    return ref.size,(ref.width-2,ref.height-2)

def place_to_native_anchor(crop,frame,anchor_stats,bottom_margin=1):
    cst=alpha_stats(crop)
    target_cx=anchor_stats['cx_ratio']*frame[0]
    x=round(target_cx-cst['cx'])
    x=max(1,min(frame[0]-crop.width-1,x))
    y=frame[1]-crop.height-bottom_margin
    y=max(0,y)
    return x,y

def make_sprite(name,tileset,anchors):
    source=Image.open(SOURCE_DIR/(name+'.png')).convert('RGBA')
    box=source.getchannel('A').getbbox(); require(box is not None,'Empty source: '+name)
    crop=source.crop(box)
    frame,maxsize=frame_for(name,tileset,anchors)
    anchor=anchors[UNIT_CLASS[name]]
    if tileset=='AbsoluteUnits':
        rb=anchor['stats']['bbox']; native_h=rb[3]-rb[1]
        target_h=max(18,min(maxsize[1],native_h))
    else:
        target_h=maxsize[1]
    scale=min(maxsize[0]/crop.width,target_h/crop.height)
    wh=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)))
    crop=crop.resize(wh,Image.Resampling.NEAREST)
    out=Image.new('RGBA',frame,(0,0,0,0))
    x,y=place_to_native_anchor(crop,frame,anchor['stats'],1)
    out.alpha_composite(crop,(x,y))
    out.putalpha(out.getchannel('A').point(lambda v:0 if v<24 else (255 if v>224 else v)))
    return out

def make_religion_icon(baseline_icon):
    im=baseline_icon.convert('RGBA')
    out=Image.new('RGBA',im.size,(0,0,0,0))
    cx=(im.width-1)/2; cy=(im.height-1)/2; maxr=min(im.size)*0.43
    for y in range(im.height):
        for x in range(im.width):
            r,g,b,a=im.getpixel((x,y))
            if a<32: continue
            # Remove the opaque navy disk and the outer decorative rim; retain the bright
            # ouroboros/star glyph as a white tint-safe mask for CityTable.color.
            lum=0.2126*r+0.7152*g+0.0722*b
            rad=((x-cx)**2+(y-cy)**2)**0.5
            if lum<95 or rad>maxr: continue
            out.putpixel((x,y),(255,255,255,a))
    box=out.getchannel('A').getbbox(); require(box is not None,'Tint-safe Rationalism glyph empty')
    return out

def protected_baseline_check():
    allowed={'README.md','BUILD_STATUS.md','ART_VERIFICATION.json','v021.atlas','v021.png',
             'jsons/ModOptions.json','.github/workflows/v021-art-build.yml','tools/v021/build_assets.py'}
    for rel in baseline_files():
        if rel in allowed or rel.startswith('tools/v029/'): continue
        p=ROOT/rel
        require(p.is_file(),'Protected baseline file missing: '+rel)
        require(p.read_bytes()==git_bytes(rel),'Protected baseline file changed: '+rel)

def sprite_metrics(im,name,tileset,anchors):
    a=im.getchannel('A'); box=a.getbbox(); require(box,'Empty sprite: '+name)
    frame,maxsize=frame_for(name,tileset,anchors)
    require(im.size==frame,'Wrong sprite frame: '+tileset+' / '+name)
    require(box[3]>=im.height-2,'Sprite not bottom anchored: '+name)
    st=alpha_stats(im); target=anchors[UNIT_CLASS[name]]['stats']['cx_ratio']
    require(abs(st['cx_ratio']-target)<=0.075,'Sprite lateral anchor diverges from native reference: '+tileset+' / '+name)
    require(abs(st['cx_ratio']-.5)>=0.025,'Sprite remains visually centered: '+tileset+' / '+name)
    coverage=sum(v>=128 for v in a.tobytes())/(im.width*im.height)
    require(coverage<0.75,'Sprite background-like coverage: '+name)
    return {'frame':list(im.size),'bbox':list(box),'coverage':round(coverage,6),
            'centroid_x_ratio':round(st['cx_ratio'],6),'native_target_x_ratio':round(target,6),
            'rgba_sha256':digest(im.tobytes())}

def render_preview(current,anchors):
    PREVIEWS.mkdir(parents=True,exist_ok=True)
    font=ImageFont.load_default(size=13)
    cellw,cellh=210,150
    sheet=Image.new('RGB',(cellw*3,cellh*len(UNITS)),(45,45,45))
    d=ImageDraw.Draw(sheet)
    for row,name in enumerate(UNITS):
        cls=UNIT_CLASS[name]; native=anchors[cls]['image']
        custom=current[f'TileSets/AbsoluteUnits/Units/{name}']
        y=row*cellh
        d.text((5,y+5),name,font=font,fill='white')
        sheet.paste(native,(10,y+28),native)
        sheet.paste(custom,(220,y+28),custom)
        d.line((cellw*2+105,y+24,cellw*2+105,y+125),fill='white',width=1)
        sheet.paste(custom,(cellw*2+(210-custom.width)//2,y+28),custom)
        d.text((10,y+125),'native '+anchors[cls]['name'],font=font,fill='white')
        d.text((220,y+125),'Veilfall 1:1',font=font,fill='white')
        d.text((425,y+125),'centerline check',font=font,fill='white')
    sheet.save(PREVIEWS/'absoluteunits-native-comparison.png',optimize=True)

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

    native,native_atlas_sha,native_png_sha=fetch_native(); anchors=choose_native_anchors(native)
    current,_=atlas_read(ROOT); baseline=baseline_regions()
    require(len(current)==91,'Unexpected atlas entry count')
    require(set(baseline)-set(current)==set(),'Baseline atlas keys removed')
    for key in set(baseline)-EXISTING_REBUILT-{RELIGION_ICON}:
        require(current[key].size==baseline[key].size and current[key].tobytes()==baseline[key].tobytes(),'Preserved atlas region changed: '+key)

    metrics={}
    for name in UNITS:
        metrics[name]={}
        for ts in SETS:
            key=f'TileSets/{ts}/Units/{name}'
            require(key in current,'Missing rebuilt sprite: '+key)
            metrics[name][ts]=sprite_metrics(current[key],name,ts,anchors)
            gp=GENERATED/ts/(name+'.png')
            require(gp.is_file(),'Missing generated sprite: '+key)
            gi=Image.open(gp).convert('RGBA')
            require(gi.size==current[key].size and gi.tobytes()==current[key].tobytes(),'Generated/packed mismatch: '+key)

    for ts in SETS:
        require(len({metrics[n][ts]['rgba_sha256'] for n in UNITS})==11,'Duplicate map sprites in '+ts)
        require(similarity(current[f'TileSets/{ts}/Units/Slave'],current[f'TileSets/{ts}/Units/Slave Raider'])<0.80,'Slave/Raider too similar in '+ts)
        require(similarity(current[f'TileSets/{ts}/Units/Mounted Slave Raider'],current[f'TileSets/{ts}/Units/Slave Raider'])<0.90,'Mounted Raider insufficiently distinct in '+ts)

    icon=current[RELIGION_ICON]
    a=icon.getchannel('A'); box=a.getbbox(); require(box is not None,'Rationalism icon empty')
    require(a.getpixel((0,0))==0 and a.getpixel((icon.width-1,icon.height-1))==0,'Rationalism icon background not transparent')
    opaque=sum(v>=128 for v in a.tobytes())/(icon.width*icon.height)
    require(opaque<0.30,'Rationalism city icon still disk-like')
    for r,g,b,alpha in icon.getdata():
        if alpha: require(r==255 and g==255 and b==255,'Rationalism icon not tint-safe')

    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    status=(ROOT/'BUILD_STATUS.md').read_text(encoding='utf-8')
    workflow=(ROOT/'.github/workflows/v021-art-build.yml').read_text(encoding='utf-8')
    require(readme.startswith('# Unciv: Veilfall v0.2.9'),'README version wrong')
    require(status.startswith('# Veilfall v0.2.9'),'BUILD_STATUS version wrong')
    require('veilfall-v0.2.9-runtime-art-fix' in workflow and 'veilfall-v0.2.9-art-integration' in workflow,'Workflow branches wrong')

    return {
      'release':RELEASE,'predecessor':PREDECESSOR,'baseline_commit':BASELINE,'status':'automated_checks_passed',
      'manual_in_game_acceptance':'pending','entry_count':len(current),'rebuilt_map_sprite_region_count':44,
      'preserved_existing_region_count':46,'new_absoluteunits_region_count':11,'rationalism_city_icon_rebuilt':True,
      'native_reference_commit':NATIVE_COMMIT,'native_reference_atlas_sha256':native_atlas_sha,'native_reference_png_sha256':native_png_sha,
      'native_anchor_references':{k:{'name':v['name'],'frame':list(v['image'].size),'centroid_x_ratio':round(v['stats']['cx_ratio'],6),'bbox':list(v['stats']['bbox'])} for k,v in anchors.items()},
      'map_sprite_metrics':metrics,'exact_capture_rule':RULE,'capture_chance_percent':50,
      'gameplay_files_byte_identical':True,'portraits_and_icons_preserved_from_v0.2.8_except_rationalism_city_icon':True,
      'engine_note':'Unciv blocks embarked land units from capturing civilian units on water; no Marine gameplay semantics changed in this patch.',
      'v021_png_sha256':digest((ROOT/'v021.png').read_bytes()),'v021_atlas_sha256':digest((ROOT/'v021.atlas').read_bytes())
    }

def build():
    baseline=baseline_regions()
    native,_,_=fetch_native(); anchors=choose_native_anchors(native)
    assets={k:v for k,v in baseline.items() if k not in EXISTING_REBUILT and k!=RELIGION_ICON}
    rebuilt={}
    for name in UNITS:
        for ts in SETS:
            rebuilt[f'TileSets/{ts}/Units/{name}']=make_sprite(name,ts,anchors)
    assets.update(rebuilt)
    assets[RELIGION_ICON]=make_religion_icon(baseline[RELIGION_ICON])

    GENERATED.mkdir(parents=True,exist_ok=True)
    for key,im in rebuilt.items():
        _,ts,_,name=key.split('/',3)
        p=GENERATED/ts/(name+'.png'); p.parent.mkdir(parents=True,exist_ok=True); im.save(p,optimize=True)
    iconp=GENERATED/'UI'/'Rationalism-city-icon.png'; iconp.parent.mkdir(parents=True,exist_ok=True); assets[RELIGION_ICON].save(iconp,optimize=True)

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
    render_preview(assets,anchors)
    report=verify()
    (ROOT/'ART_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--check',action='store_true'); args=ap.parse_args()
    report=verify() if args.check else build()
    if args.check: require(report==load_json(ROOT/'ART_VERIFICATION.json'),'ART_VERIFICATION does not match deployed bytes')
    print(json.dumps({k:report[k] for k in ['release','status','entry_count','rebuilt_map_sprite_region_count','new_absoluteunits_region_count','capture_chance_percent','v021_png_sha256']},indent=2))

if __name__=='__main__': main()
