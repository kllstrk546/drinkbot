import sqlite3


def main():
    conn = sqlite3.connect("drink_bot.db")
    cur = conn.cursor()

    # Получаем всех активных ботов в Киеве
    cur.execute(
        """
        SELECT user_id, gender, name, photo_id
        FROM profiles
        WHERE is_bot = 1
          AND city_normalized = 'Kyiv'
          AND last_rotation_date = DATE('now')
        ORDER BY gender, user_id
        """
    )
    bots = cur.fetchall()
    print(f"Total active Kyiv bots: {len(bots)}")
    for g, cnt in [('male', 0), ('female', 0)]:
        cnt = sum(1 for b in bots if b[1] == g)
        print(f"  {g}: {cnt}")

    # Цель: 19-20 мужчин, 19 женщин (парней чуть больше)
    target_male = 20
    target_female = 19

    male_bots = [b for b in bots if b[1] == 'male']
    female_bots = [b for b in bots if b[1] == 'female']

    print(f"\nTarget: male={target_male}, female={target_female}")

    # Если мужчин меньше, конвертируем женщин в мужчин
    if len(male_bots) < target_male:
        needed = target_male - len(male_bots)
        print(f"Need to convert {needed} female -> male")
        for i in range(min(needed, len(female_bots))):
            bot = female_bots[i]
            user_id = bot[0]
            cur.execute("UPDATE profiles SET gender = 'male' WHERE user_id = ?", (user_id,))
            print(f"  Converted {bot[2]} (ID {user_id}) to male")

    # Если женщин меньше, конвертируем мужчин в женщин
    if len(female_bots) < target_female:
        needed = target_female - len(female_bots)
        print(f"Need to convert {needed} male -> female")
        # Получаем обновленный список мужчин
        cur.execute(
            """
            SELECT user_id, gender, name, photo_id
            FROM profiles
            WHERE is_bot = 1
              AND city_normalized = 'Kyiv'
              AND last_rotation_date = DATE('now')
              AND gender = 'male'
            ORDER BY user_id
            """
        )
        updated_male_bots = cur.fetchall()
        for i in range(min(needed, len(updated_male_bots))):
            bot = updated_male_bots[i]
            user_id = bot[0]
            cur.execute("UPDATE profiles SET gender = 'female' WHERE user_id = ?", (user_id,))
            print(f"  Converted {bot[2]} (ID {user_id}) to female")

    conn.commit()

    # Проверяем результат
    cur.execute(
        """
        SELECT gender, COUNT(*) as cnt
        FROM profiles
        WHERE is_bot = 1
          AND city_normalized = 'Kyiv'
          AND last_rotation_date = DATE('now')
        GROUP BY gender
        ORDER BY gender
        """
    )
    rows = cur.fetchall()
    print("\nAfter balancing:")
    for gender, cnt in rows:
        print(f"  {gender}: {cnt}")

    conn.close()


if __name__ == "__main__":
    main()
