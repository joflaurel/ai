---
name: motion-graphics
description: Make code-generated motion graphics (logo or shape reveals, star draw-on) with motion-graphics/logo_reveal.py and star_draw.py. Use when asked for a logo reveal, intro, animated shape or motion graphic.
---

# Motion graphics

- Logo/shape reveal: `py motion-graphics/logo_reveal.py --image <png> --text "<TEXT>" [--vertical]`
  - The image can be a dark shape on white (e.g. a Paint drawing) or a transparent PNG. Save reusable images to `motion-graphics/assets/`.
- Star draw-on: `py motion-graphics/star_draw.py`
- Output goes to `motion-graphics/output/`.

Before saying it's done, grab a frame to check it, e.g.
`ffmpeg -ss 5.5 -i <video> -frames:v 1 check.png`, and look at the image.

For new animations, copy `logo_reveal.py` as a starting point: timing lives in `frame(i)` as eased
time windows (e.g. `ease_io((t - 2.4) / 1.0)` is a 1-second move starting at 2.4s).
