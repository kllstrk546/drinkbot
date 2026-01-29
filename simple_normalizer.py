def simple_normalize_city(city_input: str) -> str:
    """Простая нормализация города без API зависаний"""
    
    if not city_input:
        return ""
    
    city_lower = city_input.lower().strip()
    
    # Прямые соответствия
    city_mappings = {
        "киев": "Kyiv",
        "київ": "Kyiv", 
        "kyiv": "Kyiv",
        "москва": "Moscow",
        "санкт-петербург": "Saint Petersburg",
        "спб": "Saint Petersburg",
        "минск": "Minsk",
        "харьков": "Kharkiv",
        "одесса": "Odesa",
        "днепр": "Dnipro",
        "донецк": "Donetsk",
        "запорожье": "Zaporizhzhia",
        "львов": "Lviv",
        "кривой рог": "Kryvyi Rih",
        "николаев": "Mykolaiv",
        "мариуполь": "Mariupol",
        "луганск": "Luhansk",
        "севастополь": "Sevastopol",
        "симферополь": "Simferopol",
        "винница": "Vinnytsia",
        "херсон": "Kherson",
        "полтава": "Poltava",
        "чернигов": "Chernihiv",
        "черкассы": "Cherkasy",
        "житомир": "Zhytomyr",
        "сумы": "Sumy",
        "ровно": "Rivne",
        "тернополь": "Ternopil",
        "луцк": "Lutsk",
        "белая церковь": "Bila Tserkva",
        "кременчуг": "Kremenchuk",
        "ивано-франковск": "Ivano-Frankivsk",
        "дрогобыч": "Drohobych",
        "каменец-подольский": "Kamianets-Podilskyi",
        "ужгород": "Uzhhorod",
        "бердянск": "Berdiansk",
        "павлоград": "Pavlohrad",
        "алчевск": "Alchevsk",
        "лисичанск": "Lysychansk",
        "северодонецк": "Sievierodonetsk",
        # Российские города
        "новосибирск": "Novosibirsk",
        "екатеринбург": "Yekaterinburg",
        "ташкент": "Tashkent",
        "казань": "Kazan",
        "нижний новгород": "Nizhny Novgorod",
        "челябинск": "Chelyabinsk",
        "алматы": "Almaty",
        "самара": "Samara",
        "уфа": "Ufa",
        "ростов-на-дону": "Rostov-on-Don",
        "красноярск": "Krasnoyarsk",
        "омск": "Omsk",
        "воронеж": "Voronezh",
        "пермь": "Perm",
        "волгоград": "Volgograd",
        "краснодар": "Krasnodar",
        "саратов": "Saratov",
        "тюмень": "Tyumen",
        "тольятти": "Tolyatti",
        "барнаул": "Barnaul",
        "ульяновск": "Ulyanovsk",
        "иркутск": "Irkutsk",
        "хабаровск": "Khabarovsk",
        "махачкала": "Makhachkala",
        "владивосток": "Vladivostok",
        "ярославль": "Yaroslavl",
        "оренбург": "Orenburg",
        "томск": "Tomsk",
        "кемерово": "Kemerovo",
        "рязань": "Ryazan",
        "набережные челны": "Naberezhnye Chelny",
        "астана": "Astana",
        "пенза": "Penza",
        "киров": "Kirov",
        "липецк": "Lipetsk",
        "чебоксары": "Cheboksary",
        "балашиха": "Balashikha"
    }
    
    # Проверяем точное соответствие
    if city_lower in city_mappings:
        return city_mappings[city_lower]
    
    # Проверяем с опечатками (простая эвристика)
    for known_city, english_name in city_mappings.items():
        # Если разница в 1-2 символах - считаем опечаткой
        if abs(len(city_lower) - len(known_city)) <= 2 and city_lower[:3] == known_city[:3]:
            return english_name
    
    # Если ничего не найдено - возвращаем как есть с заглавной буквы
    return city_input.title()

# Тест
if __name__ == "__main__":
    test_cities = ["Киев", "киев", "Кипв", "Масква", "СПБ", "харьков"]
    
    for city in test_cities:
        result = simple_normalize_city(city)
        print(f"'{city}' -> '{result}'")
