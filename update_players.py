import csv
import io
import json
import re
import requests

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSgejP1x9nvmxaSb8WNsa5G_CJX2Ep1VU855nrE61pfE6swdP5sR0FQE2THmmZTRevBmU5k8BfVhYXG/pub?output=csv"

ROLE_MAP = {
    'ВРТ': 'GK',
    'ЗАЩ': 'DEF',
    'ПЗ': 'MID',
    'НАП': 'FWD'
}

# 1. Словарь точных русских имен и стран
EXACT_PLAYERS = {
    'maksim glushenkov': ('Максим Глушенков', 'Россия'),
    'aleksandr sobolev': ('Александр Соболев', 'Россия'),
    'artem maksimenko': ('Артём Максименко', 'Россия'),
    'gustavo mantuan': ('Густаво Мантуан', 'Бразилия'),
    'jubal': ('Жубал', 'Бразилия'),
    'lucas olaza': ('Лукас Оласа', 'Уругвай'),
    'nikita glushkov': ('Никита Глушков', 'Россия'),
    'andrey langovich': ('Андрей Лангович', 'Россия'),
    'nikita krivtsov': ('Никита Кривцов', 'Россия'),
    'roman zobnin': ('Роман Зобнин', 'Россия'),
    'sergei varatynov': ('Сергей Варатынов', 'Россия'),
    'marquinhos': ('Маркиньос', 'Бразилия'),
    'aleksandr silyanov': ('Александр Сильянов', 'Россия'),
    'kirill danilov': ('Кирилл Данилов', 'Россия'),
    'iker pozo': ('Икер Посо', 'Испания'),
    'christian': ('Кристиан', 'Бразилия'),
    'denis adamov': ('Денис Адамов', 'Россия'),
    'dominik oroz': ('Доминик Ороз', 'Австрия'),
    'nino': ('Нино', 'Бразилия'),
    'andrei kasadzhikov': ('Андрей Касаджиков', 'Россия'),
    'igor diveev': ('Игорь Дивеев', 'Россия'),
    'kevin andrade': ('Кевин Андраде', 'Колумбия'),
    'danil krugovoy': ('Данил Круговой', 'Россия'),
    'konstantin tyukavin': ('Константин Тюкавин', 'Россия'),
    'christopher wooh': ('Кристофер Ву', 'Камерун'),
    'nathan gassama': ('Натан Гассама', 'Франция'),
    'turpal ibishev': ('Турпал Ибишев', 'Россия'),
    'anton miranchuk': ('Антон Миранчук', 'Россия'),
    'román vega': ('Роман Вега', 'Аргентина'),
    'dmitri skopintsev': ('Дмитрий Скопинцев', 'Россия'),
    'lechi sadulaev': ('Лечи Садулаев', 'Россия'),
    'artur garibian': ('Артур Гарибян', 'Россия'),
    'sergei pesyakov': ('Сергей Песьяков', 'Россия'),
    'daniil frolkin': ('Даниил Фролкин', 'Россия'),
    'zelimkhan bakayev': ('Зелимхан Бакаев', 'Россия'),
    'timur suleimanov': ('Тимур Сулейманов', 'Россия'),
    'andrey lunyov': ('Андрей Лунёв', 'Россия'),
    'stanislav agkatsev': ('Станислав Агкацев', 'Россия'),
    'aleksandr maksimenko': ('Александр Максименко', 'Россия'),
    'vladislav torop': ('Владислав Тороп', 'Россия'),
    'gamid agalarov': ('Гамид Агаларов', 'Россия'),
    'georgi melkadze': ('Георгий Мелкадзе', 'Грузия'),
    'batxi': ('Батчи', 'Ангола'),
    'joão victor': ('Жоао Виктор', 'Бразилия'),
    'vítor tormena': ('Витор Тормена', 'Португалия'),
    'eldar ćivić': ('Элдар Чивич', 'Босния и Герцеговина'),
    'brayan gil': ('Брайан Хиль', 'Колумбия'),
    'jacques siwe': ('Жак Сиве', 'Франция'),
    'jhon jhon': ('Джон Джон', 'Бразилия'),
    'esequiel barco': ('Эсекьель Барко', 'Аргентина'),
    'pedrinho santos': ('Педриньо Сантос', 'Бразилия'),
    'viktor okishor': ('Виктор Окишор', 'Россия'),
    'andrés alarcón': ('Андрес Аларкон', 'Колумбия'),
    'nikolai titkov': ('Николай Титков', 'Россия'),
    'andrei mendel': ('Андрей Мендель', 'Россия'),
    'stefan lončar': ('Стефан Лончар', 'Черногория'),
    'ivan oleinikov': ('Иван Олейников', 'Россия'),
    'maksim vityugov': ('Максим Витюгов', 'Россия'),
    'vyacheslav yakimov': ('Вячеслав Якимов', 'Россия'),
    'vitali gudiyev': ('Виталий Гудиев', 'Россия'),
    'rustam yatimov': ('Рустам Ятимов', 'Таджикистан'),
    'ivan oblyakov': ('Иван Обляков', 'Россия'),
    'matija popović': ('Матия Попович', 'Сербия'),
    'kirill glebov': ('Кирилл Глебов', 'Россия'),
    'felipe augusto': ('Фелипе Аугусто', 'Бразилия'),
    'pablo solari': ('Пабло Солари', 'Аргентина'),
    'arthur': ('Артур', 'Бразилия'),
    'miro': ('Миро', 'Бразилия'),
    'chinonso offor': ('Чинонсо Оффор', 'Нигерия'),
    'sergey pinyaev': ('Сергей Пиняев', 'Россия'),
    'danil prutsev': ('Данил Пруцев', 'Россия'),
    'aleksandr sandrachuk': ('Александр Сандрачук', 'Россия'),
    'kevin arévalo': ('Кевин Аревало', 'Колумбия'),
    'gilson benchimol': ('Жилсон Беншимол', 'Кабо-Верде'),
    'marat bokoev': ('Марат Бокоев', 'Россия'),
    'joão escoval': ('Жоао Эсковал', 'Португалия'),
    'konstantin maradishvili': ('Константин Марадишвили', 'Грузия'),
    'slobodan tedić': ('Слободан Тедич', 'Сербия'),
    'aleksa đurasovic': ('Алекса Джурасович', 'Сербия'),
    'kristijan bistrović': ('Кристиян Бистрович', 'Хорватия'),
    'yomar rocha': ('Йомар Роча', 'Боливия'),
    'khetag khosonov': ('Хетаг Хосонов', 'Россия'),
    'ionuț nedelcearu': ('Ионуц Неделчару', 'Румыния'),
    'yuri zheleznov': ('Юрий Железнов', 'Россия'),
    'dudu': ('Дуду', 'Бразилия'),
    'nikita bazilevskii': ('Никита Базилевский', 'Россия'),
    'klisman cake': ('Клиsman Чаке', 'Албания'),
    'miroslav bogosavac': ('Мирослав Богосавац', 'Сербия'),
    'ousmane ndong': ('Усман Ндонг', 'Сенегал'),
    'erald maksuti': ('Эральд Максути', 'Албания'),
    'arsen adamov': ('Арсен Адамов', 'Россия'),
    'julio romão': ('Жулио Ромао', 'Бразилия'),
    'ismael silva lima': ('Исмаэл Силва Лима', 'Бразилия'),
    'maksim samorodov': ('Максим Самородов', 'Казахстан'),
    'vadim ulyanov': ('Вадим Ульянов', 'Россия'),
    'egas cacintura': ('Эгаш Касинтура', 'Ангола'),
    'giorgi shelia': ('Гиорги Шелия', 'Россия'),
    'kirill shchetinin': ('Кирилл Щетинин', 'Россия'),
    'keliano': ('Келиану', 'Ангола'),
    'maksim sidorov': ('Максим Сидоров', 'Россия'),
    'galymzhan kenzhebek': ('Галымжан Кенжебек', 'Казахстан'),
    'kalidou sidibé': ('Калиду Сидибе', 'Франция'),
    'mohamed konaté': ('Мохамед Конате', 'Буркина-Фасо'),
    'mingiyan beveev': ('Мингиян Бевеев', 'Россия'),
    'yevgeni latyshonok': ('Евгений Латышонок', 'Россия'),
    'eduardo anderson': ('Эдуардо Андерсон', 'Панама'),
    'maksim petrov': ('Максим Петров', 'Россия'),
    'aymane mourid': ('Айман Мурид', 'Марокко'),
    'fahd moufi': ('Фахд Муфи', 'Марокко'),
    'maksim borisko': ('Максим Бориско', 'Россия'),
    'loris mouyokolo': ('Лорис Муйоколо', 'Франция'),
    'maksim shnaptsev': ('Максим Шнапцев', 'Россия'),
    'ilya petrov': ('Илья Петров', 'Россия'),
    'vladislav pospelov': ('Владислав Поспелов', 'Россия'),
    'ivan belikov': ('Иван Беликов', 'Россия'),
    'tenton yenne': ('Тентон Йенне', 'Нигерия'),
    'dmitrii nikitin': ('Дмитрий Никитин', 'Россия'),
    'mikhail ryadno': ('Михаил Рядно', 'Россия'),
    'konstantin shiltsov': ('Константин Шильцов', 'Россия')
}

# 2. Универсальный транслитератор для остальных имен
def transliterate_to_russian(text):
    text = text.strip()
    clean_k = text.lower()
    if clean_k in EXACT_PLAYERS:
        return EXACT_PLAYERS[clean_k][0]

    rules = [
        ('shch', 'щ'), ('sch', 'щ'), ('kh', 'х'), ('ts', 'ц'), ('ch', 'ч'),
        ('sh', 'ш'), ('zh', 'ж'), ('yu', 'ю'), ('ya', 'я'), ('yo', 'ё'),
        ('ye', 'е'), ('iy', 'ий'), ('yy', 'ый'), ('ay', 'ай'), ('ey', 'ей'),
        ('oy', 'ой'), ('uy', 'уй'), ('th', 'т'), ('ph', 'ф'), ('gh', 'г'),
        ('dzh', 'дж'), ('ck', 'к'), ('qu', 'кв'), ('w', 'в'), ('x', 'кс')
    ]
    char_map = {
        'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 'e': 'е', 'z': 'з',
        'i': 'и', 'j': 'й', 'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о',
        'p': 'п', 'r': 'р', 's': 'с', 't': 'т', 'u': 'у', 'f': 'ф', 'h': 'х',
        'c': 'к', 'y': 'ы', 'q': 'к', 'w': 'в', 'x': 'кс'
    }

    words = text.split()
    ru_words = []
    for w in words:
        w_low = w.lower()
        for lat, cyr in rules:
            w_low = w_low.replace(lat, cyr)
        res = ""
        for ch in w_low:
            res += char_map.get(ch, ch)
        ru_words.append(res.capitalize())

    return " ".join(ru_words)

def sync_roster():
    print("⏳ Синхронизация Google Таблицы V3 с автопереводом на русский...")

    try:
        res = requests.get(CSV_URL, timeout=20)
        res.encoding = 'utf-8'
        if res.status_code != 200:
            print(f"Ошибка доступа к CSV: {res.status_code}")
            return
    except Exception as e:
        print(f"Ошибка сетевого запроса: {e}")
        return

    database = {
        "GK": [],
        "DEF": [],
        "MID": [],
        "FWD": []
    }

    f = io.StringIO(res.text)
    reader = csv.DictReader(f)

    loaded_count = 0
    for row in reader:
        eng_name = row.get("Игрок", "").strip()
        club = row.get("Клуб", "").strip()
        raw_role = row.get("Амплуа", "").strip()
        raw_points = row.get("Очки", "0").strip()
        next_match = row.get("Следующий матч", "").strip()

        if not eng_name or not raw_role:
            continue

        role_key = ROLE_MAP.get(raw_role, "MID")

        try:
            points = int(raw_points)
        except ValueError:
            points = 0

        # Перевод имени на русский и определение страны
        eng_lower = eng_name.lower()
        if eng_lower in EXACT_PLAYERS:
            rus_name, country = EXACT_PLAYERS[eng_lower]
        else:
            rus_name = transliterate_to_russian(eng_name)
            country = "Россия"

        player_card = {
            "name": rus_name,
            "club": club,
            "country": country,
            "tier": raw_role,
            "points": points,
            "next_match": next_match
        }

        database[role_key].append(player_card)
        loaded_count += 1

    with open("players.json", "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)

    print(f"✅ Успешно! {loaded_count} игроков переведены на русский язык и записаны в players.json!")

if __name__ == "__main__":
    sync_roster()
