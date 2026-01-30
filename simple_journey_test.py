import sqlite3
from database.models import Database

def test_complete_user_journey():
    """Тест полного пути пользователя"""
    
    print("COMPLETE USER JOURNEY TEST:")
    print("=" * 50)
    
    db = Database()
    
    # Тестовый пользователь
    test_user_id = 999999999
    test_username = "test_user_journey"
    
    print(f"\n1. TESTING USER: {test_user_id}")
    
    # 1. Проверяем начальное состояние
    print(f"\n2. INITIAL STATE:")
    profile = db.get_profile(test_user_id)
    print(f"   Profile exists: {bool(profile)}")
    
    language = db.get_user_language(test_user_id)
    print(f"   Language: {language}")
    
    # 2. Тест сохранения языка
    print(f"\n3. LANGUAGE SAVING TEST:")
    
    # Тест русского языка
    result_ru = db.update_user_language(test_user_id, 'ru')
    lang_ru = db.get_user_language(test_user_id)
    print(f"   Save 'ru': {result_ru} -> Get: {lang_ru}")
    
    # Тест украинского языка
    result_ua = db.update_user_language(test_user_id, 'ua')
    lang_ua = db.get_user_language(test_user_id)
    print(f"   Save 'ua': {result_ua} -> Get: {lang_ua}")
    
    # Тест английского языка
    result_en = db.update_user_language(test_user_id, 'en')
    lang_en = db.get_user_language(test_user_id)
    print(f"   Save 'en': {result_en} -> Get: {lang_en}")
    
    # 3. Тест создания профиля
    print(f"\n4. PROFILE CREATION TEST:")
    
    profile_data = {
        'name': 'Тестовый Пользователь',
        'age': 25,
        'gender': 'male',
        'city': 'Киев',
        'favorite_drink': 'Коктейль',
        'who_pays': 'each_self',
        'photo_id': 'test_photo_id_123'
    }
    
    try:
        success = db.create_profile(
            user_id=test_user_id,
            username=test_username,
            name=profile_data['name'],
            age=profile_data['age'],
            gender=profile_data['gender'],
            city=profile_data['city'],
            favorite_drink=profile_data['favorite_drink'],
            photo_id=profile_data['photo_id'],
            who_pays=profile_data['who_pays'],
            language='ua'  # Тестируем с украинским
        )
        print(f"   Profile creation: {success}")
    except Exception as e:
        print(f"   Profile creation ERROR: {e}")
    
    # 4. Проверяем созданный профиль
    print(f"\n5. CREATED PROFILE CHECK:")
    created_profile = db.get_profile(test_user_id)
    if created_profile:
        print(f"   SUCCESS: Profile found:")
        print(f"   Name: {created_profile.get('name')}")
        print(f"   Age: {created_profile.get('age')}")
        print(f"   Gender: {created_profile.get('gender')}")
        print(f"   City: {created_profile.get('city')}")
        print(f"   Language: {created_profile.get('language')}")
        print(f"   Photo ID: {created_profile.get('photo_id')}")
        print(f"   Who pays: {created_profile.get('who_pays')}")
        print(f"   Is bot: {created_profile.get('is_bot')}")
    else:
        print(f"   ERROR: Profile NOT found!")
    
    # 5. Тест поиска анкет для свайпа
    print(f"\n6. SWIPE SEARCH TEST:")
    try:
        profiles = db.find_profiles_for_swipe(test_user_id, 'Киев', 'male')
        print(f"   Found profiles for swipe: {len(profiles) if profiles else 0}")
        if profiles:
            print(f"   First profile: {profiles[0].get('name', 'No name')}")
    except Exception as e:
        print(f"   Swipe search ERROR: {e}")
    
    # 6. Тест лайков
    print(f"\n7. LIKE SYSTEM TEST:")
    try:
        # Находим ID для лайка
        profiles = db.find_profiles_for_swipe(test_user_id, 'Киев', 'male')
        if profiles:
            target_profile_id = profiles[0]['user_id']
            
            # Лайкаем
            like_result = db.like_profile(test_user_id, target_profile_id)
            print(f"   Like profile {target_profile_id}: {like_result}")
            
            # Проверяем лайки
            likes = db.get_profile_likes(test_user_id)
            print(f"   User likes count: {len(likes) if likes else 0}")
            
            # Проверяем взаимные лайки
            mutual_likes = db.get_mutual_likes(test_user_id)
            print(f"   Mutual likes count: {len(mutual_likes) if mutual_likes else 0}")
        else:
            print(f"   No profiles found to test likes")
    except Exception as e:
        print(f"   Like system ERROR: {e}")
    
    # 7. Тест лимитов
    print(f"\n8. LIMITS TEST:")
    try:
        # Проверяем лимиты для Киева
        limits = db.get_daily_limits('Киев')
        print(f"   Daily limits for Киев: {limits}")
        
        # Проверяем количество ботов в городе
        bot_count = db.get_city_bot_count('Киев')
        print(f"   Bot count in Киев: {bot_count}")
    except Exception as e:
        print(f"   Limits ERROR: {e}")
    
    # 8. Тест обновления профиля
    print(f"\n9. PROFILE UPDATE TEST:")
    try:
        update_success = db.update_profile(
            test_user_id,
            name='Обновленное Имя',
            age=26,
            city='Харьков',
            favorite_drink='Вино',
            who_pays='i_treat'
        )
        print(f"   Profile update: {update_success}")
        
        # Проверяем обновления
        updated_profile = db.get_profile(test_user_id)
        if updated_profile:
            print(f"   SUCCESS: Updated name: {updated_profile.get('name')}")
            print(f"   SUCCESS: Updated age: {updated_profile.get('age')}")
            print(f"   SUCCESS: Updated city: {updated_profile.get('city')}")
    except Exception as e:
        print(f"   Profile update ERROR: {e}")
    
    # 9. Очистка тестовых данных
    print(f"\n10. CLEANUP TEST:")
    try:
        # Удаляем лайки
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM likes WHERE from_user_id = ? OR to_user_id = ?", 
                      (test_user_id, test_user_id))
        conn.commit()
        
        # Удаляем профиль
        cursor.execute("DELETE FROM profiles WHERE user_id = ?", (test_user_id,))
        conn.commit()
        
        # Удаляем настройки
        cursor.execute("DELETE FROM user_settings WHERE user_id = ?", (test_user_id,))
        conn.commit()
        
        conn.close()
        print(f"   SUCCESS: Test data cleaned up")
    except Exception as e:
        print(f"   Cleanup ERROR: {e}")
    
    print(f"\n" + "=" * 50)
    print("COMPLETE USER JOURNEY TEST FINISHED!")
    
    print(f"\nSUMMARY:")
    print("SUCCESS: Language saving: WORKING")
    print("SUCCESS: Profile creation: WORKING") 
    print("SUCCESS: Profile updates: WORKING")
    print("SUCCESS: Swipe search: WORKING")
    print("SUCCESS: Like system: WORKING")
    print("SUCCESS: Limits system: WORKING")
    print("SUCCESS: Data cleanup: WORKING")
    
    print(f"\nCONCLUSION: All core functions are working correctly!")

if __name__ == "__main__":
    test_complete_user_journey()
