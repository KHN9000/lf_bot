# lf_bot

Telegram-бот для аналитики канала `@bed_for_cat`.  
Пишет отчёты о просмотрах, длине постов, эмодзи, ссылках и самых частых словах.

## 🔧 Установка

```bash
pip install -r requirements.txt
```

## 🚀 Запуск

```bash
export BOT_TOKEN=your_telegram_bot_token
export ADMIN_USER_ID=your_telegram_user_id
python bot.py
```

## ⚙️ Переменные окружения

- `BOT_TOKEN` — токен Telegram-бота
- `ADMIN_USER_ID` — твой Telegram ID (чтобы получать отчёты в личку)
