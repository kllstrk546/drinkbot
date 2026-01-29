import sqlite3

def fix_state_profiles():
    """Исправляем проблему с state profiles"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    user_id = 547486189
    city_normalized = 'Kyiv'
    
    print("FIXING STATE PROFILES ISSUE:")
    print("=" * 40)
    
    # Получаем все профили как в коде
    cursor.execute('''
        SELECT user_id, name, gender, who_pays, photo_id
        FROM profiles 
        WHERE user_id != ? 
        AND city_normalized = ?
        AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
        AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
        ORDER BY RANDOM()
        LIMIT 10
    ''', (user_id, city_normalized, user_id, user_id, city_normalized))
    
    profiles = cursor.fetchall()
    print(f"Should be {len(profiles)} profiles in state")
    
    # Показываем все профили
    print("\nAll profiles that should be available:")
    for i, profile in enumerate(profiles):
        user_id_bot, name, gender, who_pays, photo_id = profile
        print(f"  {i+1}. {name} ({gender}) - {who_pays} - {photo_id[:30] if photo_id else 'NO PHOTO'}...")
    
    # Проверяем есть ли проблема с who_pays
    who_pays_dist = {}
    for profile in profiles:
        wp = profile[3]
        who_pays_dist[wp] = who_pays_dist.get(wp, 0) + 1
    
    print(f"\nWho_pays distribution:")
    for wp, count in who_pays_dist.items():
        print(f"  {wp}: {count}")
    
    conn.close()
    
    print("\nSOLUTION:")
    print("1. Clear FSM state in bot")
    print("2. Start new search")
    print("3. Should show all profiles")

if __name__ == "__main__":
    fix_state_profiles()
