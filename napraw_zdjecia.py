import re

with open("index.html", "r", encoding="utf-8") as f:
    txt = f.read()

# 1. Dodaj meta no-referrer w <head>, aby serwer centrumrespo.pl nie blokował obrazków
if 'name="referrer"' not in txt:
    txt = txt.replace(
        '<meta charset="utf-8" />',
        '<meta charset="utf-8" />\n  <meta name="referrer" content="no-referrer" />'
    )
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(txt)
    print("Dodano <meta name=\"referrer\" content=\"no-referrer\" /> do index.html.")

# 2. Pokaż jak index.html obsługuje obrazki (meal-thumb / imageKey / image)
for kw in ("meal-thumb", "modal-image"):
    idx = txt.find(kw, txt.find("<script>"))
    if idx != -1:
        print(f"=== Kod JS wokół {kw} ===")
        print(txt[max(0, idx-250):idx+450])
