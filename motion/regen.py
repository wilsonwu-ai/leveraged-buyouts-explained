#!/usr/bin/env python3
"""Re-generate scenes whose narration does not match the script (gpt-4o-mini-tts sometimes drops a final
sentence). Each attempt calls tts.py for that scene, transcribes the raw clip locally with Whisper, and keeps
the best take; stops at a 100% word match. Usage: regen.py s3 [s5 ...]   (max 6 attempts per scene)"""
import json, os, shutil, subprocess, sys, difflib, whisper
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from textnorm import norm
S = {s['id']: s for s in json.load(open(os.path.join(here, 'script.json')))['scenes']}
model = whisper.load_model('medium')
tmp = os.path.join(here, 'build', 'regen'); os.makedirs(tmp, exist_ok=True)
for sid in sys.argv[1:]:
    ref = norm(S[sid]['vo']); best = (-1.0, None)
    for attempt in range(1, 7):
        subprocess.run([sys.executable, os.path.join(here, 'tts.py'), sid], check=True, stdout=subprocess.DEVNULL)
        src = os.path.join(here, 'build', 'audio', sid + '.wav')
        take = os.path.join(tmp, '%s_take%d.wav' % (sid, attempt)); shutil.copy(src, take)
        w16 = os.path.join(tmp, sid + '_16k.wav')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-ac', '1', '-ar', '16000', w16], check=True)
        r = model.transcribe(w16, language='en', condition_on_previous_text=False, fp16=False,
                             initial_prompt='Leveraged buyout, seller note, coverage, illustrative company, operating profit.')
        hyp = norm(r['text'])
        m = sum(b.size for b in difflib.SequenceMatcher(a=ref, b=hyp, autojunk=False).get_matching_blocks())
        pct = 100.0 * m / len(ref)
        print(sid, 'attempt', attempt, round(pct, 1), '|', r['text'].strip(), flush=True)
        if pct > best[0]: best = (pct, take)
        if pct >= 100.0: break
    shutil.copy(best[1], os.path.join(here, 'build', 'audio', sid + '.wav'))
    print(sid, 'kept take with', round(best[0], 1), '%', flush=True)
