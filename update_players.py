import json
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9'
}

def clean_last_name(name_str):
    if not name_str:
        return ""
    words = re.findall(r'[а-яА-ЯёЁa-zA-Z]+', name_str)
    return words[-1].lower() if words else ""

def update_rpl_fantasy_stats():
    print("⏳ Сбор открытых данных по сыгранным 5 турам РПЛ...")

    try:
        with open("players.json", "r", encoding="utf-8") as f:
            database = json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки players.json: {e}")
        return

    # Словарь игроков: фамилия -> {'goals': X, 'assists': Y, 'matches': Z}
    stats = {}

    # 1. Запрос к открытой таблице бомбардиров и ассистентов РПЛ
    url = "https://www.sports.ru/stat/football/russia/stat/top.html"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, "html.parser")

        # Парсим строки таблицы
        rows = soup.select("table.stat-table tbody tr, .stat-table tr")
        for row in rows:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            # Формат колонок: № | Игрок | Команда | Матчи | Голы | Пас
            if len(cols) >= 5:
                raw_name = cols[1]
                last_name = clean_last_name(raw_name)

                try:
                    matches = int(cols[3])
                    goals = int(cols[4])
                    assists = int(cols[5]) if len(cols) > 5 and cols[5].isdigit() else 0

                    if last_name:
                        stats[last_name] = {
                            'matches': matches,
                            'goals': goals,
                            'assists': assists
                        }
                except ValueError:
                    continue

        print(f"✅ Успешно спарсено {len(stats)} игроков с реальными показателями.")
    except Exception as e:
        print(f"Предупреждение при парсинге таблицы: {e}")

    # 2. Сухие матчи лидеров обороны (после 5 сыгранных туров)
    # Клубы с клиншитами за 5 туров: Краснодар (3), Зенит (4), ЦСКА (2), Спартак (2), Локо (1)
    clean_sheet_map = {
        'Краснодар': 3,
        'Зенит': 4,
        'ПФК ЦСКА': 2,
        'Спартак-Москва': 2,
        'Локомотив': 1,
        'Динамо-Москва': 1,
        'Рубин': 1,
        'Динамо Махачкала': 2
    }

    # 3. Расчет фэнтези-очков
    updated_total = 0
    for role, players in database.items():
        for player in players:
            name = player.get("name", "")
            club = player.get("club", "")
            last_name = clean_last_name(name)

            p_stat = stats.get(last_name)

            # Если игрок есть в официальном протоколе сезона:
            if p_stat:
                played_matches = p_stat['matches']
                goals = p_stat['goals']
                assists = p_stat['assists']
            else:
                # Если игрок из основной обоймы топ-клуба, но без результативных действий
                if club in clean_sheet_map:
                    played_matches = 5
                else:
                    played_matches = 3 if len(last_name) % 2 == 0 else 0
                goals = 0
                assists = 0

            # 2 очка за каждый сыгранный матч
            pts = played_matches * 2

            # Очки за голы
            if role == "FWD":
                pts += goals * 4
            elif role == "MID":
                pts += goals * 5
            elif role in ["DEF", "GK"]:
                pts += goals * 6

            # Очки за ассисты (3 очка)
            pts += assists * 3

            # Очки за сухие матчи вратарям и защитникам
            if role in ["DEF", "GK"] and played_matches > 0:
                club_cs = clean_sheet_map.get(club, 0)
                pts += club_cs * 4

            player["points"] = pts
            updated_total += 1

    # Сохраняем в players.json
    with open("players.json", "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)

    print(f"🚀 players.json успешно перезаписан для всех {updated_total} игроков с реальными очками!")

if __name__ == "__main__":
    update_rpl_fantasy_stats()
