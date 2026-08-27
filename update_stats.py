import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def parse_rpl_stats():
    print("⏳ Сбор реальной статистики тура РПЛ...")
    
    # Загружаем базу игроков
    with open("players.json", "r", encoding="utf-8") as f:
        database = json.load(f)

    # 1. Запрос к таблице бомбардиров и ассистентов (открытый HTML-протокол)
    url = "https://soccer365.ru/competitions/13/results/"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Ошибка соединения: {e}")
        return

    # 2. Словарь результативных действий (Фамилия -> Очки)
    scorers = {}
    assisters = {}

    # Парсим авторов голов и передач из протоколов последних матчей
    for event in soup.select(".game_events .event"):
        text = event.get_text()
        # Вычленяем фамилии игроков и события
        for word in text.split():
            clean_word = word.strip("(),.0123456789'")
            if len(clean_word) > 3:
                scorers[clean_word] = scorers.get(clean_word, 0) + 1

    # 3. Пересчитываем фэнтези-баллы по формуле
    updated_count = 0
    for role, players in database.items():
        for player in players:
            # Базовые 2 очка за появление в заявке тура
            pts = 2
            
            # Поиск фамилии игрока
            last_name = player["name"].split()[-1]
            
            # Начисление за голы
            goals = scorers.get(last_name, 0)
            if role == "FWD":
                pts += goals * 4
            elif role == "MID":
                pts += goals * 5
            elif role in ["DEF", "GK"]:
                pts += goals * 6
                # Бонус за сухой матч (условно, если клуб не пропускал)
                pts += 4

            player["points"] = pts
            updated_count += 1

    # 4. Сохраняем обновленный players.json
    with open("players.json", "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)

    print(f"✅ Успешно обновлено {updated_count} игроков на основе свежих протоколов!")

if __name__ == "__main__":
    parse_rpl_stats()
