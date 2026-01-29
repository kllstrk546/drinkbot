import sqlite3
import random

def restore_who_pays():
    """Возвращаем who_pays обратно как было (рандомное распределение)"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    city_normalized = 'Kyiv'
    
    print("RESTORING WHO_PAYS TO ORIGINAL STATE:")
    print("=" * 50)
    
    # Варианты who_pays
    who_pays_options = ['i_treat', 'someone_treats', 'each_self']
    
    # Получаем всех ботов в Киеве
    cursor.execute('''
        SELECT user_id, name, gender, who_pays
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ?
        ORDER BY gender, name
    ''', (city_normalized,))
    
    all_bots = cursor.fetchall()
    print(f"Total bots in Kyiv: {len(all_bots)}")
    
    # Возвращаем случайное распределение
    updated_count = 0
    for bot in all_bots:
        bot_id, name, gender, current_who_pays = bot
        
        # Выбираем случайное значение
        new_who_pays = random.choice(who_pays_options)
        
        if current_who_pays != new_who_pays:
            cursor.execute('UPDATE profiles SET who_pays = ? WHERE user_id = ?', (new_who_pays, bot_id))
            updated_count += 1
            print(f"  {name} ({gender}): {current_who_pays} -> {new_who_pays}")
    
    conn.commit()
    print(f"Updated {updated_count} bots with random who_pays")
    
    # Проверяем распределение
    print("\nNew who_pays distribution:")
    cursor.execute('''
        SELECT who_pays, COUNT(*) 
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ?
        GROUP BY who_pays
        ORDER BY who_pays
    ''', (city_normalized,))
    
    distribution = cursor.fetchall()
    for wp, count in distribution:
        print(f"  {wp}: {count} bots")
    
    conn.close()
    print("WHO_PAYS RESTORED TO ORIGINAL STATE!")

if __name__ == "__main__":
    restore_who_pays()
