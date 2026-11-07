#!/usr/bin/env python3
"""Tighten each scene's TTS (trim edges, shorten long pauses), then lay the scenes on one timeline.
Writes build/audio/trim/<id>.wav, build/narration.wav (48 kHz mono), assets/narration.wav and build/timing.json.

The streamed TTS WAVs carry a placeholder length in the header, so the PCM payload is read straight from the
'data' chunk to the end of the file."""
import json, os, struct, wave, numpy as np
here = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(here, 'script.json')))
LEAD, TAIL, LAST_TAIL = 0.35, 0.40, 3.2
# hold the picture a little longer where the key reveal lands on the last words of the scene
TAILS = {'s1': 0.45, 's2': 0.70, 's3': 0.90, 's4': 1.20, 's5': 0.90, 's6': 0.80, 's7': 0.90}
THR_DB, MIN_PAUSE, KEEP_PAUSE = -42.0, 0.30, 0.24
os.makedirs(os.path.join(here, 'build/audio/trim'), exist_ok=True)

def read(p):
    raw = open(p, 'rb').read()
    assert raw[:4] == b'RIFF' and raw[8:12] == b'WAVE'
    pos, sr, ch, bits = 12, None, None, None
    while pos + 8 <= len(raw):
        cid = raw[pos:pos + 4]; size = struct.unpack('<I', raw[pos + 4:pos + 8])[0]
        if cid == b'fmt ':
            _, ch, sr, _, _, bits = struct.unpack('<HHIIHH', raw[pos + 8:pos + 24])
        elif cid == b'data':
            pcm = raw[pos + 8:]
            pcm = pcm[:len(pcm) - (len(pcm) % 2)]
            assert ch == 1 and bits == 16 and sr == 24000, (ch, bits, sr)
            return np.frombuffer(pcm, dtype='<i2').astype(np.float32) / 32768.0, sr
        pos += 8 + size + (size & 1)
    raise SystemExit('no data chunk in ' + p)

def write(p, a, sr):
    w = wave.open(p, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(a, -1, 1) * 32767).astype('<i2').tobytes()); w.close()

def tighten(a, sr):
    win = int(0.01 * sr); n = len(a) // win
    rms = np.sqrt((a[:n * win].reshape(n, win) ** 2).mean(axis=1) + 1e-12)
    loud = 20 * np.log10(rms) > THR_DB
    idx = np.where(loud)[0]
    first, last = idx[0], idx[-1]
    pad = 6  # 60 ms
    seg = loud[first:last + 1]; out = []; i = 0
    while i < len(seg):
        j = i
        while j < len(seg) and seg[j] == seg[i]: j += 1
        chunk = a[(first + i) * win:(first + j) * win]
        if (not seg[i]) and (j - i) * 0.01 > MIN_PAUSE:
            keep = int(KEEP_PAUSE * sr); h = keep // 2
            chunk = np.concatenate([chunk[:h], chunk[-(keep - h):]])
        out.append(chunk); i = j
    body = np.concatenate(out)
    fade = int(0.012 * sr)
    body[:fade] *= np.linspace(0, 1, fade); body[-fade:] *= np.linspace(1, 0, fade)
    return np.concatenate([np.zeros(pad * win), body, np.zeros(pad * win)])

timing = []; t = 0.0; sr_out = 48000; tracks = []
for k, sc in enumerate(S['scenes']):
    a, sr = read(os.path.join(here, 'build/audio', sc['id'] + '.wav'))
    raw_dur = len(a) / sr
    a = tighten(a, sr)
    write(os.path.join(here, 'build/audio/trim', sc['id'] + '.wav'), a, sr)
    # 24 kHz -> 48 kHz (linear interpolation is fine for speech)
    x = np.arange(len(a) * 2) / 2.0
    a48 = np.interp(x, np.arange(len(a)), a).astype(np.float32)
    dur_a = len(a48) / sr_out
    tail = LAST_TAIL if k == len(S['scenes']) - 1 else TAILS.get(sc['id'], TAIL)
    dur = LEAD + dur_a + tail
    timing.append({'id': sc['id'], 'start': round(t, 3), 'dur': round(dur, 3),
                   'audio_start': round(t + LEAD, 3), 'audio_dur': round(dur_a, 3), 'raw_dur': round(raw_dur, 3)})
    tracks.append((t + LEAD, a48)); t += dur
total = t
master = np.zeros(int(round(total * sr_out)) + 1, dtype=np.float32)
for st, a48 in tracks:
    i = int(round(st * sr_out)); master[i:i + len(a48)] += a48
write(os.path.join(here, 'build/narration.wav'), master, sr_out)
os.makedirs(os.path.join(here, 'assets'), exist_ok=True)
write(os.path.join(here, 'assets/narration.wav'), master, sr_out)
json.dump({'total': round(total, 3), 'scenes': timing}, open(os.path.join(here, 'build/timing.json'), 'w'), indent=1)
print(json.dumps({'total': round(total, 2), 'audio_total': round(sum(x['audio_dur'] for x in timing), 2),
                  'raw_total': round(sum(x['raw_dur'] for x in timing), 2)}))
for x in timing: print(x)
