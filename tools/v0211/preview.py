"""Exact packed before/after/native geometry comparison (nearest-neighbor zoom)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys, subprocess
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v029'))
import build_assets as b
BASELINE='29ab0a98eb8443810b91d41a07ad221f2b1f953e'

def main():
    old=lambda p:subprocess.check_output(['git','show',BASELINE+':'+p],cwd=b.ROOT)
    before,_=b.parse_atlas(old('v021.atlas'),old('v021.png'),'v021.png')
    after,_=b.atlas_read(b.ROOT)
    sheet=Image.new('RGB',(1020,6*255+45),(34,39,44))
    draw=ImageDraw.Draw(sheet); font=ImageFont.load_default(size=14)
    draw.text((12,10),'v0.2.11 | accepted v0.2.10 / corrected / native Infantry | 3x pixel zoom + actual-size inset',font=font,fill='white')
    row=0
    for name in ['Continental Marines','Expeditionary Marines']:
        for ts in b.SETS:
            key=f'TileSets/{ts}/Units/{name}'
            native=b.choose_native_reference(name,ts)[1]
            y=45+row*255; draw.text((12,y),f'{name} / {ts}',font=font,fill='white')
            for col,(label,im) in enumerate([('v0.2.10',before[key]),('v0.2.11',after[key]),('Native Infantry',native)]):
                x=12+col*340; st=b.alpha_stats(im)
                draw.text((x,y+23),f'{label}: {st["w"]}x{st["h"]}; dx={st["center_delta_x"]:.2f}',font=font,fill='white')
                big=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST)
                draw.rectangle((x,y+48,x+big.width,y+48+big.height),outline=(110,118,125))
                draw.line((x+big.width//2,y+48,x+big.width//2,y+48+big.height),fill=(70,77,84))
                sheet.paste(big,(x,y+48),big)
                sheet.paste(im,(x+215,y+70),im)
            row+=1
    sheet.save(b.ROOT/'tools/v0211/proportion-comparison.png')
if __name__=='__main__': main()
