# Lifts a plane off a flat background (the poster's red, the comic's sky) into a transparent PNG:
# background = pixels near the backdrop colour that connect to the image border; the edge pixels
# get partial alpha and have the backdrop colour taken back out so no red or blue fringe is left.
import sys
import numpy as np
from PIL import Image
from scipy import ndimage


def cutout(src, dst, clear_boxes=(), near=34, far=90):
    im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    bg = np.median(np.concatenate([im[:20, :].reshape(-1, 3), im[-20:, :].reshape(-1, 3)]), axis=0)
    for x0, y0, x1, y1 in clear_boxes:  # stray clouds etc.
        im[y0:y1, x0:x1] = bg
    dist = np.sqrt(((im - bg) ** 2).sum(axis=2))
    lab, _ = ndimage.label(dist < near)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    background = np.isin(lab, list(border))
    alpha = np.clip((dist - near) / (far - near), 0, 1)
    edge = ndimage.binary_dilation(background, iterations=3) & ~background
    a = np.where(background, 0.0, np.where(edge, alpha, 1.0))
    keep = a > 0.02
    rgb = im.copy()
    rgb[keep] = (im[keep] - (1 - a[keep, None]) * bg) / a[keep, None]
    out = np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)
    ys, xs = np.where(a > 0.5)
    pad = 12
    box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0), xs.max() + pad, ys.max() + pad)
    Image.fromarray(out, "RGBA").crop(box).save(dst)
    print(dst, "bg", bg.round(), "crop", box)


if __name__ == "__main__":
    # Poster: drop the caption under the plane before keying (it sits below row 1150).
    poster = Image.open("art/poster-united-737max9.jpg")
    poster.crop((0, 0, poster.width, 1130)).save("out/_poster-top.png")
    cutout("out/_poster-top.png", "art/cut-poster.png")
    cutout("art/ink-united-737max9.jpg", "art/cut-ink.png", clear_boxes=[(1900, 220, 2400, 430), (240, 1170, 720, 1370)])


def cut_key(src, dst):
    """Library cut, a colour-difference key against the flat magenta backdrop.
    Magenta is the only colour where red and blue both sit far above green, so the share of
    backdrop mixed into a pixel is (min(R, B) - G) / (the same for the backdrop). That gives soft
    edges, see-through propeller discs and de-pinked windows in one step. Then only the aircraft
    island is kept: anything touching the border (runway or ground left over from the reference
    photo) is dropped, and other islands survive only within a few pixels of the aircraft."""
    im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    bg = np.median(im[:24].reshape(-1, 3), axis=0)
    span = max(min(bg[0], bg[2]) - bg[1], 1.0)
    mix = np.clip((np.minimum(im[..., 0], im[..., 2]) - im[..., 1]) / span, 0, 1)
    a = 1.0 - mix
    fg = a > 0.5
    lab, n = ndimage.label(fg)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    ids = [i + 1 for i, sz in enumerate(sizes) if (i + 1) not in border and sz >= 30]
    main = max(ids, key=lambda i: sizes[i - 1])
    near_main = ndimage.binary_dilation(lab == main, iterations=12)
    ids = [i for i in ids if i == main or (near_main & (lab == i)).any()]
    body = ndimage.binary_fill_holes(np.isin(lab, ids))
    a = np.where(ndimage.binary_dilation(body, iterations=3), a, 0.0)
    # Inside the body (windows, canopy glass) keep it opaque: tinted glass, not a hole.
    inner = ndimage.binary_erosion(body, iterations=4)
    unmix = np.maximum(a, 0.05)[..., None]
    rgb = (im - (1 - unmix) * bg) / unmix
    a = np.where(inner & (a > 0.3), 1.0, a)
    out = np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)
    ys, xs = np.where(a > 0.5)
    pad = 12
    box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad, im.shape[1]), min(ys.max() + pad, im.shape[0]))
    Image.fromarray(out, "RGBA").crop(box).save(dst)
    return bg, box
