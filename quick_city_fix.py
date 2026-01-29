import sqlite3

def fix_city_normalization():
    """Быстрое исправление - добавим прямую нормализацию для Киева"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    # Обновим всех ботов у которых city_normalized не правильный
    cursor.execute('''
        UPDATE profiles 
        SET city_normalized = 'Kyiv' 
        WHERE city_normalized LIKE '%%' 
        AND (city LIKE 'Киев%' OR city LIKE 'Київ%' OR city LIKE 'Kyiv%')
        AND is_bot = 1
    ''')
    
    updated_count = cursor.rowcount
    conn.commit()
    
    print(f'Fixed city normalization for {updated_count} bots')
    
    # Проверим результат
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv"')
    kyiv_count = cursor.fetchone()[0]
    
    print(f'Total bots in Kyiv now: {kyiv_count}')
    
    conn.close()

if __name__ == "__main__":
    fix_city_normalization()
