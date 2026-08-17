#!/usr/bin/env python3
"""WCAG contrast audit for the semantic token pairs used by the templates.
Reads assets/css/02-tokens.css, resolves var() chains for :root (light) and
:root.dark, and prints ratios with AA/AAA verdicts.  python3 scripts/contrast.py"""
import re, sys, pathlib

css = pathlib.Path(__file__).resolve().parent.parent.joinpath('assets/css/02-tokens.css').read_text()
def block(sel):
    out = {}
    for m in re.finditer(r'(^|\n)\s*' + re.escape(sel) + r'\s*\{(.*?)\n\}', css, re.S):
        for k, v in re.findall(r'(--[\w-]+)\s*:\s*([^;]+);', m.group(2)):
            out[k] = v.strip()
    return out
root = block(':root'); dark = dict(root); dark.update(block(':root.dark'))

def resolve(tokens, v, depth=0):
    m = re.fullmatch(r'var\((--[\w-]+)\)', v.strip())
    if m and depth < 20: return resolve(tokens, tokens[m.group(1)], depth+1)
    m = re.fullmatch(r'oklch\(from var\((--[\w-]+)\) l c h / ([\d.]+)\)', v.strip())
    if m: return (resolve(tokens, tokens[m.group(1)]), float(m.group(2)))
    return v.strip()
def hex2rgb(h): h=h.lstrip('#'); return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))
def lum(rgb):
    f=lambda c: c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4
    r,g,b=[f(c) for c in rgb]; return .2126*r+.7152*g+.0722*b
def blend(fg, bg, a): return tuple(f*a+b*(1-a) for f,b in zip(fg,bg))
def ratio(fg, bg):
    l1,l2=lum(fg),lum(bg); hi,lo=max(l1,l2),min(l1,l2); return (hi+.05)/(lo+.05)

# (label, fg token, bg token, size class, [alpha of fg])  size: 'text' (AA 4.5/AAA 7) | 'large' (AA 3/AAA 4.5) | 'ui' (AA 3)
PAIRS = [
 ('body on page','--text-body','--surface-page','text'),
 ('body on raised/card','--text-body','--surface-raised','text'),
 ('body on sunken','--text-body','--surface-sunken','text'),
 ('body on accent (marked card)','--text-body','--surface-accent','text'),
 ('heading on page','--text-heading','--surface-page','text'),
 ('heading on card','--text-heading','--surface-card','text'),
 ('heading on accent (marked card)','--text-heading','--surface-accent','text'),
 ('muted on page (notes, rail)','--text-muted','--surface-page','text'),
 ('muted on card (descriptions)','--text-muted','--surface-card','text'),
 ('muted on sunken (tailor note)','--text-muted','--surface-sunken','text'),
 ('muted on accent (marked card desc)','--text-muted','--surface-accent','text'),
 ('muted on marginalia (sponsor blurb)','--text-muted','--surface-marginalia','text'),
 ('faint on raised (placeholder, decorative icons)','--text-faint','--surface-raised','text'),
 ('link on page','--text-link','--surface-page','text'),
 ('link on card','--text-link','--surface-card','text'),
 ('link on marginalia (strip, sponsor eyebrow)','--text-link','--surface-marginalia','text'),
 ('tag-accent: link on accent','--text-link','--surface-accent','text'),
 ('on-inverse on inverse (slot header)','--text-on-inverse','--surface-inverse','text'),
 ('on-inverse-muted on inverse (day eyebrow)','--text-on-inverse-muted','--surface-inverse','text'),
 ('on-inverse-soft on inverse (slot sub)','--text-on-inverse-soft','--surface-inverse','text'),
 ('on-accent on primary button','--text-on-accent','--action-primary','text'),
 ('on-accent on primary hover','--text-on-accent','--action-primary-hover','text'),
 ('on-accent on accent button','--text-on-accent','--action-accent','text'),
 ('on-accent on accent hover','--text-on-accent','--action-accent-hover','text'),
 ('warning text on warning surface (notice, match tag)','--status-warning','--status-warning-surface','text'),
 ('mark-on (star) on card','--mark-on','--surface-card','ui'),
 ('mark-off (star) on card','--mark-off','--surface-card','ui'),
 ('border-default on page (decorative card/tag edge)','--border-default','--surface-page','decor'),
 ('border-strong (secondary button) on page','--border-strong','--surface-page','ui'),
 ('rule-accent on page','--rule-accent','--surface-page','ui'),
 ('dimmed card: muted title/prose on sunken','--text-muted','--surface-sunken','text'),
 ('field border (strong) on raised','--border-strong','--surface-raised','ui'),
 ('tag-accent chip inside dimmed card: link on accent','--text-link','--surface-accent','text'),
]
def verdict(r, size):
    if size == 'decor': return 'n/a '
    aa, aaa = {'text':(4.5,7),'large':(3,4.5),'ui':(3,4.5)}[size]
    return 'AAA' if r>=aaa else ('AA' if r>=aa else 'FAIL')
for name, toks in (('LIGHT', root), ('DARK', dark)):
    print(f'\n== {name} ==')
    for p in PAIRS:
        label, fgk, bgk, size = p[:4]; alpha = p[4] if len(p)>4 else 1
        fg = resolve(toks, toks[fgk]); bg = resolve(toks, toks[bgk])
        if isinstance(fg, tuple): fg = fg[0]
        if isinstance(bg, tuple): bg = bg[0]
        fgc, bgc = hex2rgb(fg), hex2rgb(bg)
        if alpha < 1: fgc = blend(fgc, bgc, alpha)
        r = ratio(fgc, bgc)
        v = verdict(r, size)
        flag = '' if v!='FAIL' else '  <-- FAIL'
        print(f'{r:5.2f}  {v:4}  {label:48} {fg} on {bg}{flag}')
