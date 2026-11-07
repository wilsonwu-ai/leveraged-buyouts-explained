#!/usr/bin/env python3
"""Local Whisper (openai-whisper, medium) over each trimmed scene clip: word timings plus a word-level match
against the spoken script text ("vo"). Writes build/whisper.json. No network: model weights are cached locally.
Usage: whisper_check.py [model] [scene ids...]"""
import json, os, sys, difflib, whisper
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from textnorm import norm
S = json.load(open(os.path.join(here, 'script.json')))
model_name = sys.argv[1] if len(sys.argv) > 1 else 'medium'
only = sys.argv[2:]
model = whisper.load_model(model_name)
path = os.path.join(here, 'build/whisper.json')
res = json.load(open(path)) if (only and os.path.exists(path)) else {}
for sc in S['scenes']:
    if only and sc['id'] not in only: continue
    p = os.path.join(here, 'build/audio/trim', sc['id'] + '.wav')
    r = model.transcribe(p, language='en', word_timestamps=True, condition_on_previous_text=False, fp16=False,
                         initial_prompt='Leveraged buyout, seller note, coverage, illustrative company, operating profit.')
    words = [(w['word'].strip(), w['start'], w['end']) for seg in r['segments'] for w in seg['words']]
    hyp = norm(r['text']); ref = norm(sc['vo'])
    sm = difflib.SequenceMatcher(a=ref, b=hyp, autojunk=False)
    matched = sum(b.size for b in sm.get_matching_blocks())
    pct = 100.0 * matched / max(1, len(ref))
    res[sc['id']] = {'match_pct': round(pct, 1), 'whisper': r['text'].strip(), 'words': words,
                     'ref_tokens': len(ref), 'hyp_tokens': len(hyp)}
    print(sc['id'], round(pct, 1), '|', r['text'].strip(), flush=True)
    if pct < 100:
        for op, a0, a1, b0, b1 in sm.get_opcodes():
            if op != 'equal': print('     diff', op, 'script:', ref[a0:a1], 'whisper:', hyp[b0:b1])
json.dump(res, open(path, 'w'), indent=1)
