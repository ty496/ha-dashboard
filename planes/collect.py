# Files Nano Banana outputs under art/gen/<key>.jpg, cuts each to art/cut/<key>.png and builds a QA
# contact sheet (cutouts on the poster red, labelled) so a batch can be checked in one look.
# Usage: python collect.py KEY=path [KEY=path ...]   (no args: just rebuild the sheet of everything)
import os, shutil, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cutout import cut_key

HERE = os.path.dirname(os.path.abspath(__file__))
GEN, CUT = os.path.join(HERE, "art", "gen"), os.path.join(HERE, "art", "cut")
os.makedirs(GEN, exist_ok=True)
os.makedirs(CUT, exist_ok=True)


def sheet(keys, name):
    font = ImageFont.truetype("arial.ttf", 26)
    cw, ch = 900, 300
    cols = 2
    rows = (len(keys) + cols - 1) // cols
    img = Image.new("RGB", (cols * cw, rows * ch), (141, 14, 18))
    d = ImageDraw.Draw(img)
    for i, k in enumerate(keys):
        cut = Image.open(os.path.join(CUT, k + ".png"))
        cut.thumbnail((cw - 40, ch - 60))
        x, y = (i % cols) * cw, (i // cols) * ch
        img.paste(cut, (x + 20, y + 44), cut)
        d.text((x + 20, y + 10), k, fill=(243, 230, 200), font=font)
    out = os.path.join(HERE, "out", name)
    img.save(out, quality=85)
    return out


if __name__ == "__main__":
    done = []
    for arg in sys.argv[1:]:
        if "=" not in arg:
            continue
        k, src = arg.split("=", 1)
        if os.path.abspath(src) != os.path.abspath(os.path.join(GEN, k + ".jpg")):
            shutil.copy(src, os.path.join(GEN, k + ".jpg"))
        try:
            cut_key(os.path.join(GEN, k + ".jpg"), os.path.join(CUT, k + ".png"))
            done.append(k)
        except Exception as e:  # usually photo leftovers touching the plane; fix the image and rerun
            print(k, "CUT FAILED:", e)
    keys = done or sorted(f[:-4] for f in os.listdir(CUT) if f.endswith(".png"))
    print(sheet(keys, "qa-batch.jpg" if done else "qa-all.jpg"))
