#!/usr/bin/env python3
"""Snapshot helper: snap.py s1:2.2 s2:12.0 ...  (scene-relative seconds) -> build/snaps/*.png and labelled 2x2 contact sheets
in build/sheets/. Uses the pinned hyperframes CLI. Nothing leaves the machine."""
import json, os, shutil, subprocess, sys
from PIL import Image, ImageDraw
here = os.path.dirname(os.path.abspath(__file__))
T = {x['id']: x for x in json.load(open(os.path.join(here, 'build/timing.json')))['scenes']}
pairs = []
for a in sys.argv[1:]:
    sid, t = a.split(':'); pairs.append((sid, float(t), round(T[sid]['start'] + float(t), 3)))
abs_times = ','.join(str(p[2]) for p in pairs)
out = os.path.join(here, 'build', 'snaps')
shutil.rmtree(out, ignore_errors=True)
subprocess.run(['npx', '--yes', 'hyperframes@0.9.19', 'snapshot', '--at', abs_times, '--no-end', '--keep', '-o', out],
               cwd=here, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def fname(t):
    s = ('%g' % t)
    return os.path.join(out, 'at-%ss.png' % s)
os.makedirs(os.path.join(here, 'build', 'sheets'), exist_ok=True)
W, H = 960, 540
for k in range(0, len(pairs), 4):
    group = pairs[k:k + 4]
    im = Image.new('RGB', (W * 2, H * 2), 'white')
    for i, (sid, rel, ab) in enumerate(group):
        f = Image.open(fname(ab)).convert('RGB').resize((W, H), Image.LANCZOS)
        d = ImageDraw.Draw(f); d.rectangle((0, 0, 190, 30), fill=(0, 0, 0)); d.text((8, 8), '%s +%.1fs (abs %.1f)' % (sid, rel, ab), fill=(255, 255, 255))
        im.paste(f, ((i % 2) * W, (i // 2) * H))
    p = os.path.join(here, 'build', 'sheets', 'sheet%d.jpg' % (k // 4 + 1)); im.save(p, quality=86)
    print(p, [(g[0], g[1]) for g in group])
