import sqlite3

def main():
    conn = sqlite3.connect('drink_bot.db')
    cur = conn.cursor()

    # Kyiv check
    cur.execute(
        """
        SELECT COUNT(*)
        FROM profiles m
        JOIN profiles f ON m.photo_id = f.photo_id
        WHERE m.is_bot = 1
          AND m.city_normalized = 'Kyiv'
          AND m.gender = 'male'
          AND m.photo_id IS NOT NULL AND m.photo_id != ''
          AND f.is_bot = 1
          AND f.gender = 'female'
        """
    )
    kyiv_wrong = cur.fetchone()[0]

    # Global check
    cur.execute(
        """
        SELECT COUNT(*)
        FROM profiles m
        JOIN profiles f ON m.photo_id = f.photo_id
        WHERE m.is_bot = 1
          AND m.gender = 'male'
          AND m.photo_id IS NOT NULL AND m.photo_id != ''
          AND f.is_bot = 1
          AND f.gender = 'female'
        """
    )
    global_wrong = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*)
        FROM profiles
        WHERE is_bot = 1 AND gender='male'
        """
    )
    total_male_bots = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*)
        FROM profiles
        WHERE is_bot = 1 AND gender='male'
          AND photo_id IS NOT NULL AND photo_id != ''
        """
    )
    male_with_photo = cur.fetchone()[0]

    conn.close()

    print('VERIFY GENDER PHOTOS (DB)')
    print('Kyiv male bots with female-sourced photo_id:', kyiv_wrong)
    print('Global male bots with female-sourced photo_id:', global_wrong)
    print('Total male bots:', total_male_bots)
    print('Male bots with any photo_id:', male_with_photo)


if __name__ == '__main__':
    main()
