"""
Logo / shape reveal motion graphic (8s).
Drop-in bounce -> shockwave + particles -> card flip to gold -> shine -> title -> zoom-through.

Usage:
  py logo_reveal.py                                   (uses assets/spade.png, text SPADES)
  py logo_reveal.py --image assets/mylogo.png --text "MY BRAND"
  py logo_reveal.py --vertical                        (1080x1920 for Reels/TikTok)

--image: a dark shape on a light background (like a Paint drawing) or a PNG with transparency.
"""
import argparse, math, random, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("--image", default=str(HERE / "assets" / "spade.png"))
ap.add_argument("--text", default="SPADES")
ap.add_argument("--out", default=None)
ap.add_argument("--vertical", action="store_true")
args = ap.parse_args()

W, H = (1080, 1920) if args.vertical else (1920, 1080)
FPS, DUR = 30, 8.0
N = int(FPS * DUR)
OUT = args.out or str(HERE / "output" / (Path(args.image).stem + ("_reveal_9x16.mp4" if args.vertical else "_reveal.mp4")))
Path(OUT).parent.mkdir(parents=True, exist_ok=True)

# ---------- load the Paint spade as a clean alpha mask ----------
img = Image.open(args.image).convert("RGBA")
alpha = np.array(img.split()[3])
if alpha.min() < 250:            # transparent PNG: use its alpha
    shape = alpha > 128
else:                            # drawing on white: dark pixels are the shape
    shape = np.array(img.convert("L")) < 128
ys, xs = np.where(shape)
if len(xs) == 0:
    sys.exit("Couldn't find a shape in that image.")
pad = 6
x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad)
mask = Image.fromarray((shape[y0:ys.max() + pad, x0:xs.max() + pad] * 255).astype("uint8"))
BASE_H = 620 if not args.vertical else 640
if mask.width / mask.height > 1.3:      # wide logos: limit by width instead
    BASE_H = int(BASE_H * 1.3 * mask.height / mask.width)
mask = mask.resize((max(1, int(mask.width * BASE_H / mask.height)), BASE_H), Image.LANCZOS)
mask = mask.filter(ImageFilter.GaussianBlur(1.2))  # soften Paint jaggies

def gold_fill(size):
    w, h = size
    g = np.linspace(0, 1, h)[:, None]
    r = 255 - 25 * g; gg = 222 - 90 * g; b = 110 - 80 * g
    arr = np.stack([np.repeat(r, w, 1), np.repeat(gg, w, 1), np.repeat(b, w, 1)], -1)
    return Image.fromarray(arr.clip(0, 255).astype("uint8"), "RGB")

GOLD = gold_fill(mask.size)
CREAM = Image.new("RGB", mask.size, (245, 240, 230))

# ---------- easing ----------
clamp = lambda x: max(0.0, min(1.0, x))
def ease_io(t): t = clamp(t); return 0.5 - 0.5 * math.cos(math.pi * t)
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 3
def ease_in(t): t = clamp(t); return t ** 3
def elastic(t):
    t = clamp(t)
    if t in (0, 1): return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1

# ---------- background ----------
yy, xx = np.mgrid[0:H, 0:W]
d = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
bgv = (1 - np.clip(d * 1.6, 0, 1)) ** 1.5
BG = np.stack([10 + 30 * bgv, 9 + 18 * bgv, 14 + 14 * bgv], -1).astype("uint8")
BG = Image.fromarray(BG, "RGB")

# tiled pattern of small spades
_k = 70 / max(mask.width, mask.height)   # fit the tile inside a 70x70 box
tile_m = mask.resize((max(1, int(mask.width * _k)), max(1, int(mask.height * _k))), Image.LANCZOS)
TS = 180
PATTERN = Image.new("L", (W + 2 * TS, H + 2 * TS), 0)
for j in range(0, H + 2 * TS, TS):
    for i in range(0, W + 2 * TS, TS):
        off = TS // 2 if (j // TS) % 2 else 0
        PATTERN.paste(tile_m, (i + off - tile_m.width // 2 + TS // 2, j + TS // 2 - tile_m.height // 2), tile_m)

def load_font(size):
    for f in ["arialbd.ttf", "C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
              "DejaVuSans-Bold.ttf", "/Library/Fonts/Arial Bold.ttf"]:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()
WORD = args.text.upper()
FONT = load_font(96 if len(WORD) <= 10 else max(48, int(96 * 10 / len(WORD))))

random.seed(3)
PARTS = [(random.uniform(0, 2 * math.pi), random.uniform(350, 900), random.uniform(3, 9), random.uniform(0.7, 1.3)) for _ in range(70)]

def spade_layer(scale, rot_deg, hscale, fill):
    w, h = int(mask.width * scale), int(mask.height * scale)
    if w < 2 or h < 2: return None
    m = mask.resize((w, h), Image.BILINEAR)
    f = fill.resize((w, h), Image.BILINEAR).convert("RGBA")
    f.putalpha(m)
    if rot_deg: f = f.rotate(rot_deg, resample=Image.BICUBIC, expand=True)
    if hscale < 0.999:
        nw = max(1, int(f.width * hscale)); f = f.resize((nw, f.height), Image.BILINEAR)
    return f

def frame(i):
    t = i / FPS
    canvas = BG.copy().convert("RGBA")

    # background pattern (from 4.4s), drifting diagonally
    pa = ease_io((t - 4.4) / 1.0) * 0.07
    if pa > 0:
        sh = int((t * 40) % TS)
        pm = PATTERN.crop((TS - sh, TS - sh, TS - sh + W, TS - sh + H)).point(lambda v: int(v * pa))
        gl = Image.new("RGBA", (W, H), (255, 205, 90, 0)); gl.putalpha(pm)
        canvas.alpha_composite(gl)

    # --- main spade motion ---
    drop = elastic(t / 1.15)
    scale = 0.05 + 0.95 * drop
    rot = -25 * (1 - ease_out(t / 1.0))
    cx, cy = W / 2, H / 2

    # flip 2.4-3.4: squash horizontally, swap cream -> gold at midpoint
    fp = clamp((t - 2.4) / 1.0)
    hscale = abs(math.cos(math.pi * ease_io(fp))) if 0 < fp < 1 else 1.0
    fill = GOLD if fp >= 0.5 else CREAM

    # move up + shrink for title 4.0-4.8
    up = ease_io((t - 4.0) / 0.8)
    scale *= 1 - 0.28 * up
    cy -= 95 * up
    # gentle float
    if t > 4.8: cy += 8 * math.sin((t - 4.8) * 2.4)

    # outro zoom-through 6.9-7.7
    zoom = ease_in((t - 6.9) / 0.8)
    scale *= 1 + 14 * zoom
    cy -= 0.12 * mask.height * scale * zoom  # aim zoom into the body of the spade

    # camera shake on impact
    if 0.95 < t < 1.35:
        k = (1.35 - t) / 0.4
        cx += 10 * k * math.sin(t * 90); cy += 8 * k * math.cos(t * 77)

    # shockwave rings 1.0-2.1
    rd = ImageDraw.Draw(canvas)
    for delay in (0.0, 0.18):
        p = clamp((t - 1.0 - delay) / 1.0)
        if 0 < p < 1:
            r = 120 + 900 * ease_out(p)
            al = int(200 * (1 - p))
            ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(ring).ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 210, 110, al), width=int(10 * (1 - p)) + 2)
            canvas.alpha_composite(ring)

    # particle burst 1.0-2.3
    pp = (t - 1.0) / 1.3
    if 0 < pp < 1:
        for ang, spd, sz, life in PARTS:
            q = clamp(pp / life)
            if q >= 1: continue
            dist = spd * ease_out(q)
            x = cx + math.cos(ang) * dist; y = cy + math.sin(ang) * dist + 120 * q * q
            s = sz * (1 - q)
            rd.ellipse([x - s, y - s, x + s, y + s], fill=(255, 220, 130, int(255 * (1 - q))))

    layer = spade_layer(scale, rot, hscale, fill)
    if layer is not None:
        px, py = int(cx - layer.width / 2), int(cy - layer.height / 2)
        # glow (computed small for speed)
        if zoom < 0.5:
            ga = 0.35 + 0.45 * (fp >= 0.5)
            small = layer.split()[3].resize((max(1, layer.width // 4), max(1, layer.height // 4)))
            small = small.filter(ImageFilter.GaussianBlur(10)).resize(layer.size, Image.BILINEAR)
            glow = Image.new("RGBA", layer.size, (255, 200, 80, 0)); glow.putalpha(small.point(lambda v: int(v * ga)))
            gx, gy = px, py
            big = Image.new("RGBA", (W, H), (0, 0, 0, 0)); big.paste(glow, (gx, gy), glow)
            canvas.alpha_composite(big)

        # shine sweep across gold 3.5-4.3 and again 5.6-6.3
        for s0 in (3.5, 5.6):
            sp = (t - s0) / 0.75
            if 0 < sp < 1:
                band = Image.new("L", layer.size, 0)
                bx = -layer.width * 0.6 + sp * layer.width * 2.2
                ImageDraw.Draw(band).polygon([(bx, 0), (bx + 90, 0), (bx + 90 - layer.height * 0.5, layer.height), (bx - layer.height * 0.5, layer.height)], fill=170)
                band = band.filter(ImageFilter.GaussianBlur(12))
                band = ImageChops.multiply(band, layer.split()[3])
                white = Image.new("RGBA", layer.size, (255, 255, 240, 0)); white.putalpha(band)
                layer = layer.copy(); layer.alpha_composite(white)

        top = Image.new("RGBA", (W, H), (0, 0, 0, 0)); top.paste(layer, (px, py), layer)
        canvas.alpha_composite(top)

    # title: letters rise in staggered, 4.5-5.6
    if 4.4 < t < 7.2:
        tl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(tl)
        track = 28
        widths = [FONT.getbbox(c)[2] - FONT.getbbox(c)[0] for c in WORD]
        total = sum(widths) + track * (len(WORD) - 1)
        x = W / 2 - total / 2
        base_y = 840 if not args.vertical else 1380
        fade_out = 1 - ease_io((t - 6.8) / 0.4)
        for k, c in enumerate(WORD):
            q = ease_out((t - 4.5 - k * 0.08) / 0.55)
            if q > 0:
                td.text((x, base_y + 60 * (1 - q)), c, font=FONT, fill=(250, 228, 160, int(255 * q * fade_out)), anchor="lt")
            x += widths[k] + track
        # underline draw-on
        lq = ease_io((t - 5.2) / 0.6) * fade_out
        if lq > 0:
            lw = total * lq
            td.rectangle([W / 2 - lw / 2, base_y + 125, W / 2 + lw / 2, base_y + 129], fill=(255, 205, 90, int(230 * fade_out)))
        canvas.alpha_composite(tl)

    out = canvas.convert("RGB")
    # fade in from black / to black at end
    fade = min(1.0, t / 0.3, (DUR - t) / 0.35)
    if zoom > 0.6:
        fade = min(fade, 1 - ease_io((t - 7.45) / 0.3))
    if fade < 1:
        out = Image.blend(Image.new("RGB", (W, H)), out, max(0.0, fade))
    return out

proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
                         "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
for i in range(N):
    proc.stdin.write(frame(i).tobytes())
    if i % 30 == 0:
        print(f"  rendering... {i * 100 // N}%", end="\r")
proc.stdin.close(); proc.wait()
print(f"\nSaved: {OUT}")
