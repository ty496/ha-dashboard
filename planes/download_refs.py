# Downloads the chosen reference photo (1920px Commons thumbnail) for each combo into refs/<key>.jpg.
# PICKS maps combo key -> candidate index on its contact sheet, or a path to a local photo.
import io, json, os, sys, time
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_refs import REFS, get

PICKS = json.load(open(os.path.join(REFS, "picks.json")))


def main():
    cands = json.load(open(os.path.join(REFS, "candidates.json")))
    for k, pick in PICKS.items():
        dst = os.path.join(REFS, k + ".jpg")
        if os.path.exists(dst):
            continue
        if isinstance(pick, str):
            Image.open(pick).convert("RGB").save(dst, quality=92)
        else:
            Image.open(io.BytesIO(get(cands[k][pick]["thumb"]))).convert("RGB").save(dst, quality=92)
            time.sleep(3)
        print("saved", k)


if __name__ == "__main__":
    main()
