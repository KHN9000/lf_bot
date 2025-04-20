import os
import re
import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

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
        "<b>📊 Отчёт за сутки — {count} пост(ов)</b>\n"
        "👁 Всего просмотров: {views}\n"
        "✍️ Средняя длина текста: {length:.0f} символов / {words:.0f} слов\n"
        "😊 Эмодзи всего: {emojis}\n"
        "🔗 Ссылок всего: {links}\n"
        "💬 Частые слова: {top}"
    ).format(
        count=len(posts),
        views=total_views,
        length=avg_length,
        words=avg_words,
        emojis=total_emojis,
        links=total_links,
        top=top_words
    )

@dp.message(F.text == "/analyze")
async def manual_report(message: Message):
    if message.from_user.id != ADMIN_USER_ID:
        return await message.answer("Нет доступа.")
    posts = await fetch_recent_posts()
    report = build_report(posts)
    await message.answer(report)

async def on_startup(_: web.Application):
    await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")

async def on_shutdown(_: web.Application):
    await bot.delete_webhook()

async def main():
    logging.basicConfig(level=logging.INFO)
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app

if __name__ == '__main__':
    web.run_app(main(), host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
