#!/usr/bin/env python3
"""Audit the generated compositions against the frozen rules:
 - every number shown on screen is in the allowed set (from model/site_data.json via the visual plan);
 - no em dash (U+2014) or en dash (U+2013) and no explainer label in any composition file, index.html, script.json or the VTT;
 - every font-size is at least 44px.
Exit code 1 on any violation."""
import glob, json, os, re, sys
here = os.path.dirname(os.path.abspath(__file__))
ALLOWED = {'90%', '5%', '$4.0M', '$250K', '$800K', '$600K', '1.33x', '4.5x', '4.0x', '4x', '$671K', '1.19x', '$1.25M', '$1.0M',
           '$5.0M', '-$500K', '21x', '35%', '$0', 'Day 1', 'Week 13'}
bad = []
seen = []
for p in sorted(glob.glob(os.path.join(here, 'compositions', '*.html'))):
    html = open(p).read()
    body = re.sub(r'<style.*?</style>|<script.*?</script>', '', html, flags=re.S)
    # visible text = text between tags (svg paths carry no text)
    texts = [t.strip() for t in re.findall(r'>([^<>]+)<', body) if t.strip()]
    for t in texts:
        t = t.replace('&#8217;', "'")
        found = re.findall(r'(?:Day|Week) \d+|[-+]?\$?\d[\d,]*(?:\.\d+)?[KMx%]?', t)
        for f in found:
            f = f.lstrip('+')
            seen.append((os.path.basename(p), f, t))
            if f not in ALLOWED: bad.append(('number not in the allowed set', os.path.basename(p), f, t))
    for m in re.finditer(r'font-size:\s*(\d+)px', html):
        if int(m.group(1)) < 44: bad.append(('font-size < 44', os.path.basename(p), m.group(0)))
files = glob.glob(os.path.join(here, 'compositions', '*.html')) + [os.path.join(here, 'index.html'), os.path.join(here, 'script.json'),
                                                                   os.path.join(here, '..', 'docs', 'media', 'lbo.vtt')]
for p in files:
    if not os.path.exists(p): continue
    s = open(p).read()
    for ch, name in (('\u2014', 'em dash'), ('\u2013', 'en dash')):
        if ch in s: bad.append((name, os.path.basename(p)))
    if re.search(r'eli\s?5|expl' r'ain\s+like', s, re.I): bad.append(('explainer label', os.path.basename(p)))
nums = sorted({f for _, f, _ in seen})
print('numbers on screen:', nums)
print('allowed but not used:', sorted(ALLOWED - set(nums)))
for b in bad: print('VIOLATION', b)
print('OK' if not bad else 'FAILED')
sys.exit(1 if bad else 0)
