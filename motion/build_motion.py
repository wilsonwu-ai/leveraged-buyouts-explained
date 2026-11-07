#!/usr/bin/env python3
"""Generate the HyperFrames project (index.html + compositions/s1..s8.html) from script.json,
build/timing.json (scene lengths from the real audio) and build/whisper.json (word cues).

Every number drawn on screen comes from model/site_data.json (asserted below) and is audited by check_numbers.py.
No em dashes or en dashes, and no explainer labels. Numbers swap, they never count through in-between values.
Type: Fraunces for titles, Inter for labels AND numbers (Fraunces draws 0 like the letter O)."""
import json, os, re
from PIL import ImageFont

here = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(here, 'script.json')))
T = json.load(open(os.path.join(here, 'build/timing.json')))
W = json.load(open(os.path.join(here, 'build/whisper.json')))
DATA = json.load(open(os.path.join(here, '..', 'model', 'site_data.json')))
LEAD = 0.35
TIM = {x['id']: x for x in T['scenes']}

# NUMBERS (site_data.json, as of 7 Nov 2026):
#   stack.a: price 4,000,000 ($4.0M), closing_and_reserve 250,000 ($250K), sba 90%, standby seller note 5%, buyer cash 5%
#   cfads 800,000 ($800K); stack.a annual_sba_payment 600,235 ($600K), dscr 1.3328 (1.33x), passes
#   sens[4.5x]: payment 670,851 ($671K), dscr 1.1925 (1.19x), fails
#   qoe: claimed 1,250,000 ($1.25M), verified 1,000,000 ($1.0M), gap 250,000 ($250K), price on claimed 5.0M, on verified 4.0M,
#        overpay 1,000,000 ($1.0M), multiple 4.0
#   day1: 14 weekly points (week 0..13), low_point_no_ar -500,039 (-$500K), cash_needed_no_ar 600,039 (about $600K)
#   scenarios: base moic_proceeds_only 21.04 (about 21x), break (earnings fall 35%) buyer_cash_back 0 ($0)
st, sens = DATA['stack']['a'], {round(x['multiple'], 2): x for x in DATA['sens']}
assert round(st['price']) == 4000000 and round(st['closing_and_reserve']) == 250000
assert round(st['sba_share_of_project_pct']) == 90 and round(st['buyer_cash'] / st['project_cost'] * 100) == 5
assert round(st['standby_seller_note'] / st['project_cost'] * 100) == 5
assert round(st['cfads'] / 1000) == 800 and round(st['annual_sba_payment'] / 1000) == 600 and round(st['dscr'], 2) == 1.33
assert round(sens[4.5]['annual_sba_payment'] / 1000) == 671 and round(sens[4.5]['dscr'], 2) == 1.19 and not sens[4.5]['passes']
q = DATA['qoe']
assert q['claimed_ebitda'] == 1250000 and q['verified_ebitda'] == 1000000 and q['gap'] == 250000
assert round(q['price_on_claimed']) == 5000000 and round(q['price_on_verified']) == 4000000 and round(q['overpay']) == 1000000
d1 = DATA['day1']
assert round(d1['low_point_no_ar'] / 1000) == -500 and round(d1['cash_needed_no_ar'] / 1000) == 600
assert round(DATA['scenarios']['base']['moic_proceeds_only']) == 21
assert DATA['scenarios']['break']['buyer_cash_back'] == 0 and DATA['scenarios']['break']['year1_shock_pct'] == -35.0


def nrm(w): return re.sub(r'[^a-z0-9]', '', w.lower())


def cue(sid, word, n=1, off=-0.10):
    """scene-relative start time (s) of the n-th spoken occurrence of `word`, plus an offset (visuals lead slightly)."""
    k = 0
    for (w, s, e) in W[sid]['words']:
        if nrm(w) == nrm(word):
            k += 1
            if k == n: return round(max(0.05, LEAD + s + off), 3)
    raise SystemExit('cue not found %s %s %d' % (sid, word, n))


def cue_end(sid, word, n=1):
    k = 0
    for (w, s, e) in W[sid]['words']:
        if nrm(w) == nrm(word):
            k += 1
            if k == n: return round(LEAD + e, 3)
    raise SystemExit('cue_end not found %s %s' % (sid, word))


# ------------------------------------------------------------------ palette
INK, MUTED, LINE, PAPER, WHITE = '#10202F', '#5B6672', '#E2DDD2', '#F6F3EC', '#FFFFFF'
LOAN, SELLER, CASH, AI, FAIL, STONE, STONE_D = '#2F5DA8', '#B07D2B', '#1E7F55', '#6B4FA0', '#B42318', '#8A7A66', '#6F6150'

FONTS = """
@font-face { font-family: 'Fraunces'; src: url('assets/fonts/fraunces-600.woff2') format('woff2'); font-weight: 600; }
@font-face { font-family: 'Inter'; src: url('assets/fonts/inter-500.woff2') format('woff2'); font-weight: 500; }
@font-face { font-family: 'Inter'; src: url('assets/fonts/inter-600.woff2') format('woff2'); font-weight: 600; }
"""
CSS = f"""
#root {{ position:absolute; inset:0; background:{PAPER}; font-family:'Inter',sans-serif; font-weight:600; color:{INK}; overflow:hidden; }}
#root .wrap {{ position:absolute; inset:0; }}
#root .h {{ font-family:'Fraunces',serif; font-weight:600; position:absolute; line-height:1.08; letter-spacing:-0.01em; white-space:nowrap; }}
#root .t {{ position:absolute; font-weight:600; white-space:nowrap; line-height:1.1; }}
#root .n {{ position:absolute; font-weight:600; white-space:nowrap; line-height:1; letter-spacing:-0.025em; }}
#root .m {{ font-weight:500; }}
#root .box {{ position:absolute; }}
"""


def scene(sid, extra_css, body, js, dur, fin=True, fout=True):
    FIN = f"tl.fromTo('#{sid}-wrap', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.25, ease: 'power2.out' }}, 0);\n" if fin else ''
    FOUT = f"tl.to('#{sid}-wrap', {{ opacity: 0, duration: 0.2, ease: 'power2.in' }}, D - 0.2);\n" if fout else ''
    return f"""<template>
<style>{FONTS}{CSS}{extra_css}</style>
<div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
<div class="wrap" id="{sid}-wrap">
{body}</div>
</div>
<script>
(function() {{
const tl = gsap.timeline({{ paused: true }});
const D = {dur};
{FIN}{FOUT}{js}window.__timelines['{sid}'] = tl;
}})();
</script>
</template>
"""


# ------------------------------------------------------------------ tween helpers (return JS lines)
def pop(sel, t, dur=0.6, y=24, ease='power2.out'):
    return f"tl.fromTo('{sel}', {{ opacity: 0, y: {y} }}, {{ opacity: 1, y: 0, duration: {dur}, ease: '{ease}' }}, {t:.3f});\n"


def fin(sel, t, dur=0.4):
    return f"tl.fromTo('{sel}', {{ opacity: 0 }}, {{ opacity: 1, duration: {dur}, ease: 'power2.out' }}, {t:.3f});\n"


def fout(sel, t, dur=0.4):
    return f"tl.to('{sel}', {{ opacity: 0, duration: {dur}, ease: 'power2.in' }}, {t:.3f});\n"


def grow(sel, t, dur, axis='y', ease='power2.out'):
    p = 'scaleY' if axis == 'y' else 'scaleX'
    return f"tl.fromTo('{sel}', {{ {p}: 0 }}, {{ {p}: 1, duration: {dur}, ease: '{ease}' }}, {t:.3f});\n"


def draw(sel, t, dur, ease='power1.inOut', off=1100):
    return f"tl.fromTo('{sel}', {{ strokeDashoffset: {off} }}, {{ strokeDashoffset: 0, duration: {dur}, ease: '{ease}' }}, {t:.3f});\n"


def swap(old, new, t, dur=0.3):
    """crossfade two stacked texts: no counting through in-between numbers."""
    return fout(old, t, 0.2) + pop(new, t + 0.2, dur, 10)


_FONTS = {}
REG = []        # (id, text, x, width, size, centered_box_width) for the layout audit


def textw(text, size, cls='t'):
    c = cls.split()
    key = ('fraunces-600' if c[0] == 'h' else ('inter-500' if 'm' in c else 'inter-600'), size)
    if key not in _FONTS:
        _FONTS[key] = ImageFont.truetype(os.path.join(here, 'build', 'fonts', key[0] + '.ttf'), size)
    w = _FONTS[key].getlength(text.replace('&#8217;', '’'))
    if c[0] == 'n': w -= 0.025 * size * len(text)
    return w


def txt(i, text, x, y, size, color=INK, cls='t', extra=''):
    REG.append((i, text, x, textw(text, size, cls), size, None))
    return f'<div class="{cls}" id="{i}" style="left:{x}px;top:{y}px;font-size:{size}px;color:{color};{extra}">{text}</div>\n'


def ctr(i, text, cx, y, size, color=INK, cls='t', w=900, extra=''):
    REG.append((i, text, cx - w // 2, textw(text, size, cls), size, w))
    return (f'<div class="{cls}" id="{i}" style="left:{cx - w // 2}px;top:{y}px;font-size:{size}px;color:{color};'
            f'width:{w}px;text-align:center;{extra}">{text}</div>\n')


def row(i, items, x, y, gap=22):
    """baseline-aligned run of text spans in one animatable box. items: (text, size, color, cls)."""
    out = (f'<div class="box" id="{i}" style="left:{x}px;top:{y}px;display:flex;align-items:baseline;gap:{gap}px;white-space:nowrap;">')
    cx = x
    for text, size, color, cls in items:
        w = textw(text, size, cls)
        REG.append((i, text, cx, w, size, None)); cx += w + gap
        out += f'<span class="{cls}" style="position:static;font-size:{size}px;color:{color};">{text}</span>'
    return out + '</div>\n'


def svg_path(i, d, color, sw, extra='', pl=1000):
    return (f'<path id="{i}" d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round" pathLength="{pl}" stroke-dasharray="{pl} {pl + 200}" stroke-dashoffset="{pl + 100}" {extra}/>')


def icon_check(i, x, y, size, color):
    return (f'<svg class="box" id="{i}" style="left:{x}px;top:{y}px;" width="{size}" height="{size}" viewBox="0 0 100 100">'
            f'<circle cx="50" cy="50" r="48" fill="{color}"/>'
            f'<path id="{i}-p" d="M 27 52 L 44 69 L 74 33" fill="none" stroke="#fff" stroke-width="11" stroke-linecap="round" '
            f'stroke-linejoin="round" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="0"/></svg>\n')


def icon_x(i, x, y, size, color):
    return (f'<svg class="box" id="{i}" style="left:{x}px;top:{y}px;" width="{size}" height="{size}" viewBox="0 0 100 100">'
            f'<circle cx="50" cy="50" r="48" fill="{color}"/>'
            f'<path id="{i}-p" d="M 32 32 L 68 68 M 68 32 L 32 68" fill="none" stroke="#fff" stroke-width="11" stroke-linecap="round" '
            f'pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="0"/></svg>\n')


def icon_draw(i, t, dur=0.45):
    return (f"tl.fromTo('#{i}', {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: 'back.out(2)' }}, {t:.3f});\n"
            f"tl.fromTo('#{i}-p', {{ strokeDashoffset: 110 }}, {{ strokeDashoffset: 0, duration: {dur}, ease: 'power2.out' }}, {t + 0.15:.3f});\n")


def price_tag(i, x, y, text, size, tw, th):
    """price tag with the text inside; one box so it can move as a unit. text = list of stacked alternatives (ids i-0, i-1)."""
    pad_l = 70 + (th - 132) * 0.4
    w = tw
    path = f'M {th * 0.42:.0f} 5 H {w - 17} Q {w - 5} 5 {w - 5} 17 V {th - 17} Q {w - 5} {th - 5} {w - 17} {th - 5} H {th * 0.42:.0f} L 5 {th / 2:.0f} Z'
    return (f'<div class="box" id="{i}" style="left:{x}px;top:{y}px;width:{w}px;height:{th}px;">'
            f'<svg class="box" style="left:0;top:0;" width="{w}" height="{th}" viewBox="0 0 {w} {th}">'
            f'<path d="{path}" fill="{WHITE}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
            f'<circle cx="{th * 0.38:.0f}" cy="{th / 2:.0f}" r="11" fill="{PAPER}" stroke="{INK}" stroke-width="4"/></svg>'
            + ''.join(f'<div class="n" id="{i}-{k}" style="left:{pad_l:.0f}px;top:{(th - size) / 2:.0f}px;font-size:{size}px;color:{INK};">{tx}</div>'
                      for k, tx in enumerate(text)) + '</div>\n')


def building(prefix, x, y, w, h, wins=(5, 2), win=64):
    """simple company building: roof bar, stone body, window grid, door. ids prefix-roof/-body/-wN/-door."""
    out = f'<div class="box" id="{prefix}-roof" style="left:{x - 30}px;top:{y}px;width:{w + 60}px;height:40px;border-radius:10px;background:{STONE_D};"></div>\n'
    out += f'<div class="box" id="{prefix}-body" style="left:{x}px;top:{y + 40}px;width:{w}px;height:{h - 40}px;background:{STONE};"></div>\n'
    cols, rows = wins
    gap = (w - 2 * 46 - cols * win) / (cols - 1) if cols > 1 else 0
    k = 0
    for r in range(rows):
        for c in range(cols):
            wx = x + 46 + c * (win + gap); wy = y + 40 + 40 + r * (win + 40)
            out += f'<div class="box {prefix}-w" id="{prefix}-w{k}" style="left:{wx:.0f}px;top:{wy}px;width:{win}px;height:{win}px;border-radius:8px;background:#F6EBC8;"></div>\n'
            k += 1
    dw = 64
    out += f'<div class="box" id="{prefix}-door" style="left:{x + w // 2 - dw // 2}px;top:{y + h - 92}px;width:{dw}px;height:92px;border-radius:8px 8px 0 0;background:{STONE_D};"></div>\n'
    return out


# ================================================================== S1  opener: loan in, cash back out
def s1():
    sid = 's1'; d = TIM[sid]['dur']
    css = f"""
#root .coin {{ position:absolute; width:38px; height:38px; border-radius:19px; opacity:0; }}
#root .coin i {{ position:absolute; left:9px; top:9px; width:20px; height:20px; border-radius:10px; background:rgba(255,255,255,0.45); }}
"""
    body = txt('s1-ttl', 'What is a leveraged buyout?', 192, 92, 100, INK, 'h')
    body += txt('s1-sub', 'Buying a company mostly with a loan', 192, 218, 54, MUTED, 't m')
    body += building('s1b', 1190, 410, 500, 410, (5, 2))
    body += ctr('s1-company', 'Company', 1440, 846, 56, INK, w=500)
    body += (f'<svg class="box" id="s1-bank" style="left:150px;top:380px;" width="460" height="450" viewBox="150 380 460 450">'
             f'<polygon points="176,540 376,420 576,540" fill="{LOAN}"/>'
             f'<rect x="192" y="548" width="368" height="30" fill="{LOAN}"/>')
    for k in range(4):
        body += f'<rect x="{222 + k * 84}" y="594" width="56" height="176" fill="{LOAN}"/>'
    body += f'<rect x="192" y="780" width="368" height="40" rx="6" fill="{LOAN}"/></svg>\n'
    body += ctr('s1-bank-l', 'Bank', 376, 846, 56, LOAN, w=400)
    body += ('<svg class="box" id="s1-lanes" style="left:0;top:0;" width="1920" height="1080" viewBox="0 0 1920 1080">'
             + svg_path('s1-top', 'M 640 600 L 1070 600', LOAN, 16)
             + f'<polygon id="s1-top-h" points="1116,600 1066,570 1066,630" fill="{LOAN}"/>'
             + svg_path('s1-bot', 'M 1100 740 L 670 740', CASH, 16)
             + f'<polygon id="s1-bot-h" points="624,740 674,710 674,770" fill="{CASH}"/></svg>\n')
    body += ctr('s1-loan', 'Loan', 870, 508, 64, LOAN, w=500)
    body += ctr('s1-cash', 'Cash pays it back', 870, 782, 52, CASH, w=560)
    n_coin = 7
    for k in range(n_coin):
        body += f'<div class="coin" id="s1-ct{k}" style="left:640px;top:581px;background:{LOAN};"><i></i></div>\n'
        body += f'<div class="coin" id="s1-cb{k}" style="left:1090px;top:721px;background:{CASH};"><i></i></div>\n'
    # ---- timeline
    t_company = cue(sid, 'buying', 1, -0.35)
    t_bank = cue(sid, 'mostly', 1, -0.1)
    t_loan = cue(sid, 'loan', 1, -0.55)
    t_own = cue(sid, 'companys', 1, -0.05)
    t_cash = cue(sid, 'cash', 1, -0.25)
    js = pop('#s1-sub', cue(sid, 'buying', 1, -0.3), 0.6, 12)
    js += "".join(pop(f'#s1b-{p}', t_company + dly, 0.6, 40) for p, dly in (('roof', 0), ('body', 0.08), ('door', 0.16)))
    js += f"tl.fromTo('.s1b-w', {{ opacity: 0 }}, {{ opacity: 0.3, duration: 0.5, stagger: 0.05, ease: 'power1.out' }}, {t_company + 0.25:.3f});\n"
    js += pop('#s1-company', t_company + 0.3, 0.5, 14)
    js += pop('#s1-bank', t_bank, 0.6, 30) + pop('#s1-bank-l', t_bank + 0.2, 0.5, 14)
    js += draw('#s1-top', t_loan, 0.7, 'power2.out') + fin('#s1-top-h', t_loan + 0.55, 0.25)
    js += pop('#s1-loan', t_loan + 0.1, 0.5, 14)
    js += draw('#s1-bot', t_own, 0.8, 'power2.out') + fin('#s1-bot-h', t_own + 0.65, 0.25)
    js += pop('#s1-cash', t_cash, 0.5, 14)
    for k in range(n_coin):                       # loan coins: bank -> company
        t0 = t_loan + 0.55 + k * 0.5
        if t0 + 1.0 > d - 0.25: break
        js += (f"tl.fromTo('#s1-ct{k}', {{ x: 0, opacity: 0 }}, {{ x: 400, opacity: 1, duration: 0.18, ease: 'none' }}, {t0:.3f});\n"
               f"tl.to('#s1-ct{k}', {{ x: 440, duration: 0.82, ease: 'power1.inOut' }}, {t0 + 0.18:.3f});\n"
               f"tl.to('#s1-ct{k}', {{ opacity: 0, duration: 0.14 }}, {t0 + 0.86:.3f});\n")
    for k in range(n_coin):                       # cash coins: company -> bank; windows glow as cash leaves
        t0 = t_own + 0.7 + k * 0.5
        if t0 + 1.0 > d - 0.2: break
        js += (f"tl.fromTo('#s1-cb{k}', {{ x: 0, opacity: 0 }}, {{ x: -60, opacity: 1, duration: 0.18, ease: 'none' }}, {t0:.3f});\n"
               f"tl.to('#s1-cb{k}', {{ x: -440, duration: 0.82, ease: 'power1.inOut' }}, {t0 + 0.18:.3f});\n"
               f"tl.to('#s1-cb{k}', {{ opacity: 0, duration: 0.14 }}, {t0 + 0.86:.3f});\n")
        js += f"tl.to('#s1b-w{(k * 3) % 10}', {{ opacity: 1, duration: 0.25, yoyo: true, repeat: 1, ease: 'sine.inOut' }}, {t0 - 0.2:.3f});\n"
    return scene(sid, css, body, js, d, False, True)


# ================================================================== S2  capital stack + price tag
def s2():
    sid = 's2'; d = TIM[sid]['dur']
    X0, XW = 192, 480            # stack column
    TOP, BOT = 250, 970
    H = BOT - TOP
    h_bank, h_thin = H * 0.9, H * 0.05
    y_seller = TOP + h_thin; y_bank = TOP + 2 * h_thin
    RX = 1290                    # right column x
    css = f"""
#root .slice {{ position:absolute; left:{X0}px; width:{XW}px; transform-origin:50% 100%; }}
"""
    body = txt('s2-ttl', 'How the purchase is paid for', 192, 84, 76, INK, 'h')
    body += txt('s2-chip', 'Illustrative company', 1290, 100, 46, MUTED, 't m',
                f'padding:10px 26px;border:3px solid {LINE};border-radius:40px;background:{WHITE};')
    body += f'<div class="slice" id="s2-bank" style="top:{y_bank:.1f}px;height:{h_bank:.1f}px;background:{LOAN};border-radius:0 0 8px 8px;"></div>\n'
    body += f'<div class="slice" id="s2-sell" style="top:{y_seller:.1f}px;height:{h_thin:.1f}px;background:{SELLER};border-top:3px solid {PAPER};box-sizing:border-box;"></div>\n'
    body += f'<div class="slice" id="s2-buy" style="top:{TOP}px;height:{h_thin:.1f}px;background:{CASH};border-radius:8px 8px 0 0;"></div>\n'
    body += ctr('s2-bank-pct', '90%', X0 + XW // 2, 530, 150, WHITE, 'n', w=XW)
    body += ctr('s2-bank-l', 'Bank loan', X0 + XW // 2, 712, 64, WHITE, 't', w=XW)
    yb, ys = TOP + h_thin / 2, y_seller + h_thin / 2
    body += (f'<svg class="box" id="s2-lead" style="left:0;top:0;" width="1920" height="1080" viewBox="0 0 1920 1080">'
             + svg_path('s2-lb', f'M {X0 + XW + 6} {yb:.0f} L {X0 + XW + 64} {yb - 40:.0f}', CASH, 5)
             + svg_path('s2-ls', f'M {X0 + XW + 6} {ys:.0f} L {X0 + XW + 64} {ys + 40:.0f}', SELLER, 5) + '</svg>\n')
    LX = X0 + XW + 84
    body += row('s2-buy-r', [('Buyer cash', 56, CASH, 't'), ('5%', 72, CASH, 'n')], LX, int(yb - 40 - 40), 26)
    body += row('s2-sell-r', [('Seller note', 56, SELLER, 't'), ('5%', 72, SELLER, 'n')], LX, int(ys + 40 - 40), 26)
    body += ('<svg class="box" id="s2-arr" style="left:0;top:0;" width="1920" height="1080" viewBox="0 0 1920 1080">'
             + svg_path('s2-arr-l', 'M 1240 640 L 800 640', MUTED, 10) + f'<polygon id="s2-arr-h" points="740,640 800,606 800,674" fill="{MUTED}"/></svg>\n')
    body += ctr('s2-arr-t', 'paid for by', 990, 560, 52, MUTED, 't m', w=480)
    # right column: profit, price tag, fees
    body += row('s2-profit', [('$1.0M', 112, INK, 'n'), ('a year', 52, MUTED, 't m')], RX, 250, 22)
    body += txt('s2-profit-l', 'operating profit', RX, 382, 52, MUTED, 't m')
    body += txt('s2-tag-l', 'Price', RX + 6, 478, 48, MUTED, 't m')
    tw = int(textw('$4.0M', 96, 'n')) + 112 + 52
    body += price_tag('s2-tag', RX, 530, ['$4.0M'], 96, tw, 170)
    body += txt('s2-fee', '+$250K', RX, 744, 100, INK, 'n') + txt('s2-fee-l', 'fees and cushion', RX, 862, 56, MUTED, 't m')
    # ---- timeline
    t_ill = cue(sid, 'illustrative', 1, -0.3)
    t_1m = cue(sid, '1', 1, -0.2)
    t_op = cue(sid, 'operating', 1, -0.15)
    t_price = cue(sid, 'priced', 1, -0.1)
    t_fees = cue(sid, 'fees', 1, -0.15)
    t_bank = cue(sid, 'bank', 1, -0.25)
    t_90 = cue(sid, '90', 1, -0.2)
    t_sell = cue(sid, 'seller', 1, -0.15)
    t_buy = cue(sid, 'buyer', 1, -0.15)
    js = pop('#s2-ttl', 0.25, 0.7, 20) + pop('#s2-chip', t_ill, 0.5, 14)
    js += pop('#s2-profit', t_1m, 0.55, 20) + pop('#s2-profit-l', t_op, 0.5, 14)
    js += pop('#s2-tag', t_price, 0.6, 30) + pop('#s2-tag-l', t_price, 0.45, 10)
    js += pop('#s2-fee', t_fees, 0.55, 20) + pop('#s2-fee-l', t_fees + 0.2, 0.5, 14)
    js += draw('#s2-arr-l', t_bank - 0.1, 0.6, 'power2.out') + fin('#s2-arr-h', t_bank + 0.4, 0.2) + pop('#s2-arr-t', t_bank, 0.5, 10)
    js += grow('#s2-bank', t_bank, 0.9)                     # the stack builds bottom to top
    js += pop('#s2-bank-pct', t_90, 0.5, 16) + pop('#s2-bank-l', t_bank + 0.25, 0.5, 14)
    js += (f"tl.fromTo('#s2-sell', {{ opacity: 0, y: -50 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: 'back.out(1.5)' }}, {t_sell:.3f});\n"
           f"tl.fromTo('#s2-buy', {{ opacity: 0, y: -50 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: 'back.out(1.5)' }}, {t_buy:.3f});\n")
    js += draw('#s2-ls', t_sell + 0.25, 0.4, 'power2.out') + pop('#s2-sell-r', t_sell + 0.3, 0.5, 10)
    js += draw('#s2-lb', t_buy + 0.25, 0.4, 'power2.out') + pop('#s2-buy-r', t_buy + 0.3, 0.5, 10)
    return scene(sid, css, body, js, d)


# ================================================================== S3  the bank test
def s3():
    sid = 's3'; d = TIM[sid]['dur']
    K = 1.25                                 # px per $1K
    bx = 192
    w_cash, w_pay, w_pay2 = 800 * K, 600 * K, 671 * K
    BH = 140
    R1, R2 = 410, 720                        # bar tops
    css = f"""
#root .bar {{ position:absolute; left:{bx}px; height:{BH}px; border-radius:14px; transform-origin:0 50%; }}
#root .badge {{ position:absolute; left:1330px; top:430px; width:400px; height:360px; border-radius:30px; box-sizing:border-box; border:7px solid; }}
"""
    body = txt('s3-ttl', 'The bank’s test', 192, 84, 84, INK, 'h')
    chip = f'padding:12px 30px;border:4px solid {INK};border-radius:46px;background:{WHITE};'
    body += txt('s3-p1', 'Price: 4.0x profit', 1120, 104, 52, INK, 't', chip) + txt('s3-p2', 'Price: 4.5x profit', 1120, 104, 52, INK, 't', chip)
    body += txt('s3-l1', 'Cash for lenders', bx, R1 - 74, 56, INK)
    body += f'<div class="bar" id="s3-b1" style="top:{R1}px;width:{w_cash:.0f}px;background:{CASH};"></div>\n'
    body += txt('s3-v1', '$800K', bx + 36, R1 + (BH - 92) // 2, 92, WHITE, 'n')
    body += txt('s3-l2', 'Loan payment', bx, R2 - 74, 56, INK)
    body += f'<div class="bar" id="s3-b2" style="top:{R2}px;width:{w_pay:.0f}px;background:{LOAN};"></div>\n'
    body += f'<div class="bar" id="s3-b2x" style="top:{R2}px;width:{w_pay2:.0f}px;background:{LOAN};opacity:0;"></div>\n'
    body += txt('s3-v2', '$600K', bx + 36, R2 + (BH - 92) // 2, 92, WHITE, 'n') + txt('s3-v2x', '$671K', bx + 36, R2 + (BH - 92) // 2, 92, WHITE, 'n')
    body += (f'<svg class="box" id="s3-mk" style="left:0;top:0;" width="1920" height="1080" viewBox="0 0 1920 1080">'
             f'<path d="M {bx + w_cash:.0f} {R1 - 30} L {bx + w_cash:.0f} {R2 + BH + 36}" fill="none" stroke="{MUTED}" stroke-width="4" '
             f'stroke-dasharray="14 12" stroke-linecap="round"/></svg>\n')
    body += f'<div class="badge" id="s3-pass" style="background:rgba(30,127,85,0.10);border-color:{CASH};"></div>\n'
    body += f'<div class="badge" id="s3-fail" style="background:rgba(180,35,24,0.09);border-color:{FAIL};"></div>\n'
    body += ctr('s3-cov', 'Coverage', 1530, 356, 56, INK, 't', w=380)
    body += ctr('s3-n1', '1.33x', 1530, 470, 128, CASH, 'n', w=380) + ctr('s3-n2', '1.19x', 1530, 470, 128, FAIL, 'n', w=380)
    body += icon_check('s3-ck', 1366, 622, 100, CASH) + txt('s3-w1', 'Passes', 1484, 640, 66, CASH)
    body += icon_x('s3-xx', 1366, 622, 100, FAIL) + txt('s3-w2', 'Fails', 1484, 640, 66, FAIL)
    body += ctr('s3-f1', '$800K ÷ $600K', 1530, 826, 48, MUTED, 't m', w=420) + ctr('s3-f2', '$800K ÷ $671K', 1530, 826, 48, MUTED, 't m', w=420)
    # ---- timeline
    t_cash = cue(sid, '800', 1, -0.5)
    t_pay = cue(sid, '600', 1, -0.5)
    t_cov = cue(sid, '33', 1, -0.7)             # "1.33"
    t_pass = cue(sid, 'passes', 1, -0.25)
    t_pay2 = cue(sid, 'pay', 1, -0.15)
    t_119 = cue(sid, '19', 1, -0.5)
    js = pop('#s3-ttl', 0.25, 0.7, 20) + pop('#s3-p1', 0.6, 0.5, 12)
    js += "tl.set('#s3-p2,#s3-v2x,#s3-n2,#s3-w2,#s3-xx,#s3-f2,#s3-fail,#s3-mk,#s3-pass', { opacity: 0 }, 0);\n"
    js += pop('#s3-l1', t_cash, 0.5, 12) + grow('#s3-b1', t_cash + 0.1, 1.5, 'x') + pop('#s3-v1', t_cash + 0.5, 0.5, 10)
    js += pop('#s3-l2', t_pay, 0.5, 12) + grow('#s3-b2', t_pay + 0.1, 1.2, 'x') + pop('#s3-v2', t_pay + 0.5, 0.5, 10)
    js += fin('#s3-mk', t_pay + 0.2, 0.5)
    js += (f"tl.fromTo('#s3-pass', {{ opacity: 0, scale: 0.92 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: 'back.out(1.6)' }}, {t_cov:.3f});\n")
    js += pop('#s3-n1', t_cov + 0.1, 0.5, 14) + pop('#s3-cov', t_cov - 0.05, 0.45, 8) + pop('#s3-f1', t_cov + 0.35, 0.45, 8)
    js += icon_draw('s3-ck', t_pass) + pop('#s3-w1', t_pass + 0.1, 0.45, 12)
    js += swap('#s3-p1', '#s3-p2', t_pay2)                    # price moves to 4.5x, the payment bar grows to $671K
    js += (f"tl.set('#s3-b2x', {{ opacity: 1 }}, {t_pay2 + 0.1:.3f});\n"
           f"tl.fromTo('#s3-b2x', {{ scaleX: {w_pay / w_pay2:.4f} }}, {{ scaleX: 1, duration: 1.0, ease: 'power2.inOut', immediateRender: false }}, {t_pay2 + 0.1:.3f});\n"
           f"tl.set('#s3-b2', {{ opacity: 0 }}, {t_pay2 + 0.1:.3f});\n")
    js += swap('#s3-v2', '#s3-v2x', t_pay2 + 0.7)
    t_flip = t_119 + 0.3                                        # the whole badge flips together: number, word, icon, colour
    js += swap('#s3-f1', '#s3-f2', t_flip) + swap('#s3-n1', '#s3-n2', t_flip)
    js += fout('#s3-pass', t_flip, 0.3)
    js += (f"tl.fromTo('#s3-fail', {{ opacity: 0, scale: 0.94 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: 'back.out(1.8)' }}, {t_flip + 0.1:.3f});\n")
    js += fout('#s3-ck', t_flip, 0.25) + fout('#s3-w1', t_flip, 0.25)
    js += icon_draw('s3-xx', t_flip + 0.25) + pop('#s3-w2', t_flip + 0.35, 0.45, 12)
    js += f"tl.to('#s3-xx', {{ scale: 1.12, duration: 0.4, yoyo: true, repeat: 3, ease: 'sine.inOut' }}, {t_flip + 1.0:.3f});\n"
    return scene(sid, css, body, js, d)


# ================================================================== S4  verify the earnings
def s4():
    sid = 's4'; d = TIM[sid]['dur']
    Y0 = 900; HFULL, HVER = 500, 400
    EX, EW = 300, 300       # earnings column
    PX, PW = 1060, 300      # price column
    css = f"""
#root .hatch {{ position:absolute; background: repeating-linear-gradient(135deg, {FAIL} 0 14px, #D96A5F 14px 28px); opacity:0; }}
"""
    body = txt('s4-ttl', 'Verify the earnings', 192, 84, 84, INK, 'h')
    body += f'<div class="box" id="s4-eb" style="left:{EX}px;top:{Y0 - HVER}px;width:{EW}px;height:{HVER}px;background:{CASH};border-radius:0 0 10px 10px;transform-origin:50% 100%;"></div>\n'
    body += f'<div class="box" id="s4-es" style="left:{EX}px;top:{Y0 - HFULL}px;width:{EW}px;height:{HFULL - HVER}px;background:{CASH};border-radius:10px 10px 0 0;"></div>\n'
    body += f'<div class="hatch" id="s4-esh" style="left:{EX}px;top:{Y0 - HFULL}px;width:{EW}px;height:{HFULL - HVER}px;border-radius:10px 10px 0 0;"></div>\n'
    body += ctr('s4-ev1', '$1.25M', EX + EW // 2, Y0 - HFULL - 142, 100, INK, 'n', w=440)
    body += ctr('s4-ev2', '$1.0M', EX + EW // 2, Y0 - HVER - 142, 100, INK, 'n', w=440)
    body += ctr('s4-el1', 'Seller’s earnings', EX + EW // 2, Y0 + 30, 52, INK, 't', w=560)
    body += ctr('s4-el2', 'Verified earnings', EX + EW // 2, Y0 + 30, 52, CASH, 't', w=560)
    body += txt('s4-gap', '$250K', EX + EW + 40, Y0 - HFULL + 4, 84, FAIL, 'n') + txt('s4-gap-l', 'not real', EX + EW + 40, Y0 - HFULL + 98, 52, FAIL)
    body += f'<div class="box" id="s4-pb" style="left:{PX}px;top:{Y0 - HVER}px;width:{PW}px;height:{HVER}px;background:{LOAN};border-radius:0 0 10px 10px;transform-origin:50% 100%;"></div>\n'
    body += f'<div class="box" id="s4-ps" style="left:{PX}px;top:{Y0 - HFULL}px;width:{PW}px;height:{HFULL - HVER}px;background:{LOAN};border-radius:10px 10px 0 0;"></div>\n'
    body += f'<div class="hatch" id="s4-psh" style="left:{PX}px;top:{Y0 - HFULL}px;width:{PW}px;height:{HFULL - HVER}px;border-radius:10px 10px 0 0;"></div>\n'
    tgw = int(textw('$5.0M', 84, 'n')) + 70 + 48
    TAGY = Y0 - HFULL - 150
    BRX = PX + PW // 2 + tgw // 2 + 18                       # bracket sits just right of the tag
    body += price_tag('s4-tag', PX + PW // 2 - tgw // 2, TAGY, ['$5.0M', '$4.0M'], 84, tgw, 132)
    body += ctr('s4-pl', 'Price', PX + PW // 2, Y0 + 30, 52, INK, 't', w=400)
    body += txt('s4-over', '$1.0M', BRX + 42, Y0 - HFULL + 4, 100, FAIL, 'n') + txt('s4-over-l', 'overpaid', BRX + 42, Y0 - HFULL + 114, 60, FAIL)
    body += ('<svg class="box" id="s4-mul" style="left:0;top:0;" width="1920" height="1080" viewBox="0 0 1920 1080">'
             + svg_path('s4-mul-l', f'M {EX + EW + 80} 700 L {PX - 80} 700', MUTED, 9) + f'<polygon id="s4-mul-h" points="{PX - 24},700 {PX - 80},668 {PX - 80},732" fill="{MUTED}"/></svg>\n')
    body += ctr('s4-mul-t', '4x profit', (EX + EW + PX) // 2, 604, 56, MUTED, 't', w=380)
    body += (f'<svg class="box" id="s4-br" style="left:0;top:0;" width="1920" height="1080" viewBox="0 0 1920 1080">'
             + svg_path('s4-br-p', f'M {BRX} {Y0 - HFULL} L {BRX + 12} {Y0 - HFULL} L {BRX + 12} {Y0 - HVER} L {BRX} {Y0 - HVER}', FAIL, 6) + '</svg>\n')
    body += (f'<div class="box" id="s4-mag" style="left:0;top:0;width:260px;height:260px;"><svg width="260" height="260" viewBox="0 0 260 260">'
             f'<circle cx="104" cy="104" r="84" fill="rgba(255,255,255,0.35)" stroke="{INK}" stroke-width="16"/>'
             f'<path d="M 166 166 L 236 236" stroke="{INK}" stroke-width="26" stroke-linecap="round"/>'
             f'<path d="M 58 84 Q 70 54 102 48" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" opacity="0.8"/></svg></div>\n')
    # ---- timeline
    t_bar = 0.75
    t_verify = cue(sid, 'verify', 1, -0.05)
    t_250 = cue(sid, '250', 1, -0.1)
    t_isnt = cue(sid, 'isnt', 1, -0.05)
    t_real = cue(sid, 'real', 1, 0.0)
    t_costs = cue(sid, 'costs', 1, -0.1)
    t_mill = cue(sid, 'million', 1, -0.2)
    t_four = cue(sid, '4', 1, -0.2)
    t_times = cue(sid, 'times', 1, -0.1)
    hx, hy = EX + EW // 2 - 104, Y0 - HVER - 104 + 20      # lens centre over the slab / bar top
    js = pop('#s4-ttl', 0.25, 0.7, 20)
    js += "tl.set('#s4-ev2,#s4-el2,#s4-gap,#s4-gap-l,#s4-ps,#s4-tag,#s4-pl,#s4-over,#s4-over-l,#s4-mul,#s4-mul-t,#s4-mag,#s4-tag-1', { opacity: 0 }, 0);\n"
    js += (f"tl.fromTo('#s4-eb', {{ scaleY: 0 }}, {{ scaleY: 1, duration: 0.9, ease: 'power2.out' }}, {t_bar:.3f});\n"
           f"tl.fromTo('#s4-es', {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: 'power2.out' }}, {t_bar + 0.7:.3f});\n")
    js += pop('#s4-ev1', t_bar + 0.8, 0.5, 14) + pop('#s4-el1', t_bar + 0.3, 0.5, 12)
    c_mid, c_slab = 640, 468                                 # lens centre y: down the bar, then onto the slab
    js += (f"tl.fromTo('#s4-mag', {{ opacity: 0, x: {hx + 420}, y: {c_mid - 104 - 260}, rotation: 14 }}, {{ opacity: 1, x: {hx}, y: {c_mid - 104}, rotation: 0, duration: 0.9, ease: 'power2.out' }}, {t_verify:.3f});\n"
           f"tl.to('#s4-mag', {{ y: {c_slab - 104}, duration: 1.0, ease: 'sine.inOut' }}, {max(t_verify + 1.0, t_250 - 0.45):.3f});\n")
    js += fin('#s4-esh', t_250, 0.35) + pop('#s4-gap', t_250 + 0.1, 0.5, 12) + pop('#s4-gap-l', t_isnt, 0.45, 10)
    t_drop = t_real + 0.15
    js += f"tl.to('#s4-es,#s4-esh', {{ y: 70, opacity: 0, duration: 0.5, ease: 'power2.in' }}, {t_drop:.3f});\n"
    js += swap('#s4-ev1', '#s4-ev2', t_drop - 0.05) + swap('#s4-el1', '#s4-el2', t_drop)
    js += fout('#s4-gap,#s4-gap-l', t_drop + 0.2, 0.4) + fout('#s4-mag', t_drop - 0.05, 0.45)
    js += (f"tl.fromTo('#s4-pb', {{ scaleY: 0 }}, {{ scaleY: 1, duration: 0.8, ease: 'power2.out' }}, {t_costs + 0.1:.3f});\n"
           f"tl.fromTo('#s4-ps', {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: 'power2.out' }}, {t_costs + 0.7:.3f});\n")
    js += pop('#s4-tag', t_costs + 0.5, 0.5, 14) + pop('#s4-pl', t_costs + 0.3, 0.45, 10)
    js += fin('#s4-psh', t_mill - 0.1, 0.35) + pop('#s4-over', t_mill, 0.5, 12) + pop('#s4-over-l', t_mill + 0.15, 0.5, 10) + draw('#s4-br-p', t_mill - 0.05, 0.5, 'power2.out')
    js += f"tl.fromTo('#s4-mul', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {t_four - 0.1:.3f});\n"
    js += draw('#s4-mul-l', t_four - 0.1, 0.6, 'power2.out') + pop('#s4-mul-t', t_four, 0.45, 10)
    t_down = t_times + 0.0
    js += (f"tl.to('#s4-ps,#s4-psh', {{ y: 70, opacity: 0, duration: 0.55, ease: 'power2.in' }}, {t_down:.3f});\n"
           f"tl.to('#s4-tag', {{ y: 100, duration: 0.6, ease: 'power2.inOut' }}, {t_down:.3f});\n")
    js += fout('#s4-tag-0', t_down + 0.15, 0.25) + fin('#s4-tag-1', t_down + 0.3, 0.3)
    return scene(sid, css, body, js, d)


# ================================================================== S5  day-one cash line
def s5():
    sid = 's5'; d = TIM[sid]['dur']
    wk = DATA['day1']['weeks']
    X0, X1 = 250, 1180                    # week 0 .. week 13
    Z = 470                               # y of $0
    K = 0.7                               # px per $1K
    px = lambda w: X0 + (X1 - X0) * w / 13.0
    py = lambda v: Z - v / 1000.0 * K
    pts = [(px(r['week']), py(r['cash_no_ar'])) for r in wk]
    path = 'M ' + ' L '.join('%.1f %.1f' % p for p in pts)
    low = min(wk, key=lambda r: r['cash_no_ar'])
    lx, ly = px(low['week']), py(low['cash_no_ar'])
    sy = py(wk[0]['cash_no_ar'])
    BX = 1250                             # bracket x
    mid = int((sy + ly) / 2)
    body = txt('s5-ttl', 'Day 1 cash', 192, 84, 84, INK, 'h')
    body += txt('s5-sub', 'The seller keeps what customers owe', 192, 196, 54, MUTED, 't m')
    body += (f'<svg class="box" id="s5-svg" style="left:0;top:0;" width="1920" height="1080" viewBox="0 0 1920 1080">'
             f'<line x1="{X0 - 20}" y1="{Z}" x2="{X1 + 30}" y2="{Z}" stroke="{MUTED}" stroke-width="4"/>'
             f'<path id="s5-ref1" d="M {X0} {sy:.0f} L {BX + 24} {sy:.0f}" fill="none" stroke="{MUTED}" stroke-width="3" stroke-dasharray="12 12" opacity="0"/>'
             f'<path id="s5-ref2" d="M {lx:.0f} {ly:.0f} L {BX + 24} {ly:.0f}" fill="none" stroke="{MUTED}" stroke-width="3" stroke-dasharray="12 12" opacity="0"/>'
             + svg_path('s5-line', path, INK, 12) +
             f'<circle id="s5-d0" cx="{X0}" cy="{sy:.0f}" r="14" fill="{INK}"/>'
             f'<circle id="s5-dl" cx="{lx:.0f}" cy="{ly:.0f}" r="18" fill="{FAIL}" stroke="{PAPER}" stroke-width="5"/>'
             + svg_path('s5-br', f'M {BX} {sy:.0f} L {BX} {ly:.0f}', INK, 8) +
             f'<path id="s5-br1" d="M {BX - 22} {sy:.0f} L {BX} {sy:.0f}" stroke="{INK}" stroke-width="8" stroke-linecap="round" opacity="0"/>'
             f'<path id="s5-br2" d="M {BX - 22} {ly:.0f} L {BX} {ly:.0f}" stroke="{INK}" stroke-width="8" stroke-linecap="round" opacity="0"/>'
             '</svg>\n')
    body += txt('s5-z', '$0', X0 - 150, Z - 30, 52, MUTED, 'n', 'width:110px;text-align:right;')
    body += txt('s5-a0', 'Day 1', X0 - 40, 936, 48, MUTED, 't m') + ctr('s5-a1', 'Week 13', X1, 936, 48, MUTED, 't m', w=260)
    body += ctr('s5-low', '-$500K', lx, ly + 34, 64, FAIL, 'n', w=300)
    body += txt('s5-n-a', 'about', BX + 60, mid - 65 - 76, 52, MUTED, 't m')
    body += txt('s5-n', '$600K', BX + 60, mid - 65, 130, FAIL, 'n')
    body += txt('s5-n-b', 'needed', BX + 60, mid + 65 + 14, 60, INK, 't')
    # ---- timeline
    t_day = cue(sid, 'day', 1, -0.1)
    t_sub = cue(sid, 'seller', 1, -0.3)
    t_pay = cue(sid, 'payroll', 1, -0.2)
    t_arr = cue(sid, 'arrive', 1, 0.1)
    t_600 = cue(sid, '600', 1, -0.55)
    js = pop('#s5-ttl', 0.25, 0.7, 20)
    js += "tl.set('#s5-d0,#s5-dl,#s5-z,#s5-low,#s5-n-a,#s5-n,#s5-n-b,#s5-a0,#s5-a1', { opacity: 0 }, 0);\n"
    js += f"tl.fromTo('#s5-svg', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, {t_day:.3f});\n"
    js += fin('#s5-d0', t_day + 0.2, 0.3) + fin('#s5-z', t_day + 0.2, 0.3) + fin('#s5-a0', t_day + 0.3, 0.3)
    js += pop('#s5-sub', t_sub, 0.6, 14)
    js += f"tl.fromTo('#s5-ref1', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, {t_sub + 0.4:.3f});\n"
    js += draw('#s5-line', t_pay, t_arr - t_pay + 0.2, 'none') + fin('#s5-a1', t_pay + 1.6, 0.4)
    t_low = t_pay + (t_arr - t_pay) * 0.62
    js += f"tl.fromTo('#s5-dl', {{ opacity: 0, scale: 0.2, transformOrigin: '50% 50%' }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: 'back.out(2)' }}, {t_low:.3f});\n"
    js += pop('#s5-low', t_low + 0.15, 0.5, 10)
    js += f"tl.fromTo('#s5-ref2,#s5-br1,#s5-br2', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, {t_600:.3f});\n"
    js += draw('#s5-br', t_600, 0.7, 'power2.out')
    js += pop('#s5-n-a', t_600 + 0.2, 0.45, 10) + pop('#s5-n', t_600 + 0.3, 0.55, 14) + pop('#s5-n-b', t_600 + 0.5, 0.45, 10)
    # keep the held end state alive: a slow pulse on the low point (even number of half cycles, so it ends at rest)
    js += f"tl.to('#s5-dl', {{ scale: 1.3, transformOrigin: '50% 50%', duration: 0.5, yoyo: true, repeat: 3, ease: 'sine.inOut' }}, {t_600 + 1.0:.3f});\n"
    return scene(sid, '', body, js, d)


# ================================================================== S6  AI tools by department
def s6():
    sid = 's6'; d = TIM[sid]['dur']
    tiles = [('Operations', 'Quoting'), ('Sales', 'Follow-ups'), ('Finance', 'Billing'), ('Accounting', 'Month-end'), ('Reporting', 'Dashboards')]
    TW, TH, GX, GY = 500, 260, 40, 40
    X0, Y0 = 170, 360
    css = f"""
#root .tile {{ position:absolute; width:{TW}px; height:{TH}px; border-radius:24px; box-sizing:border-box; background:{WHITE}; border:4px solid {LINE}; }}
#root .chip {{ position:absolute; height:88px; padding:0 8px; border-radius:44px; font-size:54px; font-weight:600; line-height:80px; box-sizing:border-box; white-space:nowrap; }}
"""
    body = txt('s6-ttl', 'Then improve the business', 192, 84, 84, INK, 'h')
    chips = [('Better pricing', 'c1', INK, WHITE, LINE), ('A real sales process', 'c2', INK, WHITE, LINE), ('AI tools', 'c3', WHITE, AI, AI)]
    cx = 192
    for name, cid, fg, bg, bd in chips:
        w = int(textw(name, 54)) + 2 * 34 + 8
        body += (f'<div class="chip" id="s6-{cid}" style="left:{cx}px;top:224px;width:{w}px;text-align:center;color:{fg};background:{bg};border:4px solid {bd};">{name}</div>\n')
        cx += w + 26
    for k, (dept, task) in enumerate(tiles):
        r, c = divmod(k, 3)
        x, y = X0 + c * (TW + GX), Y0 + r * (TH + GY)
        body += f'<div class="tile" id="s6-t{k}" style="left:{x}px;top:{y}px;"></div>\n'
        body += txt(f's6-d{k}', dept, x + 38, y + 34, 66, INK, 'h')
        body += txt(f's6-k{k}', task, x + 38, y + 150, 58, WHITE, 't')
    x6, y6 = X0 + 2 * (TW + GX), Y0 + (TH + GY)
    body += f'<div class="tile" id="s6-t5" style="left:{x6}px;top:{y6}px;border:4px dashed {INK};background:transparent;"></div>\n'
    body += ctr('s6-bet', 'A bet,', x6 + TW // 2, y6 + 52, 64, INK, 'h', w=TW - 20) + ctr('s6-bet2', 'not a promise.', x6 + TW // 2, y6 + 132, 64, INK, 'h', w=TW - 20)
    # ---- timeline
    js = pop('#s6-ttl', 0.25, 0.7, 20)
    js += pop('#s6-c1', cue(sid, 'better', 1, -0.15), 0.5, 14)
    js += pop('#s6-c2', cue(sid, 'real', 1, -0.3), 0.5, 14)
    t_ai = cue(sid, 'ai', 1, -0.15)
    js += pop('#s6-c3', t_ai, 0.5, 14)
    js += ("tl.fromTo('#s6-t0,#s6-t1,#s6-t2,#s6-t3,#s6-t4,#s6-d0,#s6-d1,#s6-d2,#s6-d3,#s6-d4', { opacity: 0, y: 24 }, "
           "{ opacity: 1, y: 0, duration: 0.5, ease: 'power2.out', stagger: 0.06 }, %.3f);\n" % (t_ai + 0.25))
    lit = [cue(sid, 'quoting', 1, -0.25), cue(sid, 'scheduling', 1, -0.3), cue(sid, 'billing', 1, -0.3), cue(sid, 'and', 2, -0.05), cue(sid, 'reporting', 1, -0.3)]
    for k, t in enumerate(lit):
        js += (f"tl.to('#s6-t{k}', {{ backgroundColor: '{AI}', borderColor: '{AI}', duration: 0.4, ease: 'power2.out' }}, {t:.3f});\n"
               f"tl.to('#s6-d{k}', {{ color: '{WHITE}', duration: 0.4 }}, {t:.3f});\n"
               f"tl.fromTo('#s6-k{k}', {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: 'power2.out' }}, {t + 0.12:.3f});\n")
    js += pop('#s6-t5', cue(sid, 'bet', 1, -0.3), 0.5, 14) + pop('#s6-bet', cue(sid, 'bet', 1, -0.15), 0.6, 14) + pop('#s6-bet2', cue(sid, 'not', 1, -0.15), 0.6, 14)
    return scene(sid, css, body, js, d)


# ================================================================== S7  plan works vs profit falls
def s7():
    sid = 's7'; d = TIM[sid]['dur']
    CX_L, CX_R, CW = 120, 990, 810
    CT, CH = 130, 700
    BASE = CT + CH - 56
    BH = 21 * 21.5                       # bar height for ~21x
    css = f"""
#root .card {{ position:absolute; top:{CT}px; width:{CW}px; height:{CH}px; border-radius:30px; box-sizing:border-box; border:5px solid; }}
"""
    body = f'<div class="card" id="s7-cl" style="left:{CX_L}px;border-color:{CASH};background:rgba(30,127,85,0.07);"></div>\n'
    body += f'<div class="card" id="s7-cr" style="left:{CX_R}px;border-color:{FAIL};background:rgba(180,35,24,0.06);"></div>\n'
    body += icon_check('s7-ck', CX_L + 38, CT + 36, 96, CASH) + txt('s7-tl', 'Plan works', CX_L + 160, CT + 48, 76, CASH, 'h')
    body += icon_x('s7-xx', CX_R + 38, CT + 36, 96, FAIL) + txt('s7-tr', 'Profit falls 35%', CX_R + 160, CT + 54, 68, FAIL, 'h')
    body += f'<div class="box" id="s7-bl" style="left:{CX_L + 64}px;top:{BASE - BH:.0f}px;width:150px;height:{BH:.0f}px;background:{CASH};border-radius:12px 12px 0 0;transform-origin:50% 100%;"></div>\n'
    body += txt('s7-al', 'about', CX_L + 270, CT + 178, 54, INK, 't m') + txt('s7-nl', '21x', CX_L + 270, CT + 240, 200, CASH, 'n')
    body += txt('s7-ul', 'the buyer’s cash', CX_L + 270, CT + 470, 54, INK, 't')
    body += txt('s7-fl', 'before fees', CX_L + 270, CT + 548, 50, MUTED, 't m') + txt('s7-fl2', 'and taxes', CX_L + 270, CT + 604, 50, MUTED, 't m')
    body += (f'<div class="box" id="s7-gr" style="left:{CX_R + 64}px;top:{BASE - BH:.0f}px;width:150px;height:{BH:.0f}px;border:4px dashed {FAIL};border-radius:12px 12px 0 0;box-sizing:border-box;"></div>\n')
    body += f'<div class="box" id="s7-br" style="left:{CX_R + 64}px;top:{BASE - 14}px;width:150px;height:14px;background:{FAIL};"></div>\n'
    body += txt('s7-nr', '$0', CX_R + 270, CT + 230, 220, FAIL, 'n') + txt('s7-ur', 'back to the buyer', CX_R + 270, CT + 470, 54, INK, 't')
    body += ctr('s7-end', 'Leverage cuts both ways.', 960, 902, 76, INK, 'h', w=1500)
    # ---- timeline
    t_if1 = cue(sid, 'if', 1, -0.1)
    t_sale = cue(sid, 'sale', 1, -0.2)
    t_21 = cue(sid, '21', 1, -0.3)
    t_before = cue(sid, 'before', 1, -0.15)
    t_if2 = cue(sid, 'if', 2, -0.15)
    t_falls = cue(sid, 'falls', 1, -0.1)
    t_cash = cue(sid, 'cash', 2, -0.2)
    t_gone = cue(sid, 'gone', 1, -0.35)
    t_lev = cue(sid, 'leverage', 1, -0.1)
    js = f"tl.fromTo('#s7-cl', {{ opacity: 0, scale: 0.96 }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: 'power2.out' }}, 0.3);\n"
    js += icon_draw('s7-ck', t_if1 + 0.2) + pop('#s7-tl', t_if1 + 0.25, 0.55, 14)
    js += grow('#s7-bl', t_sale, 2.0, 'y', 'power2.out')
    js += pop('#s7-al', t_21 - 0.2, 0.4, 10) + pop('#s7-nl', t_21 - 0.1, 0.6, 18) + pop('#s7-ul', t_21 + 0.4, 0.5, 12)
    js += pop('#s7-fl', t_before, 0.5, 10) + pop('#s7-fl2', t_before + 0.15, 0.5, 10)
    js += f"tl.fromTo('#s7-cr', {{ opacity: 0, scale: 0.96 }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: 'power2.out' }}, {t_if2:.3f});\n"
    js += icon_draw('s7-xx', t_falls) + pop('#s7-tr', t_falls - 0.05, 0.55, 14)
    js += fin('#s7-gr', t_cash - 0.2, 0.5) + fin('#s7-br', t_cash, 0.4)
    js += pop('#s7-nr', t_gone, 0.6, 18) + pop('#s7-ur', t_gone + 0.45, 0.5, 12)
    js += pop('#s7-end', t_lev, 0.7, 16)
    return scene(sid, css, body, js, d)


# ================================================================== S8  end card
def s8():
    sid = 's8'; d = TIM[sid]['dur']
    SX, SW, STOP, SH = 192, 270, 250, 560
    h_b, h_t = SH * 0.9, SH * 0.05
    body = f'<div class="box" id="s8-bank" style="left:{SX}px;top:{STOP + 2 * h_t:.0f}px;width:{SW}px;height:{h_b:.0f}px;background:{LOAN};border-radius:0 0 10px 10px;transform-origin:50% 100%;"></div>\n'
    body += f'<div class="box" id="s8-sell" style="left:{SX}px;top:{STOP + h_t:.0f}px;width:{SW}px;height:{h_t:.0f}px;background:{SELLER};"></div>\n'
    body += f'<div class="box" id="s8-buy" style="left:{SX}px;top:{STOP}px;width:{SW}px;height:{h_t:.0f}px;background:{CASH};border-radius:10px 10px 0 0;"></div>\n'
    body += txt('s8-t1', 'Leveraged buyouts,', 560, 236, 124, INK, 'h') + txt('s8-t2', 'explained', 560, 372, 124, INK, 'h')
    body += f'<div class="box" id="s8-rule" style="left:564px;top:528px;width:520px;height:8px;border-radius:4px;background:{LOAN};transform-origin:0 50%;"></div>\n'
    body += txt('s8-d1', 'Illustrative company.', 560, 580, 56, MUTED, 't m') + txt('s8-d2', 'Not investment, legal or tax advice.', 560, 652, 56, MUTED, 't m')
    body += txt('s8-url', 'wilsonwu-ai.github.io/leveraged-buyouts-explained', 192, 880, 60, INK, 't')
    t_ill = cue(sid, 'illustrative', 1, -0.15)
    js = grow('#s8-bank', 0.2, 0.9) + (f"tl.fromTo('#s8-sell', {{ opacity: 0, y: -40 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: 'back.out(1.5)' }}, 0.85);\n"
                                         f"tl.fromTo('#s8-buy', {{ opacity: 0, y: -40 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: 'back.out(1.5)' }}, 1.05);\n")
    js += pop('#s8-t1', cue(sid, 'leveraged', 1, -0.05), 0.7, 20) + pop('#s8-t2', cue(sid, 'explained', 1, -0.35), 0.7, 20)
    js += grow('#s8-rule', cue(sid, 'explained', 1, 0.1), 0.6, 'x')
    js += pop('#s8-d1', t_ill, 0.55, 14) + pop('#s8-d2', t_ill + 0.2, 0.55, 14)
    js += pop('#s8-url', cue(sid, 'advice', 1, -0.5), 0.6, 14)
    return scene(sid, '', body, js, d, True, False)


scenes = {}
for fn, key in [(s1, 's1'), (s2, 's2'), (s3, 's3'), (s4, 's4'), (s5, 's5'), (s6, 's6'), (s7, 's7'), (s8, 's8')]:
    scenes[key] = fn()
bad = []
for (i, text, x, w, size, box) in REG:
    if size < 44: bad.append(('font<44', i, size))
    if box is not None and w > box: bad.append(('wider than its box', i, round(w), box))
    elif box is None and x + w > 1860: bad.append(('past right margin', i, round(x + w)))
for b in bad: print('LAYOUT WARNING', b)
os.makedirs(os.path.join(here, 'compositions'), exist_ok=True)
for k, v in scenes.items():
    open(os.path.join(here, 'compositions', k + '.html'), 'w').write(v)

total = T['total']
hosts = ''
for sc in S['scenes']:
    t = TIM[sc['id']]
    hosts += (f'<div id="{sc["id"]}" data-composition-id="{sc["id"]}" data-composition-src="compositions/{sc["id"]}.html" '
              f'data-start="{t["start"]}" data-duration="{t["dur"]}" data-track-index="1" data-track-kind="graphics" '
              f'data-width="1920" data-height="1080"></div>\n')
index = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1920, height=1080" />
<script src="assets/gsap.min.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1920px; height:1080px; overflow:hidden; background:{PAPER}; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1920" data-height="1080">
{hosts}<audio id="narration" src="assets/narration.wav" data-start="0" data-duration="{total}" data-track-index="2" data-volume="1"></audio>
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
window.__timelines['main'] = tl;
</script>
</body>
</html>
"""
open(os.path.join(here, 'index.html'), 'w').write(index)
json.dump({'total': total, 'end_card_start': TIM['s8']['start']}, open(os.path.join(here, 'build/cards.json'), 'w'))
print('ok', total)
