#!/usr/bin/env python3
"""Generate per-scene narration with OpenAI gpt-4o-mini-tts (voice marin).

Only the script's "vo" text and the style instructions are sent, to the OpenAI speech endpoint and nowhere else.
The API key is read from the OPENAI_API_KEY environment variable and is never printed, logged or written to disk.
Usage: tts.py            (all scenes)
       tts.py s3 s5      (only those scenes)
"""
import json, os, sys, time, wave, io, urllib.request, urllib.error

here = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(here, 'script.json')))
only = sys.argv[1:]
key = os.environ.get('OPENAI_API_KEY')
if not key:
    sys.exit('OPENAI_API_KEY is not set in the environment: stopping.')
URL = 'https://api.openai.com/v1/audio/speech'
out_dir = os.path.join(here, 'build', 'audio')
os.makedirs(out_dir, exist_ok=True)

def synth(text):
    body = json.dumps({'model': S['model'], 'voice': S['voice'], 'input': text,
                       'instructions': S['instructions'], 'response_format': 'wav',
                       'speed': S['speed']}).encode()
    last = None
    for attempt in range(4):
        req = urllib.request.Request(URL, data=body, headers={
            'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            # Never echo the response message: a 401 body contains a masked copy of the key.
            try:
                err = json.loads(e.read().decode('utf-8', 'replace')).get('error', {})
                last = 'HTTP %s type=%s code=%s' % (e.code, err.get('type'), err.get('code'))
            except Exception:
                last = 'HTTP %s' % e.code
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 + 3 * attempt); continue
            break
        except Exception as e:  # network or timeout
            last = type(e).__name__
            time.sleep(2 + 3 * attempt)
    sys.exit('speech request failed: %s' % last)

for sc in S['scenes']:
    if only and sc['id'] not in only:
        continue
    data = synth(sc['vo'])
    w = wave.open(io.BytesIO(data))
    assert w.getnchannels() == 1 and w.getsampwidth() == 2 and w.getframerate() == 24000, \
        (w.getnchannels(), w.getsampwidth(), w.getframerate())
    open(os.path.join(out_dir, sc['id'] + '.wav'), 'wb').write(data)
    # the streamed WAV header carries a placeholder length, so measure from the byte count
    print(sc['id'], len(data), 'bytes', round((len(data) - 44) / 48000.0, 2), 's', flush=True)
