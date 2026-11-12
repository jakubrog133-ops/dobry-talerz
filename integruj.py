import os
import re
import json
import shutil

CACHE_PATH = os.path.expanduser("~/Desktop/respo_przepisy/respo_cache.json")
INDEX_PATH = "index.html"
SW_PATH = "sw.js"

if not os.path.exists(CACHE_PATH):
    raise FileNotFoundError(f"Nie znaleziono pliku: {CACHE_PATH}")
if not os.path.exists(INDEX_PATH):
    raise FileNotFoundError(f"Nie znaleziono pliku: {INDEX_PATH}")

# Kopia zapasowa
shutil.copy2(INDEX_PATH, "index.html.bak")
print("1/4: Utworzono kopię zapasową index.html.bak")

with open(CACHE_PATH, "r", encoding="utf-8") as f:
    cache = json.load(f)

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    html_txt = f.read()

m = re.search(r"const ORIGINAL_RECIPES_BATCH\s*=\s*(\[.*?\]);", html_txt, re.S)
if not m:
    raise RuntimeError("Nie znaleziono tablicy ORIGINAL_RECIPES_BATCH w index.html")

existing_batch = json.loads(m.group(1))
existing_titles = {r.get("title", "").strip().lower() for r in existing_batch}

# Zbierz też tytuły z RECIPES i EXTRA_RECIPES, by uniknąć duplikatów
for var_name in ("RECIPES", "EXTRA_RECIPES"):
    mv = re.search(rf"const {var_name}\s*=\s*(\[.*?\]);", html_txt, re.S)
    if mv:
        for r in json.loads(mv.group(1)):
            existing_titles.add(r.get("title", "").strip().lower())

# Mapowanie kategorii Respo -> UNIFIED_CATEGORIES w Dobrym Talerzu
CAT_MAP = {
    "Śniadania i kolacje": "Śniadania i kolacje",
    "Słone": "Śniadania i kolacje",
    "Jajka": "Śniadania i kolacje",
    "Kanapki": "Śniadania i kolacje",
    "Muffiny": "Śniadania i kolacje",
    "Naleśniki": "Śniadania i kolacje",
    "Owsianki": "Śniadania i kolacje",
    "Placki": "Śniadania i kolacje",
    "Słodkie": "Śniadania i kolacje",
    "Dania główne": "Dania główne",
    "Wegetariańskie": "Dania główne",
    "Kasza": "Dania główne",
    "Makaron": "Dania główne",
    "Mięso": "Dania główne",
    "Pizza": "Zdrowy Fast Food",
    "Ryby": "Dania główne",
    "Ryż": "Dania główne",
    "Wegańskie": "Dania główne",
    "Dania obiadowe": "Dania główne",
    "Zupy": "Zupy",
    "Klasyczne": "Zupy",
    "Krem": "Zupy",
    "Desery": "Desery",
    "Ciasta": "Desery",
    "Ciastka": "Desery",
    "Inne słodkości": "Desery",
    "Sałatki": "Sałatki",
    "Zdrowy Fast Food": "Zdrowy Fast Food",
    "Napoje / koktajle": "Napoje / koktajle",
    "Lunchbox": "Lunchbox",
    "Śniadaniówka": "Lunchbox",
    "Dla dzieci": "Dla dzieci",
    "Przekąski imprezowe": "Przekąski imprezowe",
    "Przekąski": "Przekąski imprezowe",
    "Sezonowe": "Sezonowe",
    "Wiosna": "Sezonowe",
    "Lato": "Sezonowe",
    "Jesień": "Sezonowe",
    "Zima": "Sezonowe",
    "Święta/Okazje": "Święta / Okazje",
    "Święta Bożego Narodzenia": "Święta / Okazje",
    "Wielkanoc": "Święta / Okazje",
    "Majówka": "Święta / Okazje",
    "Dzień Dziecka": "Święta / Okazje",
    "Sylwester": "Święta / Okazje",
    "Tłusty Czwartek": "Święta / Okazje",
    "Walentynki": "Święta / Okazje",
    "Kat. dodatkowe": "Kat. dodatkowe",
    "Lekkostrawne": "Kat. dodatkowe",
    "Szybkie i łatwe": "Kat. dodatkowe",
    "Przepisy IBS": "Kat. dodatkowe",
    "Do 5 składników": "Kat. dodatkowe",
    "Respo Sport": "Kat. dodatkowe",
    "Inne": "Inne",
}

def map_slot_and_type(cats, title_low):
    if "Zupy" in cats or "Dania główne" in cats:
        return 2, "Obiad"
    if "Napoje / koktajle" in cats or "Desery" in cats:
        return 1, "II śniadanie"
    if "Przekąski imprezowe" in cats:
        return 4, "Przekąska"
    if "Sałatki" in cats or "Zdrowy Fast Food" in cats:
        return 3, "Kolacja"
    return 0, "Śniadanie"

new_recipes = []
skipped = 0

for idx, (url, item) in enumerate(sorted(cache.items(), key=lambda x: x[1].get("title", ""))):
    title = (item.get("title") or "").strip()
    if not title or "/kategoria/" in url or title.lower() in existing_titles:
        skipped += 1
        continue

    raw_ings = item.get("ingredients") or []
    clean_ings = [ing[4:].strip() if ing.startswith("0 g ") else ing.strip() for ing in raw_ings if ing.strip()]
    steps = [s.strip() for s in (item.get("steps") or []) if s.strip()]

    if not clean_ings or not steps:
        skipped += 1
        continue

    # Kategorie
    raw_cats = [item.get("category", "")] + (item.get("tags") or [])
    mapped_cats = []
    for rc in raw_cats:
        mc = CAT_MAP.get(rc.strip())
        if mc and mc not in mapped_cats:
            mapped_cats.append(mc)
    if not mapped_cats:
        mapped_cats = ["Inne"]

    slot, meal_type = map_slot_and_type(mapped_cats, title.lower())

    # Czas przygotowania
    time_str = item.get("time") or ""
    nums = [int(x) for x in re.findall(r"(\d+)\s*min", time_str)]
    if len(nums) >= 2:
        t_min, t_max = min(nums), max(nums)
    elif len(nums) == 1:
        t_min = t_max = nums[0]
    else:
        t_min, t_max = 15, 30

    # Opis z kaloriami i makro
    macros = (item.get("macros") or "").strip()
    tags_clean = [t for t in (item.get("tags") or []) if not t.isdigit() and len(t) < 40]
    desc_parts = []
    if macros:
        desc_parts.append(macros)
    if time_str:
        desc_parts.append(f"Czas: {time_str}")
    if tags_clean:
        desc_parts.append(f"Kategorie: {', '.join(dict.fromkeys(tags_clean))}")
    description = " · ".join(desc_parts) if desc_parts else f"Przepis z kategorii: {', '.join(mapped_cats)}."

    rec_obj = {
        "id": f"respo-{idx+1}",
        "title": title,
        "day": 0,
        "slot": slot,
        "type": meal_type,
        "catalogCategories": mapped_cats,
        "description": description,
        "ingredients": clean_ings,
        "sourceUrl": url,
        "prepTime": {"min": t_min, "max": t_max},
        "preparation": {
            "steps": steps,
            "origin": "Przepis zaimportowany z bazy Centrum Respo.",
            "kind": "respo",
            "reference": {
                "label": "Źródło przepisu — Centrum Respo",
                "url": url,
            },
        },
    }
    if item.get("image"):
        rec_obj["image"] = item["image"]

    new_recipes.append(rec_obj)
    existing_titles.add(title.lower())

print(f"2/4: Przygotowano {len(new_recipes)} nowych przepisów (pominięto {skipped} duplikatów/pustych).")

combined_batch = existing_batch + new_recipes
batch_json = json.dumps(combined_batch, ensure_ascii=False, separators=(",", ":"))

# Podmiana ORIGINAL_RECIPES_BATCH w index.html
new_html = html_txt[:m.start()] + f"const ORIGINAL_RECIPES_BATCH = {batch_json};" + html_txt[m.end():]

# Aktualizacja liczników i numeru wersji na 2.9 w index.html
total_count = 28 + 37 + len(combined_batch)
new_html = new_html.replace('content="2.7"', 'content="2.9"')
new_html = new_html.replace("Wersja 2.8", "Wersja 2.9")
new_html = new_html.replace("const DT_APP_VERSION='2.7'", "const DT_APP_VERSION='2.9'")
new_html = new_html.replace(">165<", f">{total_count}<")
new_html = new_html.replace("165 wyników", f"{total_count} wyników")
new_html = new_html.replace("165 przepisów", f"{total_count} przepisów")

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(new_html)
print(f"3/4: Zapisano nowy index.html (łącznie ok. {total_count} przepisów w aplikacji).")

# Aktualizacja wersji cache w sw.js
if os.path.exists(SW_PATH):
    with open(SW_PATH, "r", encoding="utf-8") as f:
        sw_txt = f.read()
    sw_txt = sw_txt.replace("v2.8", "v2.9").replace("v2-8", "v2-9")
    with open(SW_PATH, "w", encoding="utf-8") as f:
        f.write(sw_txt)
    print("4/4: Zaktualizowano wersję offline w sw.js na v2.9.")

print("\nGOTOWE! Otwórz index.html w przeglądarce, aby przetestować przed wysłaniem na GitHub.")
