import sqlite3
from datetime import datetime

def check_profile_creation_issue():
    """Проверка проблемы создания профилей"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    print("CHECKING PROFILE CREATION ISSUE:")
    print("=" * 60)
    
    # 1. Проверяем структуру таблицы profiles
    print(f"\n1. PROFILES TABLE STRUCTURE:")
    cursor.execute("PRAGMA table_info(profiles)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"   {col[1]}: {col[2]}")
    
    # 2. Проверяем все профили
    print(f"\n2. ALL PROFILES IN DATABASE:")
    cursor.execute('''
        SELECT user_id, name, age, gender, city, created_at, is_bot 
        FROM profiles 
        ORDER BY created_at DESC 
        LIMIT 10
    ''')
    
    profiles = cursor.fetchall()
    print(f"   Total profiles: {len(profiles)}")
    
    for profile in profiles:
        user_id, name, age, gender, city, created_at, is_bot = profile
        print(f"   ID: {user_id}, Name: {name}, Age: {age}, Gender: {gender}, City: {city}, Bot: {is_bot}, Created: {created_at}")
    
    # 3. Проверяем конкретные поля которые могут быть NULL
    print(f"\n3. CHECKING NULL VALUES:")
    
    cursor.execute('''
        SELECT COUNT(*) as total,
               COUNT(name) as has_name,
               COUNT(age) as has_age,
               COUNT(gender) as has_gender,
               COUNT(city) as has_city,
               COUNT(favorite_drink) as has_drink,
               COUNT(photo_id) as has_photo
        FROM profiles WHERE is_bot = 0
    ''')
    
    null_stats = cursor.fetchone()
    print(f"   Real users total: {null_stats[0]}")
    print(f"   Has name: {null_stats[1]}")
    print(f"   Has age: {null_stats[2]}")
    print(f"   Has gender: {null_stats[3]}")
    print(f"   Has city: {null_stats[4]}")
    print(f"   Has drink: {null_stats[5]}")
    print(f"   Has photo: {null_stats[6]}")
    
    # 4. Проверяем метод create_profile в database/models.py
    print(f"\n4. POTENTIAL ISSUES:")
    print("   Check if create_profile() properly saves all fields")
    print("   Check if get_profile() properly retrieves profiles")
    print("   Check if city_normalized is being set correctly")
    
    # 5. Проверяем последние операции
    print(f"\n5. RECENT OPERATIONS:")
    
    # Ищем профили созданные сегодня
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT user_id, name, created_at 
        FROM profiles 
        WHERE created_at LIKE ?
        ORDER BY created_at DESC
    ''', (f"{today}%",))
    
    today_profiles = cursor.fetchall()
    print(f"   Profiles created today: {len(today_profiles)}")
    
    for user_id, name, created_at in today_profiles:
        print(f"   ID: {user_id}, Name: {name}, Time: {created_at}")
    
    conn.close()
    
    print(f"\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE!")
    
    if len(profiles) == 0:
        print("❌ NO PROFILES FOUND - create_profile() may be failing")
    elif len(profiles) > 0:
        print("✅ PROFILES EXIST - issue may be in get_profile() or filters")
    
    print("\nNEXT STEPS:")
    print("1. Check create_profile() method in database/models.py")
    print("2. Check get_profile() method in database/models.py")
    print("3. Add logging to profile creation process")
    print("4. Check if city_normalized is being set")

if __name__ == "__main__":
    check_profile_creation_issue()
