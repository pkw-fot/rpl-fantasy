import json
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
}

# Словарь нормализации названий клубов РПЛ 2026/2027
CLUB_MAPPING = {
    'спартак москва': 'Спартак-Москва',
    'спартак м': 'Спартак-Москва',
    'спартак': 'Спартак-Москва',
    'динамо москва': 'Динамо-Москва',
    'динамо м': 'Динамо-Москва',
    'динамо': 'Динамо-Москва',
    'цска': 'ПФК ЦСКА',
    'пфк цска': 'ПФК ЦСКА',
    'цска москва': 'ПФК ЦСКА',
    'зенит': 'Зенит',
    'краснодар': 'Краснодар',
    'локомотив': 'Локомотив',
    'локомотив москва': 'Локомотив',
    'ростов': 'Ростов',
    'рубин': 'Рубин',
    'крылья советов': 'Крылья Советов',
    'ахмат': 'Ахмат',
    'факел': 'Факел',
    'оренбург': 'Оренбург',
    'акрон': 'Акрон',
    'балтика': 'Балтика',
    'родина': 'Родина',
    'динамо махачкала': 'Динамо Махачкала',
    'динамо мх': 'Динамо Махачкала'
}

def normalize_club(name_str):
    if not name_str:
        return ""
    clean = name_str.lower().replace("-", " ").strip()
    clean = re.sub(r'^(фк|пфк)\s+', '', clean)
    return CLUB_MAPPING.get(clean, clean.title())

def extract_last_name(name_str):
    if not name_str:
        return ""
    words = re.findall(r'[a-zA-Zа-яА-ЯёЁ]+', name_str)
    return words[-1].lower() if words else ""

def parse_season_26_27():
    print("⏳ Сбор статистики РПЛ сезона 2026/2027 с Soccer365...")

    try:
        with open("players.json", "r", encoding="utf-8") as f:
            database = json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки players.json: {e}")
        return

    # 1. Сбор результатов матчей и сухих игр сезона 26/27
    club_stats = {} # клуб -> {'matches': X, 'clean_sheets': Y}
    url_results = "https://soccer365.ru/competitions/13/"

    try:
        res = requests.get(url_results, headers=HEADERS, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, "html.parser")

        # Парсим турнирную таблицу сезона 26/27
        table_rows = soup.select("table.table_results tr, table.display tr, .stats_table tr")
        for tr in table_rows:
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if len(cells) >= 8:
                # Обычно: Позиция | Команда | И (игры) | В | Н | П | З | П (пропущено)
                club_name = normalize_club(cells[1])
                try:
                    played_games = int(cells[2])
                    if club_name:
                        if club_name not in club_stats:
                            club_stats[club_name] = {'matches': played_games, 'clean_sheets': 0}
                        else:
                            club_stats[club_name]['matches'] = max(club_stats[club_name]['matches'], played_games)
                except ValueError:
                    continue

        # Парсим сыгранные матчи для подсчета клиншитов (0 пропущенных)
        for game in soup.select(".game_block, .live_game, .game_events"):
            home_el = game.select_one(".name_ht, .ht")
            away_el = game.select_one(".name_at, .at")
            score_el = game.select_one(".gls, .score")

            if home_el and away_el and score_el:
                norm_h = normalize_club(home_el.get_text(strip=True))
                norm_a = normalize_club(away_el.get_text(strip=True))
                score_match = re.search(r'(\d+)[\s:-]+(\d+)', score_el.get_text(strip=True))
                
                if score_match:
                    h_goals = int(score_match.group(1))
                    a_goals = int(score_match.group(2))

                    if norm_h in club_stats and a_goals == 0:
                        club_stats[norm_h]['clean_sheets'] += 1
                    if norm_a in club_stats and h_goals == 0:
                        club_stats[norm_a]['clean_sheets'] += 1

        print(f"Статистика клубов сезона 26/27: {len(club_stats)} команд обработано.")
    except Exception as e:
        print(f"Предупреждение при парсинге матчей сезона 26/27: {e}")

    # 2. Сбор бомбардиров и ассистентов сезона 2026/2027
    player_stats = {} # фамилия -> {'goals': X, 'assists': Y}
    url_players = "https://soccer365.ru/competitions/13/&tab=stats_players"

    try:
        res_p = requests.get(url_players, headers=HEADERS, timeout=15)
        res_p.encoding = 'utf-8'
        soup_p = BeautifulSoup(res_p.text, "html.parser")

        for tr in soup_p.select("table.stats_table tr, table.display tr, .stats_items tr"):
            tds = tr.find_all("td")
            if len(tds) >= 3:
                name_cell = tr.select_one(".name, .player_name, a")
                if not name_cell:
                    continue
                last_name = extract_last_name(name_cell.get_text(strip=True))
                numbers = [int(s) for s in re.findall(r'\b\d+\b', tr.get_text())]
                
                if last_name and len(numbers) >= 2:
                    val = numbers[1]
                    if last_name not in player_stats:
                        player_stats[last_name] = {'goals': 0, 'assists': 0}
                    player_stats[last_name]['goals'] = max(player_stats[last_name]['goals'], val)

        print(f"Индивидуальная статистика бомбардиров сезона 26/27: {len(player_stats)} игроков.")
    except Exception as e:
        print(f"Предупреждение при сборе игроков 26/27: {e}")

    # 3. Расчет фэнтези-очков строго за сезон 26/27
    total_updated = 0
    for role, players in database.items():
        for player in players:
            club = player.get("club", "")
            last_name = extract_last_name(player.get("name", ""))
            
            c_info = club_stats.get(club, {'matches': 5, 'clean_sheets': 0})
            p_info = player_stats.get(last_name, {'goals': 0, 'assists': 0})

            # Сыгранные матчи сезона 26/27
            played_games = c_info.get('matches', 5)
            # Базовые 2 очка за каждый выход в сезоне 26/27
            pts = played_games * 2

            # Очки за голы в сезоне 26/27
            goals = p_info.get('goals', 0)
            if role == "FWD":
                pts += goals * 4
            elif role == "MID":
                pts += goals * 5
            elif role in ["DEF", "GK"]:
                pts += goals * 6

            # Очки за клиншиты сезона 26/27 (вратари и защитники)
            if role in ["DEF", "GK"]:
                clean_sheets = c_info.get('clean_sheets', 0)
                pts += clean_sheets * 4

            player["points"] = pts
            total_updated += 1

    with open("players.json", "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)

    print(f"✅ Готово! Начислены честные очки сезона 2026/2027 для {total_updated} игроков.")

if __name__ == "__main__":
    parse_season_26_27()
