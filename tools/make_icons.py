"""ORDO app icon: a heavy ivory ring on obsidian, closed by one ultramarine segment (the day, kept).

Writes the web icons (repo root) and the Android launcher icons (android/app/src/main/res/mipmap-*).
"""
import math, os
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OBSIDIAN_TOP, OBSIDIAN_BOT = (22, 24, 33), (6, 7, 10)
IVORY = (243, 241, 236)
ULTRA = (110, 126, 255)

def render(size, full_bleed=False, scale=1.0, preview=False):
    S = size * 4
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # background: vertical obsidian gradient with a soft top sheen
    bg = Image.new("RGBA", (S, S))
    px = bg.load()
    for y in range(S):
        t = y / (S - 1)
        c = tuple(int(OBSIDIAN_TOP[i] * (1 - t) + OBSIDIAN_BOT[i] * t) for i in range(3))
        for x in range(S):
            px[x, y] = c + (255,)
    sheen = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sheen).ellipse([-S * .2, -S * .75, S * 1.2, S * .45], fill=(120, 132, 255, 34))
    bg = Image.alpha_composite(bg, sheen.filter(ImageFilter.GaussianBlur(S * .08)))
    mask = Image.new("L", (S, S), 0)
    if full_bleed: ImageDraw.Draw(mask).rectangle([0, 0, S, S], fill=255)
    else: ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.23), fill=255)
    im.paste(bg, (0, 0), mask)

    # the ring
    d = ImageDraw.Draw(im)
    c = S / 2
    r_out = S * 0.335 * scale
    w = S * 0.104 * scale
    box = [c - r_out, c - r_out, c + r_out, c + r_out]
    gap = 28                                  # degrees of air either side of the blue segment
    seg_start, seg_len = -90 + 18, 46          # the kept segment, just past 12 o'clock
    d.arc(box, seg_start + seg_len + gap, seg_start - gap + 360, fill=IVORY, width=int(w))
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glow).arc(box, seg_start, seg_start + seg_len, fill=ULTRA + (150,), width=int(w * 1.15))
    im = Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(S * .02)))
    d = ImageDraw.Draw(im)
    d.arc(box, seg_start, seg_start + seg_len, fill=ULTRA, width=int(w))
    # round the ivory ends
    rr = w / 2
    for ang in (seg_start + seg_len + gap, seg_start - gap):
        a = math.radians(ang)
        ex, ey = c + (r_out - rr) * math.cos(a), c + (r_out - rr) * math.sin(a)
        d.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], fill=IVORY)
    for ang in (seg_start, seg_start + seg_len):
        a = math.radians(ang)
        ex, ey = c + (r_out - rr) * math.cos(a), c + (r_out - rr) * math.sin(a)
        d.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], fill=ULTRA)
    return im.resize((size, size), Image.LANCZOS)

def badge(size):
    """Monochrome notification badge: the ring only, white on transparent."""
    S = size * 4
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im); c = S / 2; r = S * .4; w = S * .16
    d.arc([c - r, c - r, c + r, c + r], 0, 360, fill=(255, 255, 255, 255), width=int(w))
    return im.resize((size, size), Image.LANCZOS)

if __name__ == "__main__":
    render(512).save(os.path.join(ROOT, "icon-512.png"))
    render(192).save(os.path.join(ROOT, "icon-192.png"))
    render(180).save(os.path.join(ROOT, "apple-touch-icon.png"))
    render(512, full_bleed=True, scale=.82).save(os.path.join(ROOT, "icon-maskable-512.png"))
    render(64).save(os.path.join(ROOT, "favicon.png"))
    badge(72).save(os.path.join(ROOT, "badge-72.png"))
    res = os.path.join(ROOT, "android", "app", "src", "main", "res")
    for dpi, s in {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}.items():
        render(s).save(os.path.join(res, f"mipmap-{dpi}", "ic_launcher.png"))
    render(1024).save(os.path.join(ROOT, "tools", "build", "icon-1024.png")) if os.path.isdir(os.path.join(ROOT, "tools", "build")) else None
    print("icons written")
