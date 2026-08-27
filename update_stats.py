import json
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
}

# Словарь сопоставления: название на Soccer365 -> точное название в players.json
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
    'зенит спб': 'Зенит',
    
    'краснодар': 'Краснодар',
    'локомотив': 'Локомотив',
    'локомотив м': 'Локомотив',
    
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
    'динамо мх': 'Динамо Махачкала',
    'динамо (махачкала)': 'Динамо Махачкала'
}

def normalize_club(name_str):
    if not name_str:
        return ""
    clean = name_str.lower().replace("-", " ").strip()
    clean = re.sub(r'^(фк|пфк)\s+', '', clean)
    return CLUB_MAPPING.get(clean, clean.title())

def extract_last_name(full_name):
    """Извлекает нормализованную фамилию для надежного сопоставления."""
    parts = full_name.strip().split()
    if not parts:
        return ""
    # Для составных имен/фамилий берем последнее слово
    return parts[-1].lower()

def update_stats_from_soccer365():
    print("⏳ Подключение к soccer365.ru...")

    try:
        with open("players.json", "r", encoding="utf-8") as f:
            database = json.load(f)
    except Exception as e:
        print(f"Ошибка открытия players.json: {e}")
        return

    url = "https://soccer365.ru/competitions/13/results/"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Ошибка запроса к Soccer365: {e}")
        return

    # Структура: клуб -> { 'goals': {фамилия: кол-во}, 'clean_sheet': bool, 'played': True }
    match_data = {}

    # Находим матчи тура в блоках результатов
    games = soup.select(".game_block, .live_game")
    print(f"Найдено матчей для обработки: {len(games)}")

    for game in games:
        # Извлекаем названия команд
        home_el = game.select_one(".name_ht, .ht")
        away_el = game.select_one(".name_at, .at")
        score_el = game.select_one(".gls, .score")

        if not home_el or not away_el or not score_el:
            continue

        raw_home = home_el.get_text(strip=True)
        raw_away = away_el.get_text(strip=True)
        norm_home = normalize_club(raw_home)
        norm_away = normalize_club(raw_away)

        score_text = score_el.get_text(strip=True)
        score_match = re.search(r'(\d+)[\s:-]+(\d+)', score_text)

        if not score_match:
            continue

        home_goals = int(score_match.group(1))
        away_goals = int(score_match.group(2))

        # Инициализируем статистику команд
        if norm_home not in match_data:
            match_data[norm_home] = {"goals": {}, "clean_sheet": (away_goals == 0), "played": True}
        if norm_away not in match_data:
            match_data[norm_away] = {"goals": {}, "clean_sheet": (home_goals == 0), "played": True}

        # Извлекаем авторов голов
        events = game.select(".events_ht .event, .events_at .event, .game_events .event")
        for ev in events:
            ev_text = ev.get_text(strip=True)
            # Убираем минуты (например: "Глушенков 45'")
            clean_name = re.sub(r'[\d\'\+]+', '', ev_text).strip()
            last_n = extract_last_name(clean_name)
            if last_n:
                # Проверяем, к какой команде относится событие
                if ev.find_parent(class_=re.compile(r'ht|home')):
                    match_data[norm_home]["goals"][last_n] = match_data[norm_home]["goals"].get(last_n, 0) + 1
                else:
                    match_data[norm_away]["goals"][last_n] = match_data[norm_away]["goals"].get(last_n, 0) + 1

    # Начисляем очки игрокам в players.json
    updated_count = 0
    for role, players in database.items():
        for player in players:
            club = player.get("club", "")
            last_name = extract_last_name(player.get("name", ""))

            club_stats = match_data.get(club)
            pts = 0

            if club_stats and club_stats.get("played"):
                # 2 очка за появление в матче
                pts += 2
                
                # Очки за забитые голы
                player_goals = club_stats["goals"].get(last_name, 0)
                if role == "FWD":
                    pts += player_goals * 4
                elif role == "MID":
                    pts += player_goals * 5
                elif role in ["DEF", "GK"]:
                    pts += player_goals * 6

                # 4 очка за сухой матч вратарям и защитникам
                if role in ["DEF", "GK"] and club_stats.get("clean_sheet"):
                    pts += 4
            else:
                # Если клуб еще не играл или игрок не в заявке
                pts = 0

            player["points"] = pts
            updated_count += 1

    with open("players.json", "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)

    print(f"✅ Готово! Статистика Soccer365 сопоставлена и обновлена для {updated_count} игроков.")

if __name__ == "__main__":
    update_stats_from_soccer365()
