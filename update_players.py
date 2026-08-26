import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

def fetch_official_rpl():
    print("⏳ Подключение к базе РПЛ (4 категории: ВРТ, ЗАЩ, ПЗ, НАП)...")
    url = "https://premierliga.ru/players/"
    
    db = {
        "GK": [],
        "DEF": [],
        "MID": [],
        "FWD": []
    }

    try:
        res = requests.get(url, headers=HEADERS, timeout=25)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        rows = soup.select('table tbody tr') or soup.select('tr')
        print(f"Всего строк для обработки: {len(rows)}")

        for r in rows:
            cols = [c.get_text(strip=True) for c in r.find_all(['td', 'div', 'span']) if c.get_text(strip=True)]
            
            if len(cols) >= 3:
                name = cols[0]
                club = cols[1]
                pos = cols[2].lower()

                if "игрок" in name.lower() or "клуб" in club.lower():
                    continue

                item = {"name": name, "club": club, "tier": "РПЛ"}

                if "вратарь" in pos:
                    db["GK"].append(item)
                elif "защитник" in pos:
                    db["DEF"].append(item)
                elif "полузащитник" in pos:
                    db["MID"].append(item)
                elif "нападающий" in pos:
                    db["FWD"].append(item)

    except Exception as e:
        print(f"Ошибка запроса: {e}")

    with open("players.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in db.values())
    print(f"✅ players.json сформирован! Вратарей: {len(db['GK'])}, Защитников: {len(db['DEF'])}, Полузащитников: {len(db['MID'])}, Нападающих: {len(db['FWD'])}")

if __name__ == "__main__":
    fetch_official_rpl()
