# Finds side-on reference photos on Wikimedia Commons for each library combo and lays the
# candidates out on contact sheets (one row per combo) so the best side view can be picked by eye.
import io, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from library import COMBOS, key

UA = {"User-Agent": "TyHomeDashboard/1.0 (personal project; planes overhead art)"}
REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "refs")
os.makedirs(REFS, exist_ok=True)


def get(url, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == tries - 1:
                raise
            time.sleep(15 * (i + 1))  # Commons rate-limits bursts


def search(q, n=24):
    params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": "6",
              "gsrsearch": q, "gsrlimit": str(n), "prop": "imageinfo", "iiprop": "url|size|mime",
              "iiurlwidth": "1920"}
    d = json.loads(get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)))
    pages = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    out = []
    for p in pages:
        ii = p["imageinfo"][0]
        if ii.get("mime") != "image/jpeg" or ii["width"] < 1400:
            continue
        ar = ii["width"] / ii["height"]
        if 1.3 <= ar <= 3.4:
            out.append({"title": p["title"], "thumb": ii["thumburl"], "ar": round(ar, 2)})
    return out


def main():
    cpath = os.path.join(REFS, "candidates.json")
    cands = json.load(open(cpath)) if os.path.exists(cpath) else {}
    for c in COMBOS:
        if key(c) in cands:
            continue
        airline, typ = c[2], c[3]
        q = f'"{airline}" "{typ}"' if airline else f'"{typ}"'
        res = search(q)
        if len(res) < 3 and airline:
            res += search(f"{airline} {typ}")
        cands[key(c)] = res[:4]
        time.sleep(1.5)
        json.dump(cands, open(cpath, "w"), indent=1)
    json.dump(cands, open(os.path.join(REFS, "candidates.json"), "w"), indent=1)

    font = ImageFont.truetype("arial.ttf", 22)
    ppath = os.path.join(REFS, "picks.json")
    picked = json.load(open(ppath)) if os.path.exists(ppath) else {}
    keys = [key(c) for c in COMBOS if key(c) not in picked]
    for s in range(0, len(keys), 8):
        if os.path.exists(os.path.join(REFS, f"sheetB{s // 8}.jpg")):
            continue
        sheet = Image.new("RGB", (4 * 420 + 220, 8 * 200), "white")
        d = ImageDraw.Draw(sheet)
        for r, k in enumerate(keys[s:s + 8]):
            d.text((8, r * 200 + 80), k, fill="black", font=font)
            for i, cand in enumerate(cands[k][:3]):
                # 330px is one of Wikimedia's standard thumbnail steps; other widths get throttled.
                im = Image.open(io.BytesIO(get(cand["thumb"].replace("/1920px-", "/250px-")))).convert("RGB")
                im.thumbnail((400, 180))
                x, y = 220 + i * 420, r * 200 + 8
                sheet.paste(im, (x, y))
                d.text((x + 4, y + 2), str(i), fill="yellow", font=font, stroke_width=2, stroke_fill="black")
                time.sleep(4)
        sheet.save(os.path.join(REFS, f"sheetB{s // 8}.jpg"), quality=80)
    print("sheets:", (len(keys) + 7) // 8, {k: len(v) for k, v in cands.items()})


if __name__ == "__main__":
    main()
