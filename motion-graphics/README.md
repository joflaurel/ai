# Motion graphics

Motion graphics made with Python code (Pillow + NumPy + ffmpeg). Change the timing, colors or text and re-render in seconds.

## logo_reveal.py (8 seconds)
Drop-in bounce -> camera shake, gold rings and particles -> card flip to gold -> shine -> title letters rise -> zoom-through to black.

```powershell
py logo_reveal.py                                          # spade from assets/, text "SPADES"
py logo_reveal.py --image assets\my_logo.png --text "MY BRAND"
py logo_reveal.py --vertical                               # 1080x1920 for Reels/TikTok/Shorts
```

`--image` can be a dark drawing on a white background (like a Paint drawing) or a PNG with a transparent background.
Put reusable images in `assets/` (they are the only images git keeps).

## star_draw.py (7 seconds)
A glowing pen draws a five-point star, it fills gold, spins and settles.

```powershell
py star_draw.py
```

Renders go to `output/` (ignored by git). Import them into Premiere or CapCut like any clip.
