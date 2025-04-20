import asyncio
import logging
import re
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.markdown import hbold
import os

API_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@bed_for_cat"
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

POST_HISTORY = {}

def analyze_text(text):
    emoji_count = len(re.findall(r"[\U00010000-\U0010ffff]", text))
    link_count = len(re.findall(r"https?://\S+", text))
    word_count = len(text.split())
    hashtag_count = len(re.findall(r"#\w+", text))
    return {
        "length": len(text),
        "words": word_count,
        "emojis": emoji_count,
        "links": link_count,
        "hashtags": hashtag_count,
    }

async def fetch_recent_posts():
    recent_stats = []
    async for message in bot.get_chat_history(CHANNEL_USERNAME, limit=100):
        if message.date < datetime.utcnow() - timedelta(days=1):
            break
        if message.message_id in POST_HISTORY:
            continue
        if not message.text:
            continue

        stats = analyze_text(message.text)
        stats["views"] = message.views or 0
        stats["date"] = message.date.strftime("%Y-%m-%d %H:%M")
        stats["id"] = message.message_id
        stats["text"] = message.text
        POST_HISTORY[message.message_id] = stats
        recent_stats.append(stats)
    return recent_stats

def build_report(posts):
    if not posts:
        return "За последние сутки новых постов не было."

    total_views = sum(p["views"] for p in posts)
    avg_length = sum(p["length"] for p in posts) / len(posts)
    avg_words = sum(p["words"] for p in posts) / len(posts)
    total_emojis = sum(p["emojis"] for p in posts)
    total_links = sum(p["links"] for p in posts)

    most_common_words = {}
    for p in posts:
        words = [w.lower() for w in re.findall(r"\b\w{4,}\b", p["text"])]
        for w in words:
            most_common_words[w] = most_common_words.get(w, 0) + 1
    sorted_words = sorted(most_common_words.items(), key=lambda x: x[1], reverse=True)[:10]
    top_words = ", ".join(f"{w} ({c})" for w, c in sorted_words)

    return (
        f"<b>📊 Отчёт за сутки — {len(posts)} пост(ов)</b>\n"
        f"{hbold('👁 Всего просмотров')}: {total_views}\n"
        f"{hbold('✍️ Средняя длина текста')}: {avg_length:.0f} символов / {avg_words:.0f} слов\n"
        f"{hbold('😊 Эмодзи всего')}: {total_emojis}\n"
        f"{hbold('🔗 Ссылок всего')}: {total_links}\n"
        f"{hbold('💬 Частые слова')}: {top_words}"
    )

@dp.message(F.text == "/analyze")
async def manual_report(message: Message):
    if message.from_user.id != ADMIN_USER_ID:
        return await message.answer("Нет доступа.")
    posts = await fetch_recent_posts()
    report = build_report(posts)
    await message.answer(report)

async def scheduled_report():
    while True:
        now = datetime.now()
        target = now.replace(hour=10, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        wait_time = (target - now).total_seconds()
        await asyncio.sleep(wait_time)

        posts = await fetch_recent_posts()
        report = build_report(posts)
        await bot.send_message(chat_id=ADMIN_USER_ID, text=report)

async def main():
    logging.basicConfig(level=logging.INFO)
    asyncio.create_task(scheduled_report())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
