# Full-screen poster takeover for the Show (1280x800): FlightPortrait-style print, sample data.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shoot import shoot

ART = "file:///" + os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/art"
CREAM = "#f3e6c8"
HTML = f"""<html><head><style>
* {{ box-sizing: border-box; margin: 0; }}
body {{ width: 1280px; height: 800px; overflow: hidden; background: #8d0e12; color: {CREAM}; font-family: Georgia, 'Times New Roman', serif; }}
.mark {{ position: absolute; left: 64px; top: 52px; font-size: 15px; letter-spacing: 5px; }}
.live {{ position: absolute; right: 64px; top: 52px; font-size: 13px; letter-spacing: 3px; opacity: .8; }}
.jet {{ position: absolute; left: 70px; top: 190px; width: 1140px; filter: drop-shadow(0 18px 18px rgba(0,0,0,.25)); }}
.cap {{ position: absolute; left: 120px; top: 590px; }}
.cap .a {{ font-size: 30px; }} .cap .b {{ font-size: 19px; margin-top: 8px; opacity: .85; }}
.foot {{ position: absolute; left: 64px; right: 64px; bottom: 44px; font-family: 'Segoe UI', sans-serif; font-size: 11px;
         letter-spacing: 2.4px; text-align: center; opacity: .7; }}
</style></head><body>
<div class="mark">OVERHEAD</div><div class="live">4.2 MI NE &middot; CLIMBING</div>
<img class="jet" src="{ART}/cut-poster.png">
<div class="cap"><div class="a">United Airlines &middot; Boeing 737 MAX 9</div>
  <div class="b">UA 1523 &middot; Denver &rarr; San Francisco &middot; N37440 &middot; 34,000 ft</div></div>
<div class="foot">No 37 TODAY &middot; THURSDAY 30 OCTOBER 2026 &middot; 39.77&deg; N 105.08&deg; W &middot; WHEAT RIDGE, COLORADO</div>
</body></html>"""
print(shoot("show-poster-takeover", HTML, 1280, 800))
