"""Render QA sheets from the packed atlas; these are not engine screenshots."""
from PIL import Image,ImageDraw,ImageFont
from artwork import UNITS
from build_assets import ROOT,atlas_read

def label(d,x,y,name,font,width=17):
    line='';lines=[]
    for word in name.split():
        if len(line+' '+word)>width:lines.append(line);line=word
        else:line=(line+' '+word).strip()
    lines.append(line)
    for j,t in enumerate(lines):d.text((x+3,y+j*15),t,font=font,fill='white')

def main():
    assets,_=atlas_read(ROOT);out=ROOT/'tools/v026/previews';out.mkdir(exist_ok=True)
    font=ImageFont.load_default(size=14)
    im=Image.new('RGB',(1536,610),(49,58,63));d=ImageDraw.Draw(im)
    for i,name in enumerate(UNITS):
        col=i if i<5 else i-5;row=0 if i<5 else 1;x=col*256;y=row*305
        src=assets['UnitPortraits/'+name];im.paste(src,(x,y),src);d.text((x+7,y+269),name,font=font,fill='white')
    im.save(out/'portraits.png')
    im=Image.new('RGB',(1408,346),(49,58,63));d=ImageDraw.Draw(im)
    for i,name in enumerate(UNITS):
        x=i*128;src=assets['UnitIcons/'+name];im.paste(src,(x,22),src)
        d.rectangle((x,164,x+127,291),fill=(224,219,201))
        dark=Image.new('RGBA',src.size,(31,42,58,0));dark.putalpha(src.getchannel('A'));im.paste(dark,(x,164),dark)
        label(d,x,299,name,font)
    im.save(out/'icon_tints.png')
    im=Image.new('RGB',(1408,430),(77,86,70));d=ImageDraw.Draw(im)
    d.text((7,7),'Native 128px cells; unit footprint roughly 18-44px. Lower row: enlarged silhouette inspection.',font=font,fill='white')
    for i,name in enumerate(UNITS):
        x=i*128;src=assets['TileSets/Minimal/Units/'+name];im.paste(src,(x,22),src)
        crop=src.crop(src.getchannel('A').getbbox());scale=min(4,116/crop.width,190/crop.height)
        large=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.NEAREST)
        im.paste(large,(x+(128-large.width)//2,361-large.height),large);label(d,x,380,name,font)
    im.save(out/'sprites.png')

if __name__=='__main__':main()
