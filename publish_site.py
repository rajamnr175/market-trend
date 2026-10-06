"""Copy the freshly rendered dashboard (out/scan_visual.html) into docs/index.html for GitHub Pages."""
import os
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
s = open("out/scan_visual.html").read()
if not s.lstrip().lower().startswith("<!doctype"):
    s = ('<!doctype html><html><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1"></head><body>\n' + s + "\n</body></html>")
os.makedirs("docs", exist_ok=True)
open("docs/index.html", "w").write(s)
open("docs/.nojekyll", "w").write("")
if os.path.exists("news.json"):
    import shutil; shutil.copy("news.json", "docs/news.json")
if os.path.exists("earnings.json"):
    import shutil; shutil.copy("earnings.json", "docs/earnings.json")
print("docs/index.html", len(s), "bytes")
