#!/usr/bin/env python3
"""Cut each scene out of the FINAL mp4's audio track, transcribe it locally with Whisper, and score it against the spoken
script text ("vo"). Usage: whisper_final.py [model] [path/to/video.mp4]   (default: medium, ../docs/media/lbo.mp4)."""
import json, os, subprocess, sys, difflib, whisper
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from textnorm import norm
S = json.load(open(os.path.join(here, 'script.json')))
T = {x['id']: x for x in json.load(open(os.path.join(here, 'build/timing.json')))['scenes']}
model = whisper.load_model(sys.argv[1] if len(sys.argv) > 1 else 'medium')
mp4 = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, '..', 'docs', 'media', 'lbo.mp4')
os.makedirs(os.path.join(here, 'build/final'), exist_ok=True)
tot_ref = tot_ok = 0
for sc in S['scenes']:
    t = T[sc['id']]; out = os.path.join(here, 'build/final', sc['id'] + '.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(t['start']), '-t', str(t['dur']), '-i', mp4,
                    '-vn', '-ac', '1', '-ar', '16000', out], check=True)
    r = model.transcribe(out, language='en', condition_on_previous_text=False, fp16=False,
                         initial_prompt='Leveraged buyout, seller note, coverage, illustrative company, operating profit.')
    ref, hyp = norm(sc['vo']), norm(r['text'])
    sm = difflib.SequenceMatcher(a=ref, b=hyp, autojunk=False)
    m = sum(b.size for b in sm.get_matching_blocks())
    tot_ref += len(ref); tot_ok += m
    print(sc['id'], round(100 * m / len(ref), 1), '|', r['text'].strip(), flush=True)
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op != 'equal': print('     diff', op, 'script:', ref[a0:a1], 'whisper:', hyp[b0:b1])
print('overall', round(100 * tot_ok / tot_ref, 1))
