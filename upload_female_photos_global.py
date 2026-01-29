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


def get_asset_paths(folder: str) -> list[str]:
    paths: list[str] = []
    if not os.path.isdir(folder):
        return paths
    for fn in os.listdir(folder):
        if fn.lower().endswith((".jpg", ".jpeg", ".png")):
            paths.append(os.path.join(folder, fn))
    return sorted(paths)


async def main():
    token = get_bot_token()
    if not token:
        raise RuntimeError("BOT_TOKEN not found in bot.env")

    target_chat_id = 5483644714

    assets_dir = os.path.join(os.path.dirname(__file__), "assets", "bots", "female")
    image_paths = get_asset_paths(assets_dir)
    if not image_paths:
        print(f"No female images found in {assets_dir}")
        return

    image_paths = image_paths[:100]

    conn = sqlite3.connect("drink_bot.db")
    cursor = conn.cursor()

    # female bots that need fixing: no photo OR photo_id matches any male profile photo_id
    cursor.execute(
        """
        SELECT DISTINCT f.user_id
        FROM profiles f
        LEFT JOIN profiles m
          ON f.photo_id = m.photo_id AND m.gender = 'male'
        WHERE f.is_bot = 1
          AND f.gender = 'female'
          AND (
            f.photo_id IS NULL OR f.photo_id = '' OR m.user_id IS NOT NULL
          )
        ORDER BY f.user_id
        """
    )
    female_bot_ids = [r[0] for r in cursor.fetchall()]

    print(f"Female bots to fix: {len(female_bot_ids)}")
    if not female_bot_ids:
        conn.close()
        return

    bot = Bot(token=token)
    try:
        print(f"Uploading {len(image_paths)} female photos to get file_ids...")
        file_ids: list[str] = []
        for path in image_paths:
            msg = await bot.send_photo(chat_id=target_chat_id, photo=FSInputFile(path))
            file_ids.append(msg.photo[-1].file_id)
            await bot.delete_message(chat_id=target_chat_id, message_id=msg.message_id)

        print("Assigning female file_ids to female bots (cycled)...")
        for i, bot_id in enumerate(female_bot_ids):
            file_id = file_ids[i % len(file_ids)]
            cursor.execute(
                "UPDATE profiles SET photo_id = ?, bot_photo_path = ? WHERE user_id = ?",
                (file_id, "assets/bots/female", bot_id),
            )

        conn.commit()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM profiles f
            JOIN profiles m
              ON f.photo_id = m.photo_id AND m.gender='male'
            WHERE f.is_bot=1 AND f.gender='female' AND f.photo_id IS NOT NULL AND f.photo_id != ''
            """
        )
        wrong = cursor.fetchone()[0]
        print(f"Female bots with male-matching photo_id AFTER fix: {wrong}")

    finally:
        await bot.session.close()
        conn.close()


if __name__ == "__main__":
    asyncio.run(main())
