import json, re

with open("index.html", "r", encoding="utf-8") as f:
    txt = f.read()

# Pokażmy definicję mealThumb(r)
idx = txt.find("function mealThumb")
if idx != -1:
    print("=== mealThumb ===")
    print(txt[idx:idx+600])

# 1. Dodaj "source": "respo" do wszystkich zaimportowanych przepisów w ORIGINAL_RECIPES_BATCH
m = re.search(r"const ORIGINAL_RECIPES_BATCH\s*=\s*(\[.*?\]);", txt, re.S)
arr = json.loads(m.group(1))
updated = 0
for r in arr:
    if r.get("id", "").startswith("respo-"):
        r["source"] = "respo"
        updated += 1

batch_json = json.dumps(arr, ensure_ascii=False, separators=(",", ":"))
txt = txt[:m.start()] + f"const ORIGINAL_RECIPES_BATCH = {batch_json};" + txt[m.end():]

# 2. Upewnij się, że mealThumb(r) zwraca r.image, jeśli zaczyna się od http
if idx != -1:
    old_fn = txt[idx:idx+400]
    if "r.image" not in old_fn[:180]:
        txt = txt.replace(
            "function mealThumb(r){",
            "function mealThumb(r){if(r&&r.image&&/^https?:\\/\\//i.test(r.image))return r.image;",
            1
        )
        print("Zaktualizowano funkcję mealThumb(r) o obsługę linków https://")

with open("index.html", "w", encoding="utf-8") as f:
    f.write(txt)

print(f"Zaktualizowano {updated} przepisów Respo w index.html!")
