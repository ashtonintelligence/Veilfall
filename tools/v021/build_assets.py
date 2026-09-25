# Veilfall v0.2.2 visual-art corrective atlas builder
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
import json, hashlib, math, random

OUT=Path('.')
NAVY=(7,24,39,255); NAVY2=(13,36,53,255); GOLD=(184,145,75,255); LGOLD=(213,180,111,255); SCARLET=(166,25,46,255)
STONE=(211,185,140,255); CREAM=(240,214,162,255); WHITE=(255,255,255,255)

UNITS=['Continental Marines','Marine Riflemen','Expeditionary Marines','Fleet Marine Force','Marine Expeditionary Unit','Exo-Marine','Slave','Slave Raider','Mounted Slave Raider','Slave Hunter','Industrial Slaver']
PROMOS=['Operational Frontline','Operational Support','Marine Naval Integration','Marine Embarked Recon','Marine Expeditionary Endurance','MEU Combat Tempo','Exo-Marine Mobility','Slave Raider Doctrine']

def canvas(n=256): return Image.new('RGBA',(n,n),(0,0,0,0))
def circ(draw,box,fill=None,outline=None,w=1): draw.ellipse(box,fill=fill,outline=outline,width=w)
def star(draw,cx,cy,r1,r2,n=8,fill=LGOLD):
    pts=[]
    for i in range(n*2):
        a=-math.pi/2+i*math.pi/n; r=r1 if i%2==0 else r2
        pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    draw.polygon(pts,fill=fill)

def crest(size=256):
    im=canvas(size); d=ImageDraw.Draw(im); cx=cy=size/2
    circ(d,(size*.07,size*.07,size*.93,size*.93),fill=NAVY2,outline=GOLD,w=max(5,size//24))
    # Keep the accepted outer ring fixed; optically recenter the internal heraldry right/down.
    inner=canvas(size); q=ImageDraw.Draw(inner); ox=size*.025; oy=size*.025
    q.polygon([(cx+ox,size*.27+oy),(size*.69+ox,size*.39+oy),(size*.63+ox,size*.70+oy),(cx+ox,size*.79+oy),(size*.37+ox,size*.70+oy),(size*.31+ox,size*.39+oy)],fill=NAVY,outline=GOLD)
    star(q,cx+ox,cy+size*.02+oy,size*.14,size*.055,8,LGOLD)
    q.arc((size*.12+ox,size*.18+oy,size*.58+ox,size*.76+oy),70,290,fill=LGOLD,width=max(7,size//18))
    q.arc((size*.42+ox,size*.18+oy,size*.88+ox,size*.76+oy),250,470,fill=SCARLET,width=max(7,size//18))
    q.polygon([(size*.23+ox,size*.29+oy),(size*.13+ox,size*.18+oy),(size*.30+ox,size*.21+oy)],fill=GOLD)
    q.polygon([(size*.77+ox,size*.29+oy),(size*.87+ox,size*.18+oy),(size*.70+ox,size*.21+oy)],fill=SCARLET)
    q.polygon([(size*.39+ox,size*.22+oy),(size*.44+ox,size*.12+oy),(size*.50+ox,size*.20+oy),(size*.56+ox,size*.12+oy),(size*.61+ox,size*.22+oy)],fill=GOLD)
    im.alpha_composite(inner)
    return im

def rationalism(size=256):
    im=canvas(size); d=ImageDraw.Draw(im); m=size*.10; cx=cy=size/2
    circ(d,(m,m,size-m,size-m),fill=NAVY2,outline=GOLD,w=max(5,size//24))
    bb=(size*.23,size*.23,size*.77,size*.77); w=max(9,size//14)
    d.arc(bb,25,205,fill=GOLD,width=w); d.arc(bb,205,385,fill=SCARLET,width=w)
    for ang,col in [(25,GOLD),(205,SCARLET)]:
        x=cx+math.cos(math.radians(ang))*size*.27; y=cy+math.sin(math.radians(ang))*size*.27
        rr=size*.05; d.polygon([(x,y-rr),(x+rr*1.3,y),(x,y+rr),(x-rr*.6,y)],fill=col)
    star(d,cx,cy,size*.105,size*.04,8,LGOLD); return im

def knowledge(size=256):
    im=canvas(size); d=ImageDraw.Draw(im); m=size*.10
    circ(d,(m,m,size-m,size-m),fill=NAVY2,outline=GOLD,w=max(5,size//24))
    cx=size/2; x0,y0=size*.25,size*.31; x1,y1=size*.75,size*.71
    d.rounded_rectangle((x0-5,y0-5,x1+5,y1+5),radius=size*.035,outline=GOLD,width=max(4,size//28))
    d.polygon([(x0,y0),(cx-3,y0+size*.04),(cx-3,y1),(x0,y1-size*.04)],fill=CREAM)
    d.polygon([(cx+3,y0+size*.04),(x1,y0),(x1,y1-size*.04),(cx+3,y1)],fill=CREAM)
    d.line((cx,y0+4,cx,y1),fill=SCARLET,width=max(3,size//32)); return im

def building(kind,size=256):
    im=Image.new('RGBA',(size,size),NAVY2); d=ImageDraw.Draw(im)
    for y in range(size):
        t=y/(size-1); c=(int(28+85*t),int(52+45*t),int(66+25*t),255); d.line((0,y,size,y),fill=c)
    d.rectangle((0,size*.72,size,size),fill=(73,58,48,255))
    if kind=='Athenaeum':
        d.ellipse((size*.28,size*.12,size*.72,size*.50),fill=STONE,outline=GOLD,width=3)
        d.rectangle((size*.18,size*.37,size*.82,size*.76),fill=STONE)
        d.polygon([(size*.15,size*.37),(size*.85,size*.37),(size*.72,size*.25),(size*.28,size*.25)],fill=CREAM); cols=6
    elif kind=='Strategic Analysis Center':
        d.rectangle((size*.16,size*.24,size*.84,size*.77),fill=(159,137,109,255),outline=GOLD,width=3)
        d.rectangle((size*.10,size*.34,size*.22,size*.77),fill=(132,113,93,255)); d.rectangle((size*.78,size*.34,size*.90,size*.77),fill=(132,113,93,255))
        d.polygon([(size*.12,size*.24),(size*.88,size*.24),(size*.74,size*.12),(size*.26,size*.12)],fill=CREAM); cols=5
    elif kind=='The Great Archive':
        d.rectangle((size*.13,size*.22,size*.87,size*.78),fill=(154,131,102,255),outline=GOLD,width=3)
        d.rectangle((size*.18,size*.16,size*.82,size*.25),fill=CREAM); cols=7
        for yy in [0.35,0.48,0.61]:
            for xx in [0.25,0.38,0.50,0.62,0.75]: d.rectangle((size*xx-5,size*yy-8,size*xx+5,size*yy+8),fill=(236,187,93,255))
    else:
        d.rectangle((size*.18,size*.35,size*.82,size*.75),fill=STONE)
        d.polygon([(size*.14,size*.35),(size*.86,size*.35),(size*.72,size*.21),(size*.28,size*.21)],fill=CREAM); cols=6
        d.ellipse((size*.45,size*.48,size*.55,size*.58),fill=SCARLET)
    for i in range(cols):
        x=size*(.25 + i*(.50/max(cols-1,1))); d.rectangle((x-5,size*.39,x+5,size*.73),fill=CREAM)
    d.rectangle((size*.14,size*.73,size*.86,size*.78),fill=GOLD)
    return im

def human(d,coat,legs=None,skin=(163,118,83,255),head=(64,28)):
    legs=legs or coat
    d.ellipse((head[0]-8,head[1]-8,head[0]+8,head[1]+8),fill=skin)
    d.polygon([(48,43),(80,43),(84,88),(44,88)],fill=coat)
    d.polygon([(48,84),(61,84),(58,121),(45,121)],fill=legs)
    d.polygon([(67,84),(80,84),(83,121),(70,121)],fill=legs)

def rifle(d,x1,y1,x2,y2,col=(25,27,29,255),w=5):
    d.line((x1,y1,x2,y2),fill=col,width=w)
    d.line((x2-5,y2-4,x2+4,y2+4),fill=col,width=2)

def unit_sprite(name,size=128):
    im=canvas(size); d=ImageDraw.Draw(im)
    K=(25,27,29,255); S=(163,118,83,255); B=(91,68,47,255); O=(74,83,67,255); T=(126,105,74,255)
    if name=='Continental Marines':
        human(d,NAVY); d.polygon([(48,19),(64,11),(80,19),(72,23),(56,23)],fill=K)
        d.polygon([(51,43),(59,43),(75,88),(67,88)],fill=WHITE); d.polygon([(77,43),(69,43),(53,88),(61,88)],fill=WHITE)
        rifle(d,36,50,90,108,B,4); d.rectangle((46,52,51,70),fill=SCARLET)
    elif name=='Marine Riflemen':
        human(d,NAVY2); d.rectangle((52,17,76,22),fill=K); d.ellipse((55,12,73,24),fill=K)
        d.line((45,45,83,87),fill=GOLD,width=3); rifle(d,39,48,95,105,B,4); d.rectangle((78,50,83,68),fill=SCARLET)
    elif name=='Expeditionary Marines':
        human(d,T); d.polygon([(49,20),(64,12),(79,20),(73,25),(55,25)],fill=(104,89,61,255))
        d.rectangle((45,55,83,65),fill=(92,77,51,255)); rifle(d,37,50,94,104,B,4)
    elif name=='Fleet Marine Force':
        human(d,O); d.arc((49,13,79,31),180,360,fill=K,width=7); d.rectangle((45,50,83,66),fill=(62,69,55,255))
        rifle(d,37,52,96,101,K,5); d.rectangle((76,49,82,66),fill=GOLD)
    elif name=='Marine Expeditionary Unit':
        human(d,(47,58,50,255)); d.arc((47,10,81,34),180,360,fill=K,width=9)
        d.rectangle((45,48,83,67),fill=(40,46,41,255)); d.ellipse((73,19,78,24),fill=SCARLET)
        rifle(d,35,53,98,100,K,6); d.rectangle((45,70,54,80),fill=GOLD)
    elif name=='Exo-Marine':
        human(d,(31,36,43,255),legs=(31,36,43,255)); d.arc((44,8,84,38),180,360,fill=(45,52,61,255),width=11)
        d.arc((39,37,89,98),185,355,fill=GOLD,width=5); d.rectangle((43,50,85,72),outline=GOLD,width=3)
        rifle(d,35,52,99,98,(55,61,69,255),7); d.line((93,91,111,107),fill=SCARLET,width=4)
    elif name=='Slave':
        human(d,(205,190,160,255),legs=(188,170,140,255)); d.line((45,65,83,65),fill=(120,105,85,255),width=3)
        d.arc((50,78,78,102),0,180,fill=(150,145,135,255),width=3)
    elif name=='Slave Raider':
        human(d,(112,83,56,255),legs=(92,68,49,255)); d.rectangle((51,17,77,21),fill=(79,59,42,255))
        d.line((39,47,91,104),fill=(79,58,40,255),width=4); d.line((87,101,100,116),fill=(79,58,40,255),width=3)
        d.rectangle((46,56,82,62),fill=SCARLET)
    elif name=='Mounted Slave Raider':
        d.ellipse((13,67,93,101),fill=B); d.polygon([(79,70),(102,52),(114,61),(100,82)],fill=B); d.polygon([(101,53),(110,43),(108,59)],fill=B)
        for x in (26,48,70,86): d.polygon([(x,94),(x+8,94),(x+5,124),(x-2,124)],fill=B)
        d.polygon([(18,75),(4,63),(18,88)],fill=B); d.ellipse((51,28,65,42),fill=S); d.polygon([(45,42),(70,42),(76,72),(49,73)],fill=(79,67,55,255))
        d.arc((48,20,68,37),180,360,fill=K,width=5); d.line((65,46,97,75),fill=K,width=4)
    elif name=='Slave Hunter':
        human(d,(105,55,43,255),legs=(47,49,46,255)); d.polygon([(50,18),(64,9),(78,18),(75,28),(53,28)],fill=(223,216,191,255))
        d.rectangle((45,51,83,60),fill=SCARLET); rifle(d,35,50,98,105,B,5)
    elif name=='Industrial Slaver':
        human(d,(35,36,38,255),legs=(31,32,34,255)); d.rectangle((51,11,77,18),fill=K); d.rectangle((55,4,73,15),fill=K)
        d.polygon([(48,43),(80,43),(87,93),(41,93)],fill=(38,39,41,255)); d.line((53,44,64,61),fill=GOLD,width=2); d.line((75,44,64,61),fill=GOLD,width=2)
        d.ellipse((61,59,67,65),outline=GOLD,width=2); d.rectangle((82,61,98,82),fill=B,outline=GOLD,width=2); d.line((42,56,29,110),fill=B,width=4)
    return im

def unit_icon(name,size=128):
    sp=unit_sprite(name,size); alpha=sp.getchannel('A').filter(ImageFilter.MaxFilter(3))
    im=Image.new('RGBA',(size,size),(255,255,255,0)); im.putalpha(alpha); return im

def load_unit_portraits():
    result={}
    for name in UNITS:
        fn=name.replace(' ','_')+'_portrait.jpg'
        path=Path('tools/v022/portraits')/fn
        im=Image.open(path).convert('RGB')
        if im.size != (128,128): raise SystemExit('Unexpected portrait size for '+name+': '+repr(im.size))
        result[name]=im.resize((256,256),Image.Resampling.LANCZOS).convert('RGBA')
    return result

def promo(name,size=256):
    im=canvas(size); d=ImageDraw.Draw(im); m=size*.09; cx=cy=size/2; w=max(4,size//20)
    circ(d,(m,m,size-m,size-m),fill=NAVY2,outline=GOLD,w=max(4,size//22))
    if name=='Operational Frontline': d.polygon([(cx,size*.22),(size*.70,size*.39),(size*.62,size*.76),(size*.38,size*.76),(size*.30,size*.39)],fill=SCARLET,outline=LGOLD)
    elif name=='Operational Support': d.line((cx,size*.24,cx,size*.76),fill=LGOLD,width=w); d.arc((size*.27,size*.50,size*.73,size*.85),180,360,fill=LGOLD,width=w)
    elif name=='Marine Naval Integration': d.line((size*.29,size*.72,size*.71,size*.28),fill=LGOLD,width=w); d.line((size*.29,size*.28,size*.71,size*.72),fill=SCARLET,width=w)
    elif name=='Marine Embarked Recon': d.ellipse((size*.27,size*.40,size*.73,size*.60),outline=LGOLD,width=w); d.ellipse((size*.46,size*.46,size*.54,size*.54),fill=SCARLET)
    elif name=='Marine Expeditionary Endurance': d.polygon([(cx,size*.22),(size*.68,size*.35),(size*.62,size*.76),(size*.38,size*.76),(size*.32,size*.35)],outline=LGOLD); d.line((cx,size*.32,cx,size*.66),fill=LGOLD,width=w)
    elif name=='MEU Combat Tempo': d.polygon([(size*.48,size*.22),(size*.32,size*.55),(size*.48,size*.55),(size*.38,size*.80),(size*.70,size*.43),(size*.53,size*.43)],fill=LGOLD)
    elif name=='Exo-Marine Mobility': d.line((size*.26,size*.70,size*.73,size*.27),fill=LGOLD,width=w); d.polygon([(size*.63,size*.26),(size*.78,size*.23),(size*.74,size*.38)],fill=SCARLET)
    elif name=='Slave Raider Doctrine': d.line((size*.27,size*.28,size*.73,size*.72),fill=SCARLET,width=w); d.line((size*.73,size*.28,size*.27,size*.72),fill=LGOLD,width=w)
    return im

assets={'NationPortraits/Ashton':crest(256),'NationIcons/Ashton':crest(128),'ReligionPortraits/Rationalism':rationalism(256),'ReligionIcons/Rationalism':rationalism(128),'ResourcePortraits/Knowledge':knowledge(256)}
for b in ['Athenaeum','Strategic Analysis Center','The Great Archive','Forum of Inquiry']: assets['BuildingPortraits/'+b]=building(b)
unit_portraits=load_unit_portraits()
for u in UNITS:
    assets['UnitPortraits/'+u]=unit_portraits[u]
    ui=unit_icon(u); assets['UnitIcons/'+u]=ui
    sprite=unit_sprite(u)
    for ts in ['Minimal','FantasyHex','HexaRealm']: assets[f'TileSets/{ts}/Units/{u}']=sprite.copy()
for p in PROMOS:
    assets['UnitPromotionPortraits/'+p]=promo(p,256); assets['UnitPromotionIcons/'+p]=promo(p,128)
assert len(assets)==80

atlas=Image.new('RGBA',(2048,2048),(0,0,0,0)); positions={}; x=y=2; rowh=0
for key in sorted(assets,key=lambda k:(-assets[k].height,k)):
    im=assets[key]; w,h=im.size
    if x+w+2>2048: x=2; y+=rowh+2; rowh=0
    if y+h+2>2048: raise RuntimeError('v021 atlas overflow')
    atlas.alpha_composite(im,(x,y)); positions[key]=(x,y,w,h); x+=w+2; rowh=max(rowh,h)
atlas.quantize(colors=96,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.FLOYDSTEINBERG).save(OUT/'v021.png',optimize=True)
lines=['v021.png','size: 2048, 2048','format: RGBA8888','filter: Nearest, Nearest','repeat: none']
for key in sorted(positions):
    x,y,w,h=positions[key]; lines += [key,'  rotate: false',f'  xy: {x}, {y}',f'  size: {w}, {h}',f'  orig: {w}, {h}','  offset: 0, 0','  index: -1']
(OUT/'v021.atlas').write_text('\n'.join(lines)+'\n',encoding='utf-8')
required=sorted(assets); text=(OUT/'v021.atlas').read_text(encoding='utf-8')
missing=[k for k in required if ('\n'+k+'\n') not in ('\n'+text)]
if missing: raise SystemExit('Missing atlas keys: '+repr(missing))
check=Image.open(OUT/'v021.png').convert('RGBA'); alpha=check.getchannel('A')
if alpha.getextrema()[0] != 0: raise SystemExit('Atlas has no true transparency')
icon_hashes={u:hashlib.sha256(assets['UnitIcons/'+u].tobytes()).hexdigest() for u in UNITS}
if len(set(icon_hashes.values())) != len(UNITS): raise SystemExit('Custom unit icons are not all visually distinct')
verification={'release':'v0.2.2','entry_count':80,'missing_keys':missing,'png_size':list(check.size),'alpha_extrema':list(alpha.getextrema()),'required_keys':required,'distinct_unit_icon_count':len(set(icon_hashes.values())),'v021_png_sha256':hashlib.sha256((OUT/'v021.png').read_bytes()).hexdigest(),'v021_atlas_sha256':hashlib.sha256((OUT/'v021.atlas').read_bytes()).hexdigest()}
(OUT/'ART_VERIFICATION.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in verification.items() if k!='required_keys'},indent=2))
