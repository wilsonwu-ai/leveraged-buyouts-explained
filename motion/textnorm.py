"""Shared text normaliser: turns script text or a Whisper transcript into comparable word tokens.
Spoken numbers and digits meet in the middle ("one point three three" == "1.33", "$800,000" == "eight hundred
thousand dollars"), so the word-level match measures what was said, not how Whisper chose to write it."""
import re

ONES = ('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen '
        'sixteen seventeen eighteen nineteen').split()
TENS = {2: 'twenty', 3: 'thirty', 4: 'forty', 5: 'fifty', 6: 'sixty', 7: 'seventy', 8: 'eighty', 9: 'ninety'}


def int_words(n):
    if n < 20: return [ONES[n]]
    if n < 100: return [TENS[n // 10]] + ([ONES[n % 10]] if n % 10 else [])
    if n < 1000: return [ONES[n // 100], 'hundred'] + (int_words(n % 100) if n % 100 else [])
    if n < 1000000: return int_words(n // 1000) + ['thousand'] + (int_words(n % 1000) if n % 1000 else [])
    if n < 1000000000: return int_words(n // 1000000) + ['million'] + (int_words(n % 1000000) if n % 1000000 else [])
    return [str(n)]


def num_tokens(tok):
    m = re.fullmatch(r'(\d+)(?:\.(\d+))?', tok)
    if not m: return [tok]
    out = int_words(int(m.group(1)))
    if m.group(2): out += ['point'] + [ONES[int(c)] for c in m.group(2)]
    return out


def norm(text):
    text = text.lower().replace('%', ' percent ').replace('$', ' ')
    text = text.replace('’', "'")
    text = re.sub(r'(\d),(\d)', r'\1\2', text)                      # 800,000 -> 800000
    text = re.sub(r'(\d+(?:\.\d+)?)\s*x\b', r'\1 times', text)      # 1.33x -> 1.33 times
    text = re.sub(r'(\d+(?:\.\d+)?)\s*k\b', r'\1 thousand', text)   # 800k -> 800 thousand
    text = re.sub(r'(\d+(?:\.\d+)?)\s*m\b', r'\1 million', text)    # 4m -> 4 million
    text = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1 to \2', text)
    text = re.sub(r"[^a-z0-9. ']", ' ', text.replace('-', ' '))
    text = re.sub(r'\.(?!\d)', ' ', text)
    toks = []
    for t in text.split():
        t = t.strip('.').strip("'")
        if t: toks += num_tokens(t)
    s = ' '.join(toks)
    s = s.replace('and a half', 'point five').replace('and one half', 'point five')
    s = s.replace("company's", 'companys').replace("isn't", 'isnt').replace("that's", 'thats').replace("bank's", 'banks')
    s = s.replace("buyer's", 'buyers').replace("seller's", 'sellers')
    toks = [x for x in s.split() if x not in ('dollars', 'dollar')]
    return toks
