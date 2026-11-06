#!/usr/bin/env python3
"""Rebuild approved Veilfall drone atlas from retained transparent masters.

Requires Pillow (no external image generator). --check compares rebuilt pixels
and atlas text with the committed files without overwriting them.
"""
import argparse
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = Path(__file__).resolve().parent
SOURCES = {
    'Horizon-class Recon Drone': ASSET_DIR / 'Horizon-class Recon Drone - transparent master.png',
    'Valkyrie-class Assault Drone': ASSET_DIR / 'Valkyrie-class Assault Drone - transparent master.png',
}
SETS = ('Minimal', 'HexaRealm', 'FantasyHex')
RESAMPLING = Image.Resampling


def map_frame(source):
    width, height = source.size
    scale = min(184 / width, 105 / height)
    scaled = source.resize((max(1, round(width * scale)), max(1, round(height * scale))), RESAMPLING.LANCZOS)
    scaled.putalpha(scaled.getchannel('A').point(lambda v: 255 if v >= 128 else 0))
    scaled = scaled.crop(scaled.getchannel('A').getbbox())
    frame = Image.new('RGBA', (256, 224))
    frame.paste(scaled, ((256 - scaled.width) // 2, 186 - scaled.height), scaled)
    frame.putalpha(frame.getchannel('A').point(lambda v: 255 if v >= 128 else 0))
    return frame


def centered_icon(source, size):
    frame = Image.new('RGBA', (size, size))
    target = (int(size * .86), int(size * .67)) if size == 128 else (int(size * .90), int(size * .70))
    scale = min(target[0] / source.width, target[1] / source.height)
    scaled = source.resize((round(source.width * scale), round(source.height * scale)), RESAMPLING.LANCZOS)
    frame.alpha_composite(scaled, ((size - scaled.width) // 2, (size - scaled.height) // 2))
    return frame


def build():
    entries = {}
    for name, source_path in SOURCES.items():
        source = Image.open(source_path).convert('RGBA')
        for tileset in SETS:
            entries[f'TileSets/{tileset}/Units/{name}'] = map_frame(source)
        entries[f'UnitIcons/{name}'] = centered_icon(source, 128)
        entries[f'UnitPortraits/{name}'] = centered_icon(source, 256)

    atlas = Image.new('RGBA', (1024, 1024))
    lines = ['drone-review.png', 'size: 1024, 1024', 'format: RGBA8888', 'filter: Nearest, Nearest', 'repeat: none']
    x = y = 4
    row_h = 0
    for key, img in sorted(entries.items()):
        width, height = img.size
        if x + width + 4 > 1024:
            x = 4
            y += row_h + 8
            row_h = 0
        if y + height + 4 > 1024:
            raise ValueError(f'Atlas overflow: {key}')
        atlas.alpha_composite(img, (x, y))
        lines += [key, '  rotate: false', f'  xy: {x}, {y}', f'  size: {width}, {height}', f'  orig: {width}, {height}', '  offset: 0, 0', '  index: -1']
        x += width + 8
        row_h = max(row_h, height)
    return atlas, '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--target', type=Path, default=ROOT)
    args = parser.parse_args()
    image, atlas_text = build()
    dst_img, dst_atlas = args.target / 'drone-review.png', args.target / 'drone-review.atlas'
    if args.check:
        assert dst_atlas.read_text() == atlas_text, 'Atlas index differs'
        current = Image.open(dst_img).convert('RGBA')
        assert current.size == image.size, 'Atlas dimensions differ'
        assert current.tobytes() == image.tobytes(), 'Packed atlas pixels differ'
        print('PASS: atlas index and all 1024x1024 RGBA pixels match')
    else:
        dst_img.write_bytes(b'') if False else None
        image.save(dst_img, optimize=True)
        dst_atlas.write_text(atlas_text)
        print(f'Wrote {dst_img} and {dst_atlas}')


if __name__ == '__main__':
    main()
