import sqlite3
from datetime import datetime

def complete_language_diagnosis():
    """Полная диагностика всех языков и функций"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    print("COMPLETE LANGUAGE AND FUNCTION DIAGNOSIS:")
    print("=" * 70)
    
    # 1. Проверяем таблицу user_settings
    print(f"\n1. USER_SETTINGS TABLE:")
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
        table_exists = cursor.fetchone()
        if table_exists:
            print("   ✅ user_settings table exists")
            cursor.execute("SELECT COUNT(*) FROM user_settings")
            count = cursor.fetchone()[0]
            print(f"   Records: {count}")
            
            cursor.execute("SELECT user_id, language FROM user_settings LIMIT 5")
            settings = cursor.fetchall()
            for user_id, lang in settings:
                print(f"   User {user_id}: {lang}")
        else:
            print("   ❌ user_settings table NOT exists")
    except Exception as e:
        print(f"   ❌ Error checking user_settings: {e}")
    
    # 2. Проверяем профили и языки
    print(f"\n2. PROFILES AND LANGUAGES:")
    cursor.execute('''
        SELECT user_id, name, language, is_bot 
        FROM profiles 
        ORDER BY user_id DESC 
        LIMIT 10
    ''')
    
    profiles = cursor.fetchall()
    print(f"   Recent profiles:")
    for user_id, name, language, is_bot in profiles:
        bot_status = "BOT" if is_bot else "REAL"
        print(f"   User {user_id} ({bot_status}): {name} - Language: {language}")
    
    # 3. Проверяем языковую статистику
    print(f"\n3. LANGUAGE STATISTICS:")
    cursor.execute('''
        SELECT language, COUNT(*) as count
        FROM profiles 
        WHERE is_bot = 0
        GROUP BY language
    ''')
    
    lang_stats = cursor.fetchall()
    print(f"   Real users by language:")
    for lang, count in lang_stats:
        print(f"   {lang}: {count} users")
    
    # 4. Проверяем все сообщения в locales.py
    print(f"\n4. LOCALES.PY MESSAGES CHECK:")
    try:
        with open('locales.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем ключевые сообщения
        required_messages = [
            'profile_already_exists',
            'btn_update_profile',
            'welcome',
            'select_language',
            'profile_name_prompt',
            'btn_fill_profile',
            'btn_edit_profile',
            'section_profile',
            'section_dating',
            'btn_find_dating_my_city',
            'btn_find_dating_other_city',
            'premium_title',
            'btn_buy_premium'
        ]
        
        print(f"   Checking required messages:")
        for msg in required_messages:
            if f'"{msg}":' in content:
                print(f"   ✅ {msg} - found")
            else:
                print(f"   ❌ {msg} - MISSING!")
                
    except Exception as e:
        print(f"   ❌ Error reading locales.py: {e}")
    
    # 5. Проверяем структуру сообщений
    print(f"\n5. MESSAGE STRUCTURE CHECK:")
    try:
        with open('locales.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Ищем profile_already_exists
        for i, line in enumerate(lines):
            if 'profile_already_exists' in line:
                print(f"   Found profile_already_exists at line {i+1}")
                # Показываем следующие 10 строк
                for j in range(max(0, i), min(len(lines), i+15)):
                    print(f"   {j+1:3d}: {lines[j].rstrip()}")
                break
        else:
            print("   ❌ profile_already_exists not found")
            
    except Exception as e:
        print(f"   ❌ Error checking message structure: {e}")
    
    # 6. Проверяем функции get_message
    print(f"\n6. GET_MESSAGE FUNCTION CHECK:")
    try:
        with open('locales.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'def get_message' in content:
            print("   ✅ get_message function exists")
            
            # Проверяем обработку ошибок
            if 'KeyError' in content or 'except' in content:
                print("   ✅ Error handling found")
            else:
                print("   ⚠️  No error handling found")
        else:
            print("   ❌ get_message function NOT found")
            
    except Exception as e:
        print(f"   ❌ Error checking get_message: {e}")
    
    # 7. Проверяем языковые кнопки
    print(f"\n7. LANGUAGE BUTTONS CHECK:")
    try:
        with open('handlers/start.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем кнопки заполнения анкеты
        if '📝 Заполнить анкету' in content and '📝 Заповнити анкету' in content:
            print("   ✅ Profile buttons for RU/UA found")
        else:
            print("   ❌ Profile buttons missing")
            
        # Проверяем кнопки секций
        if '👤 Мой профиль' in content and '👤 Мій профіль' in content:
            print("   ✅ Section buttons for RU/UA found")
        else:
            print("   ❌ Section buttons missing")
            
    except Exception as e:
        print(f"   ❌ Error checking buttons: {e}")
    
    # 8. Проверяем обработчики языка
    print(f"\n8. LANGUAGE HANDLERS CHECK:")
    try:
        with open('handlers/start.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'get_lang' in content:
            print("   ✅ get_lang function found")
        else:
            print("   ❌ get_lang function NOT found")
            
        if 'get_user_language' in content:
            print("   ✅ get_user_language function found")
        else:
            print("   ❌ get_user_language function NOT found")
            
        if 'language_selection_callback' in content:
            print("   ✅ language_selection_callback found")
        else:
            print("   ❌ language_selection_callback NOT found")
            
    except Exception as e:
        print(f"   ❌ Error checking handlers: {e}")
    
    conn.close()
    
    print(f"\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE!")
    
    print(f"\nNEXT STEPS:")
    print("1. Check for missing messages in locales.py")
    print("2. Verify language buttons in handlers/start.py")
    print("3. Test language switching functionality")
    print("4. Check get_message function error handling")
    print("5. Verify user_settings table creation")

if __name__ == "__main__":
    complete_language_diagnosis()
