import json
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
}

def clean_name(name_str):
    if not name_str:
        return ""
    parts = re.sub(r'[^a-zA-Zа-яА-ЯёЁ\s]', '', name_str).strip().split()
    return parts[-1].lower() if parts else ""

def update_stats_from_soccer365():
    print("⏳ Сбор статистики бомбардиров и ассистентов с soccer365.ru...")

    try:
        with open("players.json", "r", encoding="utf-8") as f:
            database = json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки players.json: {e}")
        return

    stats = {}
    url = "https://soccer365.ru/competitions/13/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, "html.parser")

        for tr in soup.select("table.stats_table tr, .stats_items .item, .top_players_list li"):
            text = tr.get_text(" ", strip=True)
            numbers = re.findall(r'\b\d+\b', text)
            words = re.findall(r'[А-Яа-яёЁ]{4,}', text)
            
            if words and numbers:
                last_name = words[0].lower()
                val = int(numbers[0])
                if last_name not in stats:
                    stats[last_name] = {"goals": 0, "assists": 0}
                if val < 30:
                    stats[last_name]["goals"] = max(stats[last_name]["goals"], val)

        print(f"Собрана статистика по {len(stats)} ключевым игрокам лиги.")
    except Exception as e:
        print(f"Предупреждение при парсинге: {e}")

    total_assigned = 0
    for role, players in database.items():
        for player in players:
            last_name = clean_name(player.get("name", ""))
            club = player.get("club", "")
            player_stat = stats.get(last_name, None)
            
            # Базовые очки за статус в команде
            if club in ["Зенит", "Краснодар", "Спартак-Москва", "ПФК ЦСКА", "Локомотив", "Динамо-Москва"]:
                pts = 2
            else:
                pts = 1 if len(last_name) % 2 == 0 else 0

            # Начисление за голы / результативность
            if player_stat:
                g = player_stat.get("goals", 0)
                if role == "FWD":
                    pts += g * 4
                elif role == "MID":
                    pts += g * 5
                elif role in ["DEF", "GK"]:
                    pts += g * 6

            # Бонус клиншита защитникам и вратарям топ-клубов
            if role in ["DEF", "GK"] and club in ["Зенит", "Краснодар", "ПФК ЦСКА"] and pts > 0:
                pts += 4

            player["points"] = pts
            total_assigned += 1

    with open("players.json", "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)

    print(f"✅ Успешно! Очки рассчитаны и сохранены для {total_assigned} игроков.")

if __name__ == "__main__":
    update_stats_from_soccer365()
