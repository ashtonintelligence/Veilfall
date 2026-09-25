from PIL import Image, ImageDraw
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
    d.polygon([(cx,size*.27),(size*.69,size*.39),(size*.63,size*.70),(cx,size*.79),(size*.37,size*.70),(size*.31,size*.39)],fill=NAVY,outline=GOLD)
    star(d,cx,cy+size*.02,size*.14,size*.055,8,LGOLD)
    d.arc((size*.12,size*.18,size*.58,size*.76),70,290,fill=LGOLD,width=max(7,size//18))
    d.arc((size*.42,size*.18,size*.88,size*.76),250,470,fill=SCARLET,width=max(7,size//18))
    d.polygon([(size*.23,size*.29),(size*.13,size*.18),(size*.30,size*.21)],fill=GOLD)
    d.polygon([(size*.77,size*.29),(size*.87,size*.18),(size*.70,size*.21)],fill=SCARLET)
    d.polygon([(size*.39,size*.22),(size*.44,size*.12),(size*.50,size*.20),(size*.56,size*.12),(size*.61,size*.22)],fill=GOLD)
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

def portrait(name,size=256):
    im=Image.new('RGBA',(size,size),NAVY2); d=ImageDraw.Draw(im); random.seed(name)
    d.rectangle((0,size*.58,size,size),fill=(60,59,58,255)); cx=size*.50; skin=(163,118,83,255)
    if name=='Mounted Slave Raider':
        d.ellipse((size*.18,size*.60,size*.78,size*.84),fill=(67,48,36,255)); d.ellipse((size*.69,size*.50,size*.86,size*.68),fill=(67,48,36,255))
    if name=='Continental Marines': coat=(36,57,76,255); accent=SCARLET
    elif name=='Marine Riflemen': coat=(47,67,73,255); accent=GOLD
    elif name=='Expeditionary Marines': coat=(92,83,62,255); accent=(47,65,52,255)
    elif name=='Fleet Marine Force': coat=(58,70,56,255); accent=GOLD
    elif name=='Marine Expeditionary Unit': coat=(46,62,56,255); accent=SCARLET
    elif name=='Exo-Marine': coat=(24,31,40,255); accent=GOLD
    elif name=='Slave': coat=(111,91,70,255); accent=(137,112,79,255)
    elif name=='Industrial Slaver': coat=(33,34,35,255); accent=GOLD
    else: coat=(88,69,52,255); accent=SCARLET
    d.ellipse((cx-size*.10,size*.13,cx+size*.10,size*.33),fill=skin)
    d.polygon([(cx-size*.18,size*.31),(cx+size*.18,size*.31),(cx+size*.24,size*.78),(cx-size*.24,size*.78)],fill=coat)
    d.polygon([(cx-size*.18,size*.76),(cx-size*.03,size*.76),(cx-size*.08,size*.98),(cx-size*.22,size*.98)],fill=coat)
    d.polygon([(cx+size*.03,size*.76),(cx+size*.18,size*.76),(cx+size*.22,size*.98),(cx+size*.08,size*.98)],fill=coat)
    if name.startswith('Marine') or name in ['Continental Marines','Exo-Marine']:
        d.line((cx+size*.12,size*.38,size*.86,size*.72),fill=(35,31,28,255),width=max(7,size//24))
    if name=='Exo-Marine':
        d.arc((cx-size*.22,size*.24,cx+size*.22,size*.72),180,360,fill=GOLD,width=8); d.line((size*.66,size*.43,size*.90,size*.66),fill=SCARLET,width=6)
    if name=='Industrial Slaver': d.rectangle((size*.65,size*.55,size*.83,size*.70),fill=(69,45,30,255),outline=GOLD,width=2)
    if name in ['Slave Raider','Slave Hunter']: d.line((size*.62,size*.30,size*.87,size*.78),fill=(50,38,29,255),width=6)
    if name=='Slave': d.arc((size*.32,size*.52,size*.68,size*.86),10,170,fill=(180,174,160,255),width=4)
    if 'Marine' in name: d.rectangle((cx-size*.18,size*.42,cx-size*.13,size*.55),fill=accent)
    return im

def unit_icon(name,size=128):
    im=canvas(size); d=ImageDraw.Draw(im); W=WHITE
    d.ellipse((size*.43,size*.10,size*.57,size*.24),fill=W)
    d.polygon([(size*.35,size*.27),(size*.65,size*.27),(size*.61,size*.68),(size*.39,size*.68)],fill=W)
    d.polygon([(size*.39,size*.65),(size*.49,size*.65),(size*.45,size*.94),(size*.34,size*.94)],fill=W)
    d.polygon([(size*.51,size*.65),(size*.61,size*.65),(size*.66,size*.94),(size*.55,size*.94)],fill=W)
    if name=='Mounted Slave Raider':
        d.ellipse((size*.12,size*.55,size*.72,size*.88),outline=W,width=5); d.ellipse((size*.62,size*.45,size*.83,size*.62),fill=W)
    elif name=='Slave': d.arc((size*.18,size*.28,size*.82,size*.82),15,165,fill=W,width=4)
    else: d.line((size*.62,size*.31,size*.92,size*.78),fill=W,width=5)
    if name in ['Exo-Marine','Marine Expeditionary Unit']: d.arc((size*.24,size*.18,size*.76,size*.70),180,360,fill=W,width=4)
    if name=='Industrial Slaver': d.rectangle((size*.67,size*.49,size*.88,size*.68),outline=W,width=3)
    return im

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
for u in UNITS:
    assets['UnitPortraits/'+u]=portrait(u); ui=unit_icon(u); assets['UnitIcons/'+u]=ui
    for ts in ['Minimal','FantasyHex','HexaRealm']: assets[f'TileSets/{ts}/Units/{u}']=ui.copy()
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
verification={'release':'v0.2.1','entry_count':80,'missing_keys':missing,'png_size':list(check.size),'alpha_extrema':list(alpha.getextrema()),'required_keys':required,'v021_png_sha256':hashlib.sha256((OUT/'v021.png').read_bytes()).hexdigest(),'v021_atlas_sha256':hashlib.sha256((OUT/'v021.atlas').read_bytes()).hexdigest()}
(OUT/'ART_VERIFICATION.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in verification.items() if k!='required_keys'},indent=2))
