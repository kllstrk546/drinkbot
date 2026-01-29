import sqlite3


def main():
    conn = sqlite3.connect("drink_bot.db")
    cur = conn.cursor()

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
    print("Active Kyiv bots by gender (today):")
    for gender, cnt in rows:
        print(f"  {gender}: {cnt}")

    cur.execute(
        """
        SELECT gender, COUNT(*) as cnt
        FROM profiles
        WHERE is_bot = 1
          AND city_normalized = 'Kyiv'
          AND last_rotation_date = DATE('now')
          AND photo_id IS NOT NULL AND photo_id != ''
        GROUP BY gender
        ORDER BY gender
        """
    )
    rows = cur.fetchall()
    print("\nActive Kyiv bots with photos by gender (today):")
    for gender, cnt in rows:
        print(f"  {gender}: {cnt}")

    cur.execute(
        """
        SELECT gender, COUNT(*) as cnt
        FROM profiles
        WHERE is_bot = 1
          AND city_normalized = 'Kyiv'
          AND last_rotation_date = DATE('now')
          AND photo_id IS NOT NULL AND photo_id != ''
          AND (
            SELECT COUNT(*)
            FROM profiles p2
            WHERE p2.photo_id = profiles.photo_id AND p2.is_bot = 1 AND p2.gender != profiles.gender
          ) = 0
        GROUP BY gender
        ORDER BY gender
        """
    )
    rows = cur.fetchall()
    print("\nActive Kyiv bots with correct-gender photos (today):")
    for gender, cnt in rows:
        print(f"  {gender}: {cnt}")

    cur.execute(
        """
        SELECT gender, COUNT(*) as cnt
        FROM profiles
        WHERE is_bot = 1
          AND city_normalized = 'Kyiv'
          AND last_rotation_date = DATE('now')
          AND photo_id IS NOT NULL AND photo_id != ''
          AND (
            SELECT COUNT(*)
            FROM profiles p2
            WHERE p2.photo_id = profiles.photo_id AND p2.is_bot = 1 AND p2.gender != profiles.gender
          ) > 0
        GROUP BY gender
        ORDER BY gender
        """
    )
    rows = cur.fetchall()
    print("\nActive Kyiv bots with wrong-gender photos (today):")
    for gender, cnt in rows:
        print(f"  {gender}: {cnt}")

    conn.close()


if __name__ == "__main__":
    main()
