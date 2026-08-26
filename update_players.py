import requests
import json
import time

BASE_URL = "https://transfermarkt-api.fly.dev"

def fetch_and_save_all_rpl():
    print("⏳ Запрашиваем актуальный список клубов РПЛ...")
    try:
        comp_res = requests.get(f"{BASE_URL}/competitions/RU1/clubs", timeout=20)
        clubs = comp_res.json().get("clubs", [])
    except Exception as e:
        print(f"Ошибка получения лиги: {e}")
        return

    db = {"GK": [], "LB": [], "CB": [], "RB": [], "MID": [], "FWD": []}

    for club in clubs:
        cid = club.get("id")
        cname = club.get("name")
        print(f"Парсинг: {cname}...")
        
        try:
            p_res = requests.get(f"{BASE_URL}/clubs/{cid}/players", timeout=20)
            players = p_res.json().get("players", [])
            
            for p in players:
                name = p.get("name")
                pos = p.get("position", "")
                val = p.get("marketValue", "—")
                
                item = {
                    "name": name,
                    "club": cname,
                    "tier": "Основа" if val != "—" else "Ротация"
                }

                if "Goalkeeper" in pos:
                    db["GK"].append(item)
                elif "Left-Back" in pos:
                    db["LB"].append(item)
                elif "Right-Back" in pos:
                    db["RB"].append(item)
                elif "Centre-Back" in pos or "Defender" in pos:
                    db["CB"].append(item)
                elif "Midfield" in pos or "Winger" in pos or "Left Winger" in pos or "Right Winger" in pos:
                    db["MID"].append(item)
                elif "Attack" in pos or "Striker" in pos or "Centre-Forward" in pos:
                    db["FWD"].append(item)
                    
            time.sleep(0.5)
        except Exception as e:
            print(f"Ошибка в клубе {cname}: {e}")

    with open("players.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print("✅ players.json успешно обновлен!")

if __name__ == "__main__":
    fetch_and_save_all_rpl()
