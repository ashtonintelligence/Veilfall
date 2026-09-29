"""Render v0.2.9 native-comparison QA sheets from the packed override atlas."""
from PIL import Image, ImageDraw, ImageFont
import build_assets as b


def draw_crosshair(d,x,y,w,h):
    d.line((x+w/2,y,x+w/2,y+h),fill=(190,190,190),width=1)
    d.line((x,y+h/2,x+w,y+h/2),fill=(190,190,190),width=1)


def paste_with_bbox(sheet,d,im,x,y,scale=1):
    if scale != 1:
        im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
    draw_crosshair(d,x,y,im.width,im.height)
    sheet.paste(im,(x,y),im)
    box=im.getchannel('A').getbbox()
    if box:
        d.rectangle((x+box[0],y+box[1],x+box[2]-1,y+box[3]-1),outline=(230,230,230),width=1)
    d.rectangle((x,y,x+im.width-1,y+im.height-1),outline=(105,105,105),width=1)


def render_set(ts, assets):
    font=ImageFont.load_default(size=14)
    row_h=170; width=1000; height=48+row_h*len(b.UNITS)
    sheet=Image.new('RGB',(width,height),(42,45,48)); d=ImageDraw.Draw(sheet)
    d.text((12,10),f'Veilfall v0.2.9 - {ts} map sprites: pinned native reference vs custom override',font=font,fill='white')
    d.text((12,28),'Top: exact native/game texture scale. Bottom: 3x nearest-neighbor inspection. Crosshair = canvas center; box = alpha bounds.',font=font,fill=(220,220,220))
    for i,name in enumerate(b.UNITS):
        y=48+i*row_h
        ref_name,ref,refm=b.choose_reference(name,ts)
        custom=assets[f'TileSets/{ts}/Units/{name}']
        d.text((12,y+4),name,font=font,fill='white')
        d.text((12,y+24),f'native: {ref_name}',font=font,fill=(205,205,205))
        d.text((225,y+4),'Native',font=font,fill='white'); d.text((430,y+4),'Custom',font=font,fill='white')
        paste_with_bbox(sheet,d,ref,225,y+24)
        paste_with_bbox(sheet,d,custom,430,y+24)
        paste_with_bbox(sheet,d,ref,610,y+20,3)
        paste_with_bbox(sheet,d,custom,800,y+20,3)
        cm=b.alpha_metrics(custom)
        d.text((12,y+48),f"native cx {refm['centroid_norm'][0]:.3f}",font=font,fill=(205,205,205))
        d.text((12,y+66),f"custom cx {cm['centroid_norm'][0]:.3f}",font=font,fill=(205,205,205))
        d.text((12,y+84),f"native bbox {refm['bbox']}",font=font,fill=(205,205,205))
        d.text((12,y+102),f"custom bbox {cm['bbox']}",font=font,fill=(205,205,205))
    return sheet


def render_rationalism(icon):
    font=ImageFont.load_default(size=15)
    im=Image.new('RGB',(760,330),(45,48,52)); d=ImageDraw.Draw(im)
    d.text((14,12),'Rationalism city-icon regression preview - transparent tint-safe glyph',font=font,fill='white')
    d.text((14,35),'Large source plus simulated 20px city-label rendering. No filled background disc is present.',font=font,fill=(220,220,220))
    im.paste(icon,(40,80),icon); d.rectangle((40,80,167,207),outline=(180,180,180))
    samples=[('light',(230,230,225),(35,35,35)),('dark',(38,45,52),(245,245,245)),('green',(69,91,54),(245,245,245)),('gold',(184,145,75),(20,30,38))]
    x=220
    for label,bg,tint in samples:
        d.rounded_rectangle((x,100,x+115,150),radius=8,fill=bg)
        small=icon.resize((20,20),Image.Resampling.LANCZOS)
        rgba=Image.new('RGBA',small.size,tint+(0,)); rgba.putalpha(small.getchannel('A'))
        im.paste(rgba,(x+48,115),rgba)
        d.text((x+33,165),label,font=font,fill='white')
        x+=130
    return im


def main():
    b.ensure_native_reference()
    assets,_,_=b.atlas_read('v029')
    b.PREVIEWS.mkdir(parents=True,exist_ok=True)
    for ts in b.SETS:
        render_set(ts,assets).save(b.PREVIEWS/(ts+'-native-comparison.png'))
    render_rationalism(assets['ReligionIcons/Rationalism']).save(b.PREVIEWS/'Rationalism-city-icon.png')

if __name__=='__main__': main()
