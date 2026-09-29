"""Render v0.2.9 native-comparison QA sheets from the packed atlas."""
from PIL import Image,ImageDraw,ImageFont
from build_assets import ROOT,atlas_read,UNITS,SETS,choose_native_reference,alpha_stats

def draw_canvas(draw,x,y,w,h):
    draw.rectangle((x,y,x+w-1,y+h-1),outline=(180,180,180))
    cx=x+w//2
    draw.line((cx,y,cx,y+h-1),fill=(120,120,120))

def paste_centered(sheet,im,x,y,w,h):
    sheet.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2),im)

def main():
    assets,_=atlas_read(ROOT)
    out=ROOT/'tools/v029/previews'; out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.load_default(size=13)

    # Native-scale comparison: every custom unit beside the native reference that supplied its anchor.
    row_h=92; label_w=210; cell_w=150
    sheet=Image.new('RGB',(label_w+cell_w*6+20,row_h*len(UNITS)+42),(38,42,46))
    d=ImageDraw.Draw(sheet)
    d.text((8,8),'Veilfall v0.2.9 — custom/native comparison at actual atlas scale. Gray line = canvas center.',font=font,fill='white')
    for r,name in enumerate(UNITS):
        y=34+r*row_h
        d.text((8,y+8),name,font=font,fill='white')
        for c,ts in enumerate(SETS):
            custom=assets[f'TileSets/{ts}/Units/{name}']
            ref_name,ref,_,_=choose_native_reference(name,ts)
            x=label_w+c*cell_w*2
            d.text((x,y),f'{ts} custom',font=font,fill='white')
            draw_canvas(d,x,y+18,custom.width,custom.height)
            sheet.paste(custom,(x,y+18),custom)
            x2=x+cell_w
            d.text((x2,y),f'native {ref_name}',font=font,fill='white')
            draw_canvas(d,x2,y+18,ref.width,ref.height)
            sheet.paste(ref,(x2,y+18),ref)
    sheet.save(out/'native-comparison.png')

    # Enlarged nearest-neighbor inspection with center deltas printed for placement review.
    z=4; row_h=250; cell_w=280
    zoom=Image.new('RGB',(cell_w*3+20,row_h*len(UNITS)+42),(38,42,46))
    dz=ImageDraw.Draw(zoom)
    dz.text((8,8),'Veilfall v0.2.9 — 4x nearest-neighbor inspection; native-scale sheet is authoritative for perceived size.',font=font,fill='white')
    for r,name in enumerate(UNITS):
        y=34+r*row_h
        for c,ts in enumerate(SETS):
            custom=assets[f'TileSets/{ts}/Units/{name}']
            ref_name,ref,refst,_=choose_native_reference(name,ts)
            st=alpha_stats(custom)
            x=8+c*cell_w
            dz.text((x,y),f'{name} / {ts}',font=font,fill='white')
            dz.text((x,y+15),f'custom dx {st["center_delta_x"]:.2f} | native {ref_name} dx {refst["center_delta_x"]:.2f}',font=font,fill='white')
            big=custom.resize((custom.width*z,custom.height*z),Image.Resampling.NEAREST)
            bx=x; by=y+36
            dz.rectangle((bx,by,bx+big.width-1,by+big.height-1),outline=(180,180,180))
            cx=bx+big.width//2
            dz.line((cx,by,cx,by+big.height-1),fill=(120,120,120))
            zoom.paste(big,(bx,by),big)
    zoom.save(out/'sprite-offset-inspection.png')

if __name__=='__main__': main()
