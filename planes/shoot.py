# Renders an HTML string to PNG with headless Chrome (throwaway profile, never Ty's).
import os, subprocess, sys, tempfile

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)


def shoot(name, html, w, h):
    page = os.path.join(OUT, name + ".html")
    with open(page, "w", encoding="utf-8") as f:
        f.write(html)
    png = os.path.join(OUT, name + ".png")
    prof = tempfile.mkdtemp(prefix="planeshot-")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={prof}",
                    f"--window-size={w},{h}", "--force-device-scale-factor=1", "--allow-file-access-from-files",
                    "--virtual-time-budget=1500", f"--screenshot={png}", "file:///" + page.replace("\\", "/")],
                   check=True, capture_output=True, timeout=60)
    return png


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from draw_plane import plane_svg
    html = ('<html><body style="margin:0;background:#cfd8e3">'
            + "".join(f'<div style="padding:10px 30px">{plane_svg(s)}</div>' for s in ("poster", "lit", "ink"))
            + "</body></html>")
    print(shoot("test", html, 1400, 1250))
