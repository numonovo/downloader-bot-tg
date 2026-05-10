import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")  # your telegram user ID

# Stats counter
download_stats = {"total": 0}

# Supported platforms
SUPPORTED = ["instagram.com", "tiktok.com", "youtube.com", "youtu.be", "facebook.com", "fb.watch", "pinterest.com", "pin.it"]

WELCOME = {
    "en": (
        "👋 Welcome to Media Downloader Bot!\n\n"
        "📥 Supported platforms:\n"
        "• Instagram (Posts, Reels, Stories)\n"
        "• TikTok\n"
        "• YouTube & Shorts\n"
        "• Facebook\n"
        "• Pinterest\n\n"
        "📌 How to use:\n"
        "1. Copy any video link\n"
        "2. Paste it here\n"
        "3. Choose Video or Document\n"
        "4. Done! ✅\n\n"
        "🌐 Language: /lang"
    ),
    "ru": (
        "👋 Добро пожаловать в бот для скачивания медиа!\n\n"
        "📥 Поддерживаемые платформы:\n"
        "• Instagram (Посты, Рилс, Истории)\n"
        "• TikTok\n"
        "• YouTube и Shorts\n"
        "• Facebook\n"
        "• Pinterest\n\n"
        "📌 Как использовать:\n"
        "1. Скопируйте ссылку на видео\n"
        "2. Вставьте её сюда\n"
        "3. Выберите Видео или Документ\n"
        "4. Готово! ✅\n\n"
        "🌐 Язык: /lang"
    ),
    "uz": (
        "👋 Media Yuklovchi Botga Xush Kelibsiz!\n\n"
        "📥 Qo'llab-quvvatlanadigan platformalar:\n"
        "• Instagram (Postlar, Reels, Storylar)\n"
        "• TikTok\n"
        "• YouTube va Shorts\n"
        "• Facebook\n"
        "• Pinterest\n\n"
        "📌 Qanday foydalanish:\n"
        "1. Video havolasini nusxalang\n"
        "2. Bu yerga joylashtiring\n"
        "3. Video yoki Hujjat tanlang\n"
        "4. Tayyor! ✅\n\n"
        "🌐 Til: /lang"
    ),
}

MSGS = {
    "en": {
        "downloading": "⏳ Downloading... 0%",
        "uploading": "📤 Uploading...",
        "choose": "📎 How do you want to receive it?",
        "as_video": "🎬 As Video",
        "as_doc": "📄 As Document",
        "invalid": "❌ Please send a valid link from Instagram, TikTok, YouTube, Facebook or Pinterest.",
        "failed": "❌ Download failed.\n\nReason: ",
        "choose_lang": "🌐 Choose your language:",
        "lang_set": "✅ Language set!",
    },
    "ru": {
        "downloading": "⏳ Скачивание... 0%",
        "uploading": "📤 Загрузка...",
        "choose": "📎 Как вы хотите получить файл?",
        "as_video": "🎬 Как Видео",
        "as_doc": "📄 Как Документ",
        "invalid": "❌ Пожалуйста, отправьте ссылку с Instagram, TikTok, YouTube, Facebook или Pinterest.",
        "failed": "❌ Ошибка загрузки.\n\nПричина: ",
        "choose_lang": "🌐 Выберите язык:",
        "lang_set": "✅ Язык установлен!",
    },
    "uz": {
        "downloading": "⏳ Yuklanmoqda... 0%",
        "uploading": "📤 Yuborilmoqda...",
        "choose": "📎 Qanday qabul qilmoqchisiz?",
        "as_video": "🎬 Video sifatida",
        "as_doc": "📄 Hujjat sifatida",
        "invalid": "❌ Iltimos, Instagram, TikTok, YouTube, Facebook yoki Pinterest havolasini yuboring.",
        "failed": "❌ Yuklash muvaffaqiyatsiz.\n\nSabab: ",
        "choose_lang": "🌐 Tilni tanlang:",
        "lang_set": "✅ Til o'rnatildi!",
    },
}

# Store user languages and pending downloads
user_langs = {}
pending = {}

def get_lang(user_id):
    return user_langs.get(user_id, "en")

def m(user_id, key):
    return MSGS[get_lang(user_id)][key]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    await update.message.reply_text(WELCOME[lang])

async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz")],
    ]
    await update.message.reply_text(
        m(uid, "choose_lang"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if ADMIN_ID and str(uid) == str(ADMIN_ID):
        await update.message.reply_text(f"📊 Total downloads: {download_stats['total']}")
    else:
        await update.message.reply_text("⛔ Admin only command.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    # Language selection
    if query.data.startswith("lang_"):
        lang = query.data.split("_")[1]
        user_langs[uid] = lang
        await query.edit_message_text(MSGS[lang]["lang_set"])
        return

    # Video or Document choice
    if query.data.startswith("dl_"):
        parts = query.data.split("_", 2)
        mode = parts[1]  # video or doc
        url = pending.get(uid)

        if not url:
            await query.edit_message_text("❌ Session expired. Please send the link again.")
            return

        msg = await query.edit_message_text(m(uid, "downloading"))

        try:
            os.makedirs("downloads", exist_ok=True)

            ydl_opts = {
                "outtmpl": f"downloads/{uid}_%(id)s.%(ext)s",
                "quiet": True,
                "progress_hooks": [lambda d: None],
            }

            # Progress updater
            last = [0]
            async def update_progress(d):
                if d["status"] == "downloading":
                    pct = d.get("_percent_str", "...").strip()
                    if pct != last[0]:
                        last[0] = pct
                        try:
                            await msg.edit_text(f"⏳ Downloading... {pct}")
                        except:
                            pass

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

            await msg.edit_text(m(uid, "uploading"))

            with open(file_path, "rb") as f:
                if mode == "doc":
                    await query.message.reply_document(document=f)
                else:
                    await query.message.reply_video(video=f)

            os.remove(file_path)
            download_stats["total"] += 1
            await msg.delete()

        except Exception as e:
            await msg.edit_text(m(uid, "failed") + str(e))

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    url = update.message.text.strip()

    if not any(domain in url for domain in SUPPORTED):
        await update.message.reply_text(m(uid, "invalid"))
        return

    pending[uid] = url

    keyboard = [[
        InlineKeyboardButton(m(uid, "as_video"), callback_data="dl_video"),
        InlineKeyboardButton(m(uid, "as_doc"), callback_data="dl_doc"),
    ]]
    await update.message.reply_text(
        m(uid, "choose"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("lang", lang_command))
app.add_handler(CommandHandler("stats", stats_command))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
app.run_polling()