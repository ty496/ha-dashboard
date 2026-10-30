# Echo Show (1280x800) mockups for the planes-overhead idea, 2026-10-30. Sample flight data.
# show-card: the home view with an "Overhead now" glass card on top of the right column.
# show-takeover: the full screen while a plane passes, the comic plane over the strip-day scene.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shoot import shoot

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
BG = "file:///" + os.path.abspath(os.path.join(HERE, "..", "www", "bg", "strip-day.jpg")).replace("\\", "/")
ART = "file:///" + HERE + "/art"

BASE_CSS = f"""
* {{ box-sizing: border-box; margin: 0; }}
body {{ width: 1280px; height: 800px; overflow: hidden; font-family: 'Segoe UI', Roboto, sans-serif; color: #1b2230;
        background: #96d3f0 url('{BG}') center bottom / 100% auto no-repeat; }}
.glass {{ background: rgba(255,255,255,.34); backdrop-filter: blur(5px) saturate(140%); border: 1px solid rgba(255,255,255,.65);
          border-radius: 24px; box-shadow: inset 0 1px 0 rgba(255,255,255,.75), inset 0 -1px 0 rgba(255,255,255,.6),
          inset 0 -10px 18px -14px rgba(255,255,255,.9), 0 10px 30px rgba(31,38,135,.14); }}
.muted {{ color: #4a5568; }}
"""

CARD_HTML = f"""<html><head><style>{BASE_CSS}
.col {{ position: absolute; top: 20px; width: 604px; display: flex; flex-direction: column; gap: 14px; }}
.left {{ left: 24px; }} .right {{ left: 652px; }}
.clock {{ padding: 18px 26px; }} .clock .t {{ font-size: 92px; font-weight: 300; letter-spacing: -2px; line-height: 1; }}
.clock .d {{ font-size: 22px; margin-top: 6px; }}
.wx {{ padding: 18px 26px; display: flex; justify-content: space-between; align-items: center; }}
.wx .temp {{ font-size: 64px; font-weight: 300; }} .wx .name {{ font-size: 22px; font-weight: 600; }}
.chips {{ display: flex; gap: 14px; }} .chip {{ flex: 1; padding: 14px 18px; font-size: 15px; }} .chip b {{ display: block; font-size: 22px; font-weight: 600; }}
.plane {{ padding: 16px 22px 18px; }}
.plane .hdr {{ display: flex; justify-content: space-between; font-size: 15px; font-weight: 600; letter-spacing: .3px; }}
.plane .hdr .live {{ color: #0a6fd6; }}
.plane img {{ display: block; width: 100%; margin: 10px 0 6px; filter: drop-shadow(0 10px 12px rgba(20,30,60,.22)); }}
.plane .row {{ display: flex; justify-content: space-between; align-items: flex-end; }}
.plane .flt {{ font-size: 30px; font-weight: 700; line-height: 1.1; }} .plane .route {{ font-size: 18px; margin-top: 2px; }}
.stats {{ display: flex; gap: 8px; }} .stat {{ background: rgba(255,255,255,.55); border-radius: 12px; padding: 6px 10px; font-size: 13px; text-align: center; }}
.stat b {{ display: block; font-size: 17px; }}
.cal {{ padding: 16px 22px; height: 300px; }} .cal h3 {{ font-size: 18px; margin-bottom: 10px; }}
.ev {{ display: flex; gap: 14px; padding: 8px 0; border-top: 1px solid rgba(0,0,0,.06); font-size: 16px; }}
.ev .day {{ width: 64px; font-weight: 600; }} .dot {{ width: 9px; height: 9px; border-radius: 50%; margin-top: 7px; }}
.bar {{ position: absolute; bottom: 18px; left: 370px; width: 540px; height: 58px; border-radius: 29px; display: flex;
        justify-content: space-around; align-items: center; background: rgba(255,255,255,.70); font-size: 16px; font-weight: 600; }}
</style></head><body>
<div class="col left">
  <div class="glass clock"><div class="t">4:02</div><div class="d muted">Thursday, October 30</div></div>
  <div class="glass wx"><div><div class="name">Wheat Ridge</div><div class="muted">Sunny · H 61° L 35°</div></div><div class="temp">54°</div></div>
  <div class="chips"><div class="glass chip muted"><b style="color:#1b2230">7:22</b>Sunrise</div>
    <div class="glass chip muted"><b style="color:#1b2230">5:52</b>Sunset</div>
    <div class="glass chip muted"><b style="color:#1b2230">Crescent</b>Moon</div></div>
</div>
<div class="col right">
  <div class="glass plane">
    <div class="hdr"><span class="live">&#9992;&#xFE0E; OVERHEAD NOW</span><span class="muted">4.2 mi NE · climbing</span></div>
    <img src="{ART}/cut-poster.png">
    <div class="row">
      <div><div class="flt">United 1523</div><div class="route muted">Denver &rarr; San Francisco</div></div>
      <div class="stats"><div class="stat"><b>34,000</b>ft</div><div class="stat"><b>512</b>mph</div><div class="stat"><b>737 MAX 9</b>N37440</div></div>
    </div>
  </div>
  <div class="glass cal"><h3>This week</h3>
    <div class="ev"><span class="day">Today</span><span class="dot" style="background:#d84315"></span>Flight home</div>
    <div class="ev"><span class="day">Sat</span><span class="dot" style="background:#2e7d32"></span>Trash &amp; recycling out</div>
    <div class="ev"><span class="day">Sun</span><span class="dot" style="background:#b26a00"></span>Broncos at 2:05</div>
  </div>
</div>
<div class="bar"><span>&#9889;&#xFE0E; Quick actions</span><span>Rooms</span><span>Scores</span></div>
</body></html>"""

TAKEOVER_HTML = f"""<html><head><style>{BASE_CSS}
.jet {{ position: absolute; left: 250px; top: 40px; width: 740px; transform: rotate(-4deg); }}
.cap {{ position: absolute; left: 32px; bottom: 30px; padding: 16px 24px; background: rgba(255,255,255,.72); }}
.cap .k {{ font-size: 13px; font-weight: 700; letter-spacing: 1.2px; color: #0a6fd6; }}
.cap .f {{ font-size: 30px; font-weight: 700; margin-top: 2px; }} .cap .s {{ font-size: 17px; margin-top: 2px; }}
</style></head><body>
<img class="jet" src="{ART}/cut-ink.png">
<div class="glass cap"><div class="k">&#9992;&#xFE0E; OVERHEAD NOW · 4.2 MI NE</div>
  <div class="f">United 1523 &nbsp;<span style="font-weight:400">Denver &rarr; San Francisco</span></div>
  <div class="s muted">Boeing 737 MAX 9 · N37440 · 34,000 ft · 512 mph</div></div>
</body></html>"""

if __name__ == "__main__":
    print(shoot("show-card", CARD_HTML, 1280, 800))
    print(shoot("show-takeover", TAKEOVER_HTML, 1280, 800))
