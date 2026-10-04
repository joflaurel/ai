"""
Star draw-on animation (7s): pen draws a 5-point star, gold fill, spin, settle.
Usage:  py star_draw.py            -> output/star.mp4
"""
import math, random, subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent
(HERE / "output").mkdir(exist_ok=True)
from PIL import Image, ImageDraw, ImageFilter

W, H, FPS, DUR = 1920, 1080, 30, 7.0
SS = 2  # supersample
N = int(FPS * DUR)
CX, CY, R = W / 2, H / 2 + 20, 380

# Same geometry as the Paint drawing: 5 outer points, drawn in order 0-2-4-1-3-0
def verts(angle=0.0, scale=1.0):
    pts = []
    for k in range(5):
        a = math.radians(-90 + 72 * k) + angle
        pts.append((CX + R * scale * math.cos(a), CY + R * scale * math.sin(a)))
    return pts

ORDER = [0, 2, 4, 1, 3, 0]

def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)

def ease_out_back(t):
    t = max(0.0, min(1.0, t)); c = 1.7
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2

def fill_polygon(pts):
    # outer + inner points of a pentagram so the fill is solid
    outer = pts
    inner = []
    ri = R * 0.382
    cx = sum(p[0] for p in outer) / 5; cy = sum(p[1] for p in outer) / 5
    for k in range(5):
        a = math.atan2(outer[k][1] - cy, outer[k][0] - cx) + math.radians(36)
        s = math.hypot(outer[k][0] - cx, outer[k][1] - cy) / R
        inner.append((cx + ri * s * math.cos(a), cy + ri * s * math.sin(a)))
    poly = []
    for k in range(5):
        poly += [outer[k], inner[k]]
    return poly

def background():
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(12 + 18 * t), int(14 + 10 * t), int(38 + 30 * t)))
    return bg

BG = background()
random.seed(7)
SPARKS = [(random.uniform(0, W), random.uniform(0, H), random.uniform(0, 6.28), random.uniform(1.5, 4)) for _ in range(90)]
GOLD = (255, 205, 60)

def frame(i):
    t = i / FPS
    img = BG.copy()

    # twinkling background stars
    d0 = ImageDraw.Draw(img)
    for x, y, ph, s in SPARKS:
        b = 0.5 + 0.5 * math.sin(t * 3 + ph)
        c = int(70 + 150 * b)
        d0.ellipse([x - s / 2, y - s / 2, x + s / 2, y + s / 2], fill=(c, c, min(255, c + 30)))

    # timeline
    draw_p = ease_in_out(t / 2.6)                       # 0-2.6s draw on
    fill_a = ease_in_out((t - 2.5) / 0.9)              # 2.5-3.4s fill fades in
    spin = ease_in_out((t - 3.4) / 2.2) * 2 * math.pi  # 3.4-5.6s full spin
    pop = 1.0 + 0.12 * math.sin(math.pi * max(0, min(1, (t - 3.4) / 2.2)))
    settle = ease_out_back((t - 5.6) / 0.8) if t > 5.6 else 0
    scale = pop if t < 5.6 else 1.0 + 0.06 * settle

    pts = verts(spin, scale)
    layer = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    S = lambda p: (p[0] * SS, p[1] * SS)

    if fill_a > 0:
        d.polygon([S(p) for p in fill_polygon(pts)], fill=GOLD + (int(255 * fill_a),))

    # progressive stroke along the 5 segments
    segs = [(pts[ORDER[j]], pts[ORDER[j + 1]]) for j in range(5)]
    total = draw_p * 5
    line_col = tuple(int(255 * (1 - fill_a) + c * fill_a) for c in (255, 255, 255)) if fill_a < 1 else (255, 240, 180)
    for j, (a, b) in enumerate(segs):
        f = max(0.0, min(1.0, total - j))
        if f <= 0: break
        e = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        d.line([S(a), S(e)], fill=line_col + (255,), width=10 * SS, joint="curve")
        if f < 1:  # glowing pen tip
            r = 14 * SS
            d.ellipse([e[0] * SS - r, e[1] * SS - r, e[0] * SS + r, e[1] * SS + r], fill=(255, 255, 255, 255))

    layer = layer.resize((W, H), Image.LANCZOS)
    glow = layer.filter(ImageFilter.GaussianBlur(28))
    glow_strength = 0.6 + 0.6 * fill_a
    a = glow.split()[3].point(lambda v: int(min(255, v * glow_strength)))
    glow_col = Image.new("RGBA", (W, H), (255, 210, 90, 0)); glow_col.putalpha(a)
    out = img.convert("RGBA")
    out.alpha_composite(glow_col)
    out.alpha_composite(layer)

    # fade in / out
    fade = min(1.0, t / 0.4, (DUR - t) / 0.5)
    if fade < 1:
        out = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), out, max(0, fade))
    return out.convert("RGB")

proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                         "-crf", "18", "-movflags", "+faststart", str(HERE / "output" / "star.mp4")], stdin=subprocess.PIPE)
for i in range(N):
    f = frame(i)
    proc.stdin.write(f.tobytes())
proc.stdin.close(); proc.wait()
print("Saved:", HERE / "output" / "star.mp4")
