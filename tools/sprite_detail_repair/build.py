"""Dense map sprites with explicit world-space limits and a last-loaded atlas.

Recommended execution model: GPT-6 Astra; effort: Extra High.
Requires Pillow 11.3.0. Art generation prompts are recorded separately.
"""
from pathlib import Path
from io import BytesIO
import argparse
import hashlib
import json
import subprocess
import sys
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASELINE = 'de02479f97a367e8a12c40a8feb14beb9428ba27'
ENGINE = '3318515bfca2609a9edb127b59cfadbab6d58d38'
SETS = ['Minimal', 'HexaRealm', 'FantasyHex']
REFERENCES = {
    'Slave': 'Worker', 'Slave Raider': 'Swordsman', 'Mounted Slave Raider': 'Knight',
    'Slave Hunter': 'Rifleman', 'Industrial Slaver': 'Infantry',
    'Continental Marines': 'Musketman', 'Marine Riflemen': 'Rifleman',
    'Expeditionary Marines': 'Infantry', 'Fleet Marine Force': 'Marine',
    'Marine Expeditionary Unit': 'Marine', 'Exo-Marine': 'Marine',
}
UNITS = list(REFERENCES)
KEYS = {f'TileSets/{ts}/Units/{n}' for ts in SETS for n in UNITS}
sys.path.insert(0, str(ROOT / 'tools/v029'))
import build_assets as legacy


def old(path):
    return subprocess.check_output(['git', 'show', BASELINE + ':' + path], cwd=ROOT)


def sha(data):
    return hashlib.sha256(data).hexdigest()


@lru_cache(maxsize=1)
def baseline():
    return legacy.parse_atlas(old('v021.atlas'), old('v021.png'), 'v021.png')[0]


def refset(ts):
    return 'HexaRealm' if ts == 'Minimal' else ts


def reference(name, ts):
    return Image.open(HERE / 'reference' / f'{refset(ts)}-{REFERENCES[name]}.png').convert('RGBA')


def prepare_references(engine_root):
    p = Path(engine_root)
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=p, text=True).strip() == ENGINE
    a = p / 'android/assets'
    regions, _ = legacy.parse_atlas((a/'Tilesets.atlas').read_bytes(), (a/'Tilesets.png').read_bytes(), 'Tilesets.png')
    for ts in ['HexaRealm', 'FantasyHex']:
        for name in sorted(set(REFERENCES.values())):
            regions[f'TileSets/{ts}/Units/{name}'].save(HERE/'reference'/f'{ts}-{name}.png')
        for terrain in ['Grassland', 'Desert']:
            regions[f'TileSets/{ts}/Tiles/{terrain}'].save(HERE/'reference'/f'{ts}-{terrain}.png')
    license_file = p / 'LICENSE'
    if license_file.exists():
        (HERE/'reference/UNCIV-LICENSE.txt').write_bytes(license_file.read_bytes())


def make_sprite(name, ts, prior):
    source = Image.open(HERE/'source'/f'{name}.png').convert('RGBA')
    box = source.getchannel('A').point(lambda v: 255 if v >= 128 else 0).getbbox()
    assert box
    crop = source.crop(box)
    ps = legacy.alpha_stats(prior)
    rs = legacy.alpha_stats(reference(name, ts))
    density = 256 / prior.width
    frame = (256, round(prior.height * density))
    # Never stretch independently. Keep native-comparable height, with modest
    # width allowance for the new poses, within the released occupied width.
    max_h = min(ps['h'], rs['h'] * 1.05)
    max_w = min(ps['w'], rs['w'] * 1.20)
    target_x = (ps['centroid_x'] if name=='Continental Marines' else rs['centroid_x']) * density
    bottom = ps['bbox'][3] * density
    scale = min(max_w*density/crop.width, max_h*density/crop.height)
    for _ in range(300):
        size = tuple(max(1, round(v*scale)) for v in crop.size)
        fig = crop.resize(size, Image.Resampling.LANCZOS)
        # Alpha is quantized only at the final dense texture size. This prevents
        # fringe residue without collapsing the figure into a coarse grid.
        fig.putalpha(fig.getchannel('A').point(lambda v: 255 if v >= 128 else 0))
        fig = fig.crop(fig.getchannel('A').getbbox())
        fs = legacy.alpha_stats(fig)
        x = round(target_x - fs['centroid_x'])
        y = round(bottom - fig.height)
        if x >= 2 and y >= 2 and x+fig.width <= frame[0]-2 and y+fig.height <= frame[1]-2:
            break
        scale *= .99
    else:
        raise AssertionError('Could not fit without clipping: '+name+' / '+ts)
    out = Image.new('RGBA', frame)
    out.paste(fig, (x, y))
    return out


def pack(assets):
    page = Image.new('RGBA', (2048, 2048))
    lines = ['sprite-detail.png', 'size: 2048, 2048', 'format: RGBA8888',
             'filter: Nearest, Nearest', 'repeat: none']
    x = y = 4
    row_h = 0
    for key, im in sorted(assets.items()):
        w,h = im.size
        if x+w+4 > page.width:
            x=4; y+=row_h+8; row_h=0
        assert y+h+4 <= page.height
        page.paste(im,(x,y))
        lines += [key,'  rotate: false',f'  xy: {x}, {y}',f'  size: {w}, {h}',
                  f'  orig: {w}, {h}','  offset: 0, 0','  index: -1']
        x+=w+8; row_h=max(row_h,h)
    buf=BytesIO();page.save(buf,format='PNG',optimize=True)
    return ('\n'.join(lines)+'\n').encode(),buf.getvalue()


def render_tile(unit, name, ts, width, terrain, badge=True):
    # Deliberately a CPU texture-sampling simulation, not an Unciv screenshot.
    tile = Image.new('RGBA',(width,round(width*1.12)), '#d9dfca' if terrain=='Grassland' else '#e2d1a6')
    bg = Image.open(HERE/'reference'/f'{refset(ts)}-{terrain}.png').convert('RGBA')
    bg = bg.resize((width,round(bg.height*width/bg.width)),Image.Resampling.NEAREST)
    tile.alpha_composite(bg,(0,round(width*.10)))
    art = unit.resize((width,round(unit.height*width/unit.width)),Image.Resampling.NEAREST)
    tile.alpha_composite(art,(0,round(width*.10)))
    if badge:
        # Positions follow the pinned engine's default TileGroup size (54),
        # image width (81), origin and +/-20 flag slot offset. Circle decoration
        # is still approximate; this is not a full UI rendering.
        slot_offset=-20 if name=='Slave' else 20
        cy_ratio=unit.height/unit.width-(3**.5/16)-(27+slot_offset)/81
        cx,cy=round(width*.50),round(width*(.10+cy_ratio))
        r=round(width*15/81)
        d=ImageDraw.Draw(tile)
        d.ellipse((cx-r,cy-r,cx+r,cy+r), fill='#102b39',outline='#d6ba64',width=max(1,round(width*.018)))
        icon = baseline()['UnitIcons/'+name]
        icon=icon.resize((round(r*1.38),round(r*1.38)),Image.Resampling.LANCZOS)
        tile.alpha_composite(icon,(cx-icon.width//2,cy-icon.height//2))
        d.rectangle((cx-r,cy+r-1,cx+r,cy+r+round(width*.035)),fill='#07100d')
        d.rectangle((cx-r+2,cy+r+1,cx+r-2,cy+r+round(width*.028)),fill='#3fe52d')
    return tile


def preview(before, after):
    outdir=HERE/'review';outdir.mkdir(exist_ok=True)
    font=ImageFont.load_default(size=19);small=ImageFont.load_default(size=14)
    # Six-by-five roster groups are split into short review pages for legibility.
    for ts in ['HexaRealm','FantasyHex']:
        for family,names in [('marines',UNITS[5:]),('slavery',UNITS[:5])]:
            height=125+len(names)*285
            sheet=Image.new('RGB',(1160,height),'#f1eee6');d=ImageDraw.Draw(sheet)
            d.text((20,14),f'{ts} | {family.title()} | packed assets at equal displayed frame widths',fill='#142737',font=font)
            d.text((20,42),'SIMULATED texture sampling, not a running-game screenshot. Badge placement is approximate.',fill='#44515b',font=small)
            d.text((20,64),'Each group: 192 px inspection on grassland + 96 px map-size sample on desert. Minimal uses HexaRealm art.',fill='#44515b',font=small)
            for i,name in enumerate(names):
                y=100+i*285
                d.text((20,y),name,fill='#142737',font=font)
                key=f'TileSets/{ts}/Units/{name}'
                for col,(label,im) in enumerate([('Released v0.2.11',before[key]),('Repair candidate',after[key]),('Native '+REFERENCES[name],reference(name,ts))]):
                    x=20+col*380
                    d.text((x,y+25),label,fill='#344b58',font=small)
                    for dx,width,terrain in [(0,192,'Grassland'),(230,96,'Desert')]:
                        tile=render_tile(im,name,ts,width,terrain)
                        sheet.paste(tile,(x+dx,y+48),tile)
            sheet.save(outdir/f'{ts.lower()}-{family}.png')
    # One compact lead image with the two units in Paul's screenshots, unbadged
    # for unobstructed inspection and badged for overlap context.
    sheet=Image.new('RGB',(1140,780),'#f1eee6');d=ImageDraw.Draw(sheet)
    d.text((20,14),'Continental Marines + Mounted Slave Raider | packed candidate',fill='#142737',font=font)
    d.text((20,42),'SIMULATED comparison: same 192 px frame width. Actual device appearance remains unaccepted.',fill='#44515b',font=small)
    for row,name in enumerate(['Continental Marines','Mounted Slave Raider']):
        ts='HexaRealm';key=f'TileSets/{ts}/Units/{name}';y=80+row*345
        d.text((20,y),name,fill='#142737',font=font)
        for col,(label,im) in enumerate([('Released v0.2.11',before[key]),('Repair candidate',after[key]),('Native '+REFERENCES[name],reference(name,ts))]):
            x=20+col*380
            d.text((x,y+30),label,fill='#344b58',font=small)
            for dx,width,terrain,badge in [(0,192,'Grassland',False),(230,96,'Desert',True)]:
                tile=render_tile(im,name,ts,width,terrain,badge)
                sheet.paste(tile,(x+dx,y+56),tile)
    sheet.save(outdir/'key-unit-comparison.png')


def verify():
    before=baseline()
    atlas=(ROOT/'sprite-detail.atlas').read_bytes();png=(ROOT/'sprite-detail.png').read_bytes()
    current,boxes=legacy.parse_atlas(atlas,png,'sprite-detail.png')
    assert set(current)==KEYS
    expected={f'TileSets/{ts}/Units/{n}':make_sprite(n,ts,before[f'TileSets/{ts}/Units/{n}']) for ts in SETS for n in UNITS}
    assert pack(expected)==(atlas,png),'Packed output not reproducible from source'
    geometry=[]
    for key,im in current.items():
        ts=key.split('/')[1];name=key.split('/')[-1]
        prev=legacy.alpha_stats(before[key]);now=legacy.alpha_stats(im);ref=legacy.alpha_stats(reference(name,ts))
        density=im.width/before[key].width
        assert im.width==256
        assert now['w']/density<=prev['w']+.25 and now['h']/density<=prev['h']+.25,'Oversized '+key
        assert now['h']/density<=ref['h']*1.05+.25,'Exceeds native height '+key
        assert now['h']/density>=ref['h']*.65,'Figure too small '+key
        assert abs(now['bbox'][3]/density-prev['bbox'][3])<.13,'Grounding drift '+key
        target_cx=prev['centroid_x'] if name=='Continental Marines' else ref['centroid_x']
        shift=now['centroid_x']/density-prev['centroid_x']
        assert abs(now['centroid_x']/density-target_cx)<=.5/density+1e-9,'Lateral anchor drift '+key
        assert now['center_delta_x']*prev['center_delta_x']>0,'Offset reversal '+key
        assert now['soft_alpha_ratio']==0,'Alpha fringe '+key
        box=now['bbox'];assert box[0]>=2 and box[1]>=2 and box[2]<=im.width-2 and box[3]<=im.height-2,'Clipping '+key
        x,y,w,h=boxes[key]
        for other,(ox,oy,ow,oh) in boxes.items():
            if key!=other:assert x+w<=ox or ox+ow<=x or y+h<=oy or oy+oh<=y,'Overlapping atlas regions'
        geometry.append({'region':key,'old_frame':list(before[key].size),'new_frame':list(im.size),
            'old_occupied':list(prev['bbox']),'new_occupied_in_old_coordinates':[round(v/density,3) for v in now['bbox']],
            'native_reference':REFERENCES[name],'native_height_ratio':round(now['h']/density/ref['h'],3),
            'lateral_shift_in_old_pixels':round(shift,5),'rgba_sha256':sha(im.tobytes())})
    files=subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE],cwd=ROOT,text=True).splitlines()
    for rel in files:
        if rel!='Atlases.json':assert (ROOT/rel).read_bytes()==old(rel),'Protected predecessor changed: '+rel
    assert json.loads((ROOT/'Atlases.json').read_text())==['game','v021','sprite-detail']
    # Match ImageGetter's last-region-wins load order; all existing pages remain unchanged.
    effective=dict(before);effective.update(current)
    assert len(effective)==len(before)==80
    assert all(effective[k].tobytes()==before[k].tobytes() for k in set(before)-KEYS)
    assert all(effective[k].tobytes()==current[k].tobytes() for k in KEYS)
    for ts in SETS:
        assert len({sha(current[f'TileSets/{ts}/Units/{n}'].tobytes()) for n in UNITS})==11
    source_hashes={n:sha((HERE/'source'/f'{n}.png').read_bytes()) for n in UNITS}
    return {'status':'PASS','baseline_commit':BASELINE,'engine_reference':ENGINE,
            'candidate_only':True,'deployed':False,'visual_acceptance':'pending',
            'preview_kind':'CPU simulation, not actual Unciv graphical rendering',
            'effective_changed_regions':33,'effective_preserved_v021_regions':47,
            'protected_predecessor_files':len(files)-1,'all_gameplay_json_byte_identical':True,
            'all_original_atlas_files_byte_identical':True,'source_sha256':source_hashes,
            'atlas_sha256':sha(atlas),'png_sha256':sha(png),'geometry':geometry}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');ap.add_argument('--references-from')
    args=ap.parse_args()
    if args.references_from:prepare_references(args.references_from)
    if not args.check:
        before=baseline();assets={f'TileSets/{ts}/Units/{n}':make_sprite(n,ts,before[f'TileSets/{ts}/Units/{n}']) for ts in SETS for n in UNITS}
        a,p=pack(assets);(ROOT/'sprite-detail.atlas').write_bytes(a);(ROOT/'sprite-detail.png').write_bytes(p)
        (ROOT/'Atlases.json').write_text(json.dumps(['game','v021','sprite-detail'],indent=2)+'\n')
        # Review crops are deliberately re-read from packed bytes.
        packed,_=legacy.parse_atlas(a,p,'sprite-detail.png');preview(before,packed)
    report=verify()
    if args.check:assert report==json.loads((HERE/'verification.json').read_text())
    else:(HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['geometry','source_sha256']},indent=2))


if __name__=='__main__':main()
