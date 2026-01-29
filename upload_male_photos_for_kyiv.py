import os
import sqlite3
import asyncio

from aiogram import Bot
from aiogram.types import FSInputFile


def get_bot_token() -> str | None:
    env_path = os.path.join(os.path.dirname(__file__), "bot.env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("BOT_TOKEN="):
                    return line.split("=", 1)[1].strip()
    return None


async def main():
    token = get_bot_token()
    if not token:
        raise RuntimeError("BOT_TOKEN not found in bot.env")

    # куда бот будет отправлять фото, чтобы получить file_id
    target_chat_id = 5483644714

    city = "Kyiv"
    assets_dir = os.path.join(os.path.dirname(__file__), "assets", "bots", "male")

    conn = sqlite3.connect("drink_bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user_id
        FROM profiles
        WHERE is_bot = 1
          AND city_normalized = ?
          AND gender = 'male'
        ORDER BY user_id
        """,
        (city,),
    )
    male_bot_ids = [r[0] for r in cursor.fetchall()]

    if not male_bot_ids:
        print("No male bots in Kyiv")
        conn.close()
        return

    if not os.path.isdir(assets_dir):
        print(f"Male assets dir not found: {assets_dir}")
        conn.close()
        return

    image_paths = []
    for fn in os.listdir(assets_dir):
        if fn.lower().endswith((".jpg", ".jpeg", ".png")):
            image_paths.append(os.path.join(assets_dir, fn))

    if not image_paths:
        print("No male images found in assets/bots/male")
        conn.close()
        return

    # ограничим количеством ботов в Киеве
    image_paths = image_paths[: len(male_bot_ids)]

    bot = Bot(token=token)

    try:
        uploaded_file_ids: list[str] = []

        print(f"Uploading {len(image_paths)} male photos to get file_ids...")
        for path in image_paths:
            msg = await bot.send_photo(
                chat_id=target_chat_id,
                photo=FSInputFile(path),
            )
            file_id = msg.photo[-1].file_id
            uploaded_file_ids.append(file_id)
            # чистим чат
            await bot.delete_message(chat_id=target_chat_id, message_id=msg.message_id)

        print("Assigning uploaded male file_ids to Kyiv male bots...")
        for bot_id, file_id in zip(male_bot_ids, uploaded_file_ids, strict=False):
            cursor.execute(
                "UPDATE profiles SET photo_id = ?, bot_photo_path = ? WHERE user_id = ?",
                (file_id, "assets/bots/male", bot_id),
            )

        conn.commit()

        # проверка: есть ли male боты с photo_id, которое принадлежит female боту
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM profiles m
            JOIN profiles f ON m.photo_id = f.photo_id
            WHERE m.is_bot = 1
              AND m.city_normalized = ?
              AND m.gender = 'male'
              AND f.is_bot = 1
              AND f.gender = 'female'
            """,
            (city,),
        )
        wrong = cursor.fetchone()[0]
        print(f"Kyiv male bots with female-sourced photo_id (by join): {wrong}")

        print("Done")

    finally:
        await bot.session.close()
        conn.close()


if __name__ == "__main__":
    asyncio.run(main())
