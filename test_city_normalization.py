from helpers.city_normalizer import normalize_city_name

city_input = 'Киев'
normalized = normalize_city_name(city_input)
print(f'"{city_input}" -> "{normalized}"')

# Проверим другие варианты
test_cities = ['Киев', 'киев', 'KYIV', 'Kyiv']
for city in test_cities:
    result = normalize_city_name(city)
    print(f'"{city}" -> "{result}"')
