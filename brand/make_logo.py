# MatRAG logo: geometric stroke letters, one gradient, crystal on the M, and an SHG wave (λ, then λ/2).
import sys
out = sys.argv[1]
def wave(x0, x1, period, amp, y=72):
    n = round((x1 - x0) / (period / 2))
    h = period / 2
    return f"M{x0} {y}q{h/2:g} {-2*amp:g} {h:g} 0" + f"t{h:g} 0" * (n - 1), x0 + n * h
w1, xe = wave(100, 300, 56, 7)
w2, _ = wave(xe, 548, 28, 5)
GRAD = ('<linearGradient id="g" gradientUnits="userSpaceOnUse" x1="20" x2="540"><stop offset="0" stop-color="#6fe0e8"/>'
        '<stop offset=".27" stop-color="#a6e2f0"/><stop offset=".45" stop-color="#6c95d6"/><stop offset=".62" stop-color="#6356bd"/>'
        '<stop offset=".8" stop-color="#b2b6ec"/><stop offset="1" stop-color="#a383dd"/></linearGradient>')
CRYSTAL = ('<path fill="#bdf3f4" d="M65 0 52 20h13z"/><path fill="#a9cdf0" d="M65 0 78 20H65z"/>'
           '<path fill="#86bfe3" d="M52 20h13v32z"/><path fill="#9a8ee0" d="M78 20H65v32z"/>')
M = '<path d="M29 120V30l36 52 36-52v90" stroke-linejoin="miter"/>'
LETTERS = (M + '<circle cx="159" cy="94" r="26"/><path d="M185 59v61M225 34v66q0 20 22 20M206 68h42'
           'M272 120V33h34a25 25 0 0 1 0 50h-34m29 0 30 37M362 120l35-96 35 96M521.6 44.4A39 39 0 1 0 533 72h-31"/>')
WEDGE = '<path fill="url(#g)" d="m374 100 58-30-8 14z"/>'
def svg(vb, body, extra=""):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">{extra}{body}</svg>'
strokes = f'<g fill="none" stroke="url(#g)" stroke-width="18">{LETTERS}</g>'
def word(wave_color):
    return svg("10 -12 545 142", f'<defs>{GRAD}</defs><path fill="none" stroke="{wave_color}" stroke-width="2.6" d="{w1}{w2}"/>{strokes}{WEDGE}{CRYSTAL}')
open(f"{out}/matrag-logo-light.svg", "w").write(word("#79bfe0"))   # on white
open(f"{out}/matrag-logo-dark.svg", "w").write(word("#c4ecf7"))    # on dark
# icon: the M and its crystal on a dark rounded tile (favicon, Telegram bot picture)
ig = ('<linearGradient id="g" gradientUnits="userSpaceOnUse" x1="20" x2="110" y1="30" y2="120"><stop offset="0" stop-color="#6fe0e8"/>'
      '<stop offset=".55" stop-color="#a6c8f0"/><stop offset="1" stop-color="#8d7fe0"/></linearGradient>')
icon = svg("0 0 130 130", f'<defs>{ig}</defs><rect width="130" height="130" rx="28" fill="#141b2d"/>'
           f'<g transform="translate(16 20) scale(.75)"><g fill="none" stroke="url(#g)" stroke-width="18">{M}</g>{CRYSTAL}</g>')
open(f"{out}/matrag-icon.svg", "w").write(icon)
