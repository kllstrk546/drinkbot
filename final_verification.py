import sqlite3


def main():
    conn = sqlite3.connect("drink_bot.db")
    cur = conn.cursor()

    print("=== FINAL VERIFICATION ===")
    print("1. Global photo correctness")
    cur.execute(
        """
        SELECT m.gender, COUNT(*) as cnt
        FROM profiles m
        JOIN profiles f ON m.photo_id = f.photo_id AND f.is_bot = 1
        WHERE m.is_bot = 1
          AND m.photo_id IS NOT NULL AND m.photo_id != ''
          AND m.gender != f.gender
        GROUP BY m.gender
        ORDER BY m.gender
        """
    )
    rows = cur.fetchall()
    global_wrong = sum(cnt for _, cnt in rows)
    print(f"  Global bots with wrong-gender photos: {global_wrong}")
    for gender, cnt in rows:
        print(f"    {gender}: {cnt}")

    print("\n2. Kyiv active bots")
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
    print("  Active Kyiv bots by gender:")
    for gender, cnt in rows:
        print(f"    {gender}: {cnt}")

    print("\n3. Kyiv bots with photos")
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
    print("  Kyiv bots with photos by gender:")
    for gender, cnt in rows:
        print(f"    {gender}: {cnt}")

    print("\n4. Kyiv bots with correct photos")
    cur.execute(
        """
        SELECT m.gender, COUNT(*) as cnt
        FROM profiles m
        JOIN profiles f ON m.photo_id = f.photo_id AND f.is_bot = 1
        WHERE m.is_bot = 1
          AND m.city_normalized = 'Kyiv'
          AND m.last_rotation_date = DATE('now')
          AND m.photo_id IS NOT NULL AND m.photo_id != ''
          AND m.gender = f.gender
        GROUP BY m.gender
        ORDER BY m.gender
        """
    )
    rows = cur.fetchall()
    print("  Kyiv bots with correct-gender photos:")
    for gender, cnt in rows:
        print(f"    {gender}: {cnt}")

    print("\n5. Sample Kyiv bots")
    cur.execute(
        """
        SELECT m.user_id, m.name, m.gender, f.name as photo_source, f.gender as photo_gender
        FROM profiles m
        JOIN profiles f ON m.photo_id = f.photo_id AND f.is_bot = 1
        WHERE m.is_bot = 1
          AND m.city_normalized = 'Kyiv'
          AND m.last_rotation_date = DATE('now')
          AND m.photo_id IS NOT NULL AND m.photo_id != ''
        ORDER BY m.gender, m.user_id
        LIMIT 6
        """
    )
    rows = cur.fetchall()
    print("  Sample Kyiv bots:")
    for row in rows:
        status = "OK" if row[2] == row[4] else "WRONG"
        print(f"    {row[1]} ({row[2]}) <- {row[3]} ({row[4]}) [{status}]")

    conn.close()


if __name__ == "__main__":
    main()
