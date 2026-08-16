#!/usr/bin/env python3
"""Generate 50–950 color ladders (Tailwind stops) in OKLCH, fitted to the design
exemplar's anchor colors. Anchors are kept exact; missing stops are interpolated
in OKLCH along the ladder. Prints CSS custom properties.

    python3 scripts/palette.py > /tmp/palette.css
"""
import math

STOPS=[50,100,200,300,400,500,600,700,800,900,950]
# Target lightness (OKLCH L) per stop, Tailwind-like
L_TARGET={50:.985,100:.965,200:.92,300:.86,400:.76,500:.66,600:.56,700:.47,800:.39,900:.31,950:.22}

def hex2rgb(h): h=h.lstrip('#'); return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))
def srgb2lin(c): return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
def lin2srgb(c): c=max(0,min(1,c)); return 12.92*c if c<=0.0031308 else 1.055*c**(1/2.4)-0.055
def rgb2oklch(rgb):
    r,g,b=[srgb2lin(c) for c in rgb]
    l=0.4122214708*r+0.5363325363*g+0.0514459929*b
    m=0.2119034982*r+0.6806995451*g+0.1073969566*b
    s=0.0883024619*r+0.2817188376*g+0.6299787005*b
    l_,m_,s_=l**(1/3),m**(1/3),s**(1/3)
    L=0.2104542553*l_+0.7936177850*m_-0.0040720468*s_
    a=1.9779984951*l_-2.4285922050*m_+0.4505937099*s_
    b2=0.0259040371*l_+0.7827717662*m_-0.8086757660*s_
    C=math.hypot(a,b2); h=math.degrees(math.atan2(b2,a))%360
    return L,C,h
def oklch2hex(L,C,h):
    a=C*math.cos(math.radians(h)); b=C*math.sin(math.radians(h))
    l_=L+0.3963377774*a+0.2158037573*b; m_=L-0.1055613458*a-0.0638541728*b; s_=L-0.0894841775*a-1.2914855480*b
    l,m,s=l_**3,m_**3,s_**3
    r=+4.0767416621*l-3.3077115913*m+0.2309699292*s
    g=-1.2684380046*l+2.6097574011*m-0.3413193965*s
    b=-0.0041960863*l-0.7034186147*m+1.7076147010*s
    return '#%02x%02x%02x'%tuple(round(lin2srgb(v)*255) for v in (r,g,b))

# Exemplar anchors (exact hex from the design), keyed by Tailwind stop.
FAMILIES={
 'pine':   {100:'#e3ece8',200:'#c0d3ca',300:'#8bb0a0',400:'#5b8c78',500:'#3d6d5a',600:'#2e5647',700:'#254739',800:'#1b352b',900:'#12241d'},
 'terra':  {100:'#faeae1',200:'#f2d5c5',300:'#e7b299',400:'#d98f6d',500:'#c96f4a',600:'#b85c38',700:'#9c4629',800:'#7d3620',900:'#5e2617'},
 'ochre':  {100:'#fcf5e6',200:'#f6e8c8',300:'#ecd39c',400:'#dcb768',500:'#c89a3c',600:'#a97a22',700:'#8a6318'},
 'oxblood':{100:'#f9ecea',200:'#eccfc9',500:'#a24f45',600:'#8c3a32',700:'#6b241f'},
 # warm neutral (paper → sand → stone → ink), one ramp
 'sepia':  {50:'#fffdf8',100:'#faf6ef',200:'#f4ede1',300:'#e9dfcf',400:'#dbcdb6',500:'#c4b49b',600:'#a3937c',700:'#7d7060',800:'#544a3e',900:'#3a332b',950:'#2a2520'},
}

def lerp(a,b,t): return a+(b-a)*t
def hlerp(a,b,t):
    d=((b-a+180)%360)-180; return (a+d*t)%360

out=[]
for fam,anch in FAMILIES.items():
    known={s:rgb2oklch(hex2rgb(h)) for s,h in anch.items()}
    ks=sorted(known)
    vals={}
    for s in STOPS:
        if s in known: vals[s]=anch[s]; continue
        # interpolate C,h between neighbouring anchors on the stop axis; L from target ladder
        lo=max([k for k in ks if k<s],default=None); hi=min([k for k in ks if k>s],default=None)
        if lo is None: lo=hi
        if hi is None: hi=lo
        if lo==hi:
            L0,C0,h0=known[lo]; L=L_TARGET[s]
            # extrapolate: taper chroma toward the ends, keep lightness monotonic
            prev=STOPS[STOPS.index(s)-1] if s>lo else None
            if prev is not None:
                Lp=rgb2oklch(hex2rgb(vals[prev]))[0]; L=min(L,Lp-0.045)
            C=C0*(0.55 if s in (50,950) else 0.8); h=h0
        else:
            t=(s-lo)/(hi-lo)
            L=lerp(known[lo][0],known[hi][0],t); C=lerp(known[lo][1],known[hi][1],t); h=hlerp(known[lo][2],known[hi][2],t)
        vals[s]=oklch2hex(L,C,h)
    out.append(f"  /* {fam} */")
    for s in STOPS:
        L,C,h=rgb2oklch(hex2rgb(vals[s]))
        out.append(f"  --{fam}-{s}: {vals[s]};   /* oklch({L:.3f} {C:.3f} {h:.0f}) */")
print("\n".join(out))
