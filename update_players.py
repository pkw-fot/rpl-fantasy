import csv
import io
import json
import requests

PLAYERS_CSV_URL = "https://raw.githubusercontent.com/dcaribou/transfermarkt-datasets/master/data/default/players.csv"
CLUBS_CSV_URL = "https://raw.githubusercontent.com/dcaribou/transfermarkt-datasets/master/data/default/clubs.csv"

def update_rpl():
    print("⏳ Загрузка клубов и игроков РПЛ из открытой базы...")
    
    # 1. Получаем ID клубов РПЛ
    clubs_res = requests.get(CLUBS_CSV_URL)
    clubs_reader = csv.DictReader(io.StringIO(clubs_res.text))
    rpl_clubs = {}
    
    for row in clubs_reader:
        if row.get("domestic_competition_id") == "RU1":
            rpl_clubs[row["club_id"]] = row["name"]
            
    print(f"✅ Найдено клубов РПЛ: {len(rpl_clubs)}")

    db = {"GK": [], "LB": [], "CB": [], "RB": [], "MID": [], "FWD": []}

    # 2. Получаем игроков этих клубов
    players_res = requests.get(PLAYERS_CSV_URL)
    players_reader = csv.DictReader(io.StringIO(players_res.text))

    for p in players_reader:
        cid = p.get("current_club_id")
        if cid in rpl_clubs:
            name = p.get("name")
            club = rpl_clubs[cid]
            sub_pos = p.get("sub_position", "")
            pos = p.get("position", "")

            item = {"name": name, "club": club, "tier": "Основа"}

            if pos == "Goalkeeper":
                db["GK"].append(item)
            elif sub_pos == "Left-Back":
                db["LB"].append(item)
            elif sub_pos == "Right-Back":
                db["RB"].append(item)
            elif sub_pos == "Centre-Back" or pos == "Defender":
                db["CB"].append(item)
            elif pos == "Midfield" or "Winger" in sub_pos:
                db["MID"].append(item)
            elif pos == "Attack":
                db["FWD"].append(item)

    with open("players.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"🎉 players.json успешно сформирован! Игроков в базе: {sum(len(v) for v in db.values())}")

if __name__ == "__main__":
    update_rpl()
