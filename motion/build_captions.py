#!/usr/bin/env python3
"""WebVTT from the approved caption text (script.json "caption" fields), timed to the real narration:
each caption word is aligned to the local Whisper word timings (build/whisper.json) and offset to the scene's position
in the final timeline (build/timing.json). Writes ../docs/media/lbo.vtt."""
import json, os, re, difflib, sys
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from textnorm import norm
S = json.load(open(os.path.join(here, 'script.json')))
T = {x['id']: x for x in json.load(open(os.path.join(here, 'build/timing.json')))['scenes']}
W = json.load(open(os.path.join(here, 'build/whisper.json')))


def toks_with_owner(words):
    toks, own = [], []
    for i, w in enumerate(words):
        for t in norm(w):
            toks.append(t); own.append(i)
    return toks, own


def fmt(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return '%02d:%02d:%06.3f' % (h, m, s)


BREAK_BEFORE = {'with', 'that', 'and', 'against', 'before', 'at', 'if', 'to', 'in', 'for', 'of', 'because', 'so', 'but', 'or'}


def split_line(words, idx, limit=64):
    """recursively split one caption line: prefer a comma, then a break before a conjunction or preposition, near the middle."""
    text = ' '.join(words[i] for i in idx)
    if len(text) <= limit or len(idx) < 4: return [idx]
    mid = len(text) / 2
    best = None
    for j in range(1, len(idx) - 1):                       # split after position j
        head = len(' '.join(words[i] for i in idx[:j + 1]))
        if words[idx[j]].endswith(','): score = abs(head - mid) - 30
        elif words[idx[j + 1]].lower().strip(',.') in BREAK_BEFORE: score = abs(head - mid)
        else: score = abs(head - mid) + 40
        if best is None or score < best[0]: best = (score, j)
    j = best[1]
    return split_line(words, idx[:j + 1], limit) + split_line(words, idx[j + 1:], limit)


def chunks(words):
    """sentence-sized caption lines of at most ~64 characters"""
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        if re.search(r'[.?!]$', w):
            out.append(cur); cur = []
    if cur: out.append(cur)
    res = []
    for c in out: res += split_line(words, c)
    return res


cues = []
for sc in S['scenes']:
    words = sc['caption'].split()
    ct, co = toks_with_owner(words)
    wh = W[sc['id']]['words']
    ht, ho = toks_with_owner([w[0] for w in wh])
    sm = difflib.SequenceMatcher(a=ct, b=ht, autojunk=False)
    start = [None] * len(words); end = [None] * len(words)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            ci, hi = co[blk.a + k], ho[blk.b + k]
            if start[ci] is None: start[ci] = wh[hi][1]
            end[ci] = wh[hi][2]
    last_t = 0.0                          # words with no Whisper counterpart borrow the neighbouring times
    for i in range(len(words)):
        if start[i] is None:
            j = i
            while j < len(words) and start[j] is None: j += 1
            nxt = start[j] if j < len(words) else wh[-1][2]
            start[i] = last_t; end[i] = nxt
        last_t = end[i]
    base = T[sc['id']]['audio_start']
    for c in chunks(words):
        cues.append([base + start[c[0]], base + end[c[-1]] + 0.12, ' '.join(words[i] for i in c)])
for k in range(len(cues) - 1):            # clamp each end to the next start; hold at least 0.4 s
    if cues[k][1] > cues[k + 1][0] - 0.02: cues[k][1] = cues[k + 1][0] - 0.02
    if cues[k][1] < cues[k][0] + 0.4: cues[k][1] = min(cues[k][0] + 0.4, cues[k + 1][0] - 0.02)
out = 'WEBVTT\n\n' + '\n'.join('%d\n%s --> %s\n%s\n' % (i + 1, fmt(a), fmt(b), t) for i, (a, b, t) in enumerate(cues))
assert '\u2014' not in out and '\u2013' not in out
dest = os.path.join(here, '..', 'docs', 'media', 'lbo.vtt')
os.makedirs(os.path.dirname(dest), exist_ok=True)
open(dest, 'w').write(out)
print(out)
