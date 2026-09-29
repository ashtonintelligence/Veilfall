"""Render v0.2.8 sprite QA sheets from the packed atlas."""
from PIL import Image,ImageDraw,ImageFont
from build_assets import ROOT,atlas_read,UNITS

def label(d,x,y,name,font,width=17):
    line=''; lines=[]
    for word in name.split():
        if len(line+' '+word)>width:
            lines.append(line); line=word
        else:
            line=(line+' '+word).strip()
    lines.append(line)
    for j,t in enumerate(lines): d.text((x+3,y+j*14),t,font=font,fill='white')

def main():
    assets,_=atlas_read(ROOT)
    out=ROOT/'tools/v028/previews'; out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.load_default(size=14)
    im=Image.new('RGB',(1408,430),(77,86,70)); d=ImageDraw.Draw(im)
    d.text((7,7),'Veilfall v0.2.8 dedicated map-sprite rebuild — native frame view above, enlarged nearest-neighbor inspection below.',font=font,fill='white')
    for i,name in enumerate(UNITS):
        x=i*128
        src=assets['TileSets/Minimal/Units/'+name]
        im.paste(src,(x+(128-src.width)//2,30),src)
        box=src.getchannel('A').getbbox(); crop=src.crop(box)
        scale=min(4,116/crop.width,190/crop.height)
        large=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.NEAREST)
        im.paste(large,(x+(128-large.width)//2,356-large.height),large)
        label(d,x,370,name,font)
    im.save(out/'sprites.png')

if __name__=='__main__': main()
