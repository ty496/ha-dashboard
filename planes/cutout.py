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
