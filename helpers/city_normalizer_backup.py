"""
City normalization helper - простая версия без зависаний
"""
import logging

def normalize_city_name(city_input: str) -> str:
    """
    Простая нормализация города без API зависаний
    """
    if not city_input:
        return ""
    
    city_lower = city_input.lower().strip()
    
    # Простые соответствия
    city_mappings = {
        "киев": "Kyiv", "київ": "Kyiv", "kyiv": "Kyiv",
        "москва": "Moscow", "санкт-петербург": "Saint Petersburg", "спб": "Saint Petersburg",
        "минск": "Minsk", "харьков": "Kharkiv", "одесса": "Odesa", "днепр": "Dnipro",
        "донецк": "Donetsk", "запорожье": "Zaporizhzhia", "львов": "Lviv",
        "новосибирск": "Novosibirsk", "екатеринбург": "Yekaterinburg", "ташкент": "Tashkent",
        "казань": "Kazan", "нижний новгород": "Nizhny Novgorod", "челябинск": "Chelyabinsk",
        "алматы": "Almaty", "самара": "Samara", "уфа": "Ufa", "ростов-на-дону": "Rostov-on-Don",
        "красноярск": "Krasnoyarsk", "омск": "Omsk", "воронеж": "Voronezh", "пермь": "Perm",
        "волгоград": "Volgograd", "краснодар": "Krasnodar", "саратов": "Saratov", "тюмень": "Tyumen",
        "тольятти": "Tolyatti", "барнаул": "Barnaul", "ульяновск": "Ulyanovsk", "иркутск": "Irkutsk",
        "хабаровск": "Khabarovsk", "махачкала": "Makhachkala", "владивосток": "Vladivostok",
        "ярославль": "Yaroslavl", "оренбург": "Orenburg", "томск": "Tomsk", "кемерово": "Kemerovo",
        "рязань": "Ryazan", "набережные челны": "Naberezhnye Chelny", "астана": "Astana",
        "пенза": "Penza", "киров": "Kirov", "липецк": "Lipetsk", "чебоксары": "Cheboksary",
        "балашиха": "Balashikha", "николаев": "Mykolaiv"
    }
    
    return city_mappings.get(city_lower, city_input.title())

def smart_city_to_english(city_text: str) -> str:
    """
    Smart city translation to English for registration.
    """
    return normalize_city_name(city_text)
