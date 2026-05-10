import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

download_stats = {"total": 0}
user_langs = {}
pending = {}
all_users = set()

SUPPORTED = ["instagram.com", "tiktok.com", "pinterest.com", "pin.it"]

WELCOME = {
    "en": (
        "👋 Welcome to Media Downloader Bot!\n\n"
        "📥 Supported platforms:\n"
        "• Instagram (Posts, Reels, Stories)\n"
        "• TikTok\n"
        "• Pinterest\n\n"
        "📌 How to use:\n"
        "1. Copy any video link\n"
        "2. Paste it here\n"
        "3. Choose Video or Document\n"
        "4. Done! ✅\n\n"
        "🌐 Change language: /lang"
    ),
    "ru": (
        "👋 Добро пожаловать в бот для скачивания медиа!\n\n"
        "📥 Поддерживаемые платформы:\n"
        "• Instagram (Посты, Рилс, Истории)\n"
        "• TikTok\n"
        "• Pinterest\n\n"
        "📌 Как использовать:\n"
        "1. Скопируйте ссылку на видео\n"
        "2. Вставьте её сюда\n"
        "3. Выберите Видео или Документ\n"
        "4. Готово! ✅\n\n"
        "🌐 Сменить язык: /lang"
    ),
    "uz": (
        "👋 Media Yuklovchi Botga Xush Kelibsiz!\n\n"
        "📥 Qo'llab-quvvatlanadigan platformalar:\n"
        "• Instagram (Postlar, Reels, Storylar)\n"
        "• TikTok\n"
        "• Pinterest\n\n"
        "📌 Qanday foydalanish:\n"
        "1. Video havolasini nusxalang\n"
        "2. Bu yerga joylashtiring\n"
        "3. Video yoki Hujjat tanlang\n"
        "4. Tayyor! ✅\n\n"
        "🌐 Tilni o'zgartirish: /lang"
    ),
}

MSGS = {
    "en": {
        "downloading": "⏳ Downloading...",
        "uploading": "📤 Uploading...",
        "choose": "📎 How do you want to receive it?",
        "as_video": "🎬 As Video",
        "as_doc": "📄 As Document",
        "invalid": "❌ Please send a valid link from Instagram, TikTok or Pinterest.",
        "failed": "❌ Download failed.\n\nReason: ",
        "choose_lang": "🌐 Choose your language:",
        "lang_set": "✅ Language set!",
        "broadcast_msg": "🔄 Bot has been updated!\n\nPlease press /start to use the latest version ✅",
        "broadcast_done": "📢 Broadcast done!\n✅ Sent: {s}\n❌ Failed: {f}",
        "admin_only": "⛔ Admin only.",
        "stats": "📊 Total downloads: {n}",
        "expired": "❌ Session expired. Please send the link again.",
    },
    "ru": {
        "downloading": "⏳ Скачивание...",
        "uploading": "📤 Загрузка...",
        "choose": "📎 Как вы хотите получить файл?",
        "as_video": "🎬 Как Видео",
        "as_doc": "📄 Как Документ",
        "invalid": "❌ Пожалуйста, отправьте ссылку с Instagram, TikTok или Pinterest.",
        "failed": "❌ Ошибка загрузки.\n\nПричина: ",
        "choose_lang": "🌐 Выберите язык:",
        "lang_set": "✅ Язык установлен!",
        "broadcast_msg": "🔄 Бот обновлён!\n\nНажмите /start для использования новой версии ✅",
        "broadcast_done": "📢 Рассылка завершена!\n✅ Отправлено: {s}\n❌ Ошибок: {f}",
        "admin_only": "⛔ Только для администратора.",
        "stats": "📊 Всего загрузок: {n}",
        "expired": "❌ Сессия истекла. Отправьте ссылку снова.",
    },
    "uz": {
        "downloading": "⏳ Yuklanmoqda...",
        "uploading": "📤 Yuborilmoqda...",
        "choose": "📎 Qanday qabul qilmoqchisiz?",
        "as_video": "🎬 Video sifatida",
        "as_doc": "📄 Hujjat sifatida",
        "invalid": "❌ Iltimos, Instagram, TikTok yoki Pinterest havolasini yuboring.",
        "failed": "❌ Yuklash muvaffaqiyatsiz.\n\nSabab: ",
        "choose_lang": "🌐 Tilni tanlang:",
        "lang_set": "✅ Til o'rnatildi!",
        "broadcast_msg": "🔄 Bot yangilandi!\n\nEng yangi versiyadan foydalanish uchun /start bosing ✅",
        "broadcast_done": "📢 Xabar yuborildi!\n✅ Yuborildi: {s}\n❌ Xato: {f}",
        "admin_only": "⛔ Faqat admin uchun.",
        "stats": "📊 Jami yuklamalar: {n}",
        "expired": "❌ Sessiya tugadi. Havolani qayta yuboring.",
    },
}

def get_lang(user_id):
    return user_langs.get(user_id, "en")

def m(user_id, key):
    return MSGS[get_lang(user_id)][key]

async def set_commands(app):
    user_commands = [
        BotCommand("start", "🚀 Start the bot"),
        BotCommand("lang", "🌐 Change language"),
    ]
    admin_commands = [
        BotCommand("start", "🚀 Start the bot"),
        BotCommand("lang", "🌐 Change language"),
        BotCommand("stats", "📊 Download statistics"),
        BotCommand("broadcast", "📢 Notify all users"),
    ]
    await app.bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
    if ADMIN_ID:
        await app.bot.set_my_commands(
            admin_commands,
            scope=BotCommandScopeChat(chat_id=int(ADMIN_ID))
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    all_users.add(uid)
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
    if not ADMIN_ID or str(uid) != str(ADMIN_ID):
        await update.message.reply_text(m(uid, "admin_only"))
        return
    await update.message.reply_text(m(uid, "stats").format(n=download_stats["total"]))

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not ADMIN_ID or str(uid) != str(ADMIN_ID):
        await update.message.reply_text(m(uid, "admin_only"))
        return
    success = 0
    failed = 0
    for user_id in all_users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=m(user_id, "broadcast_msg")
            )
            success += 1
        except:
            failed += 1
    await update.message.reply_text(
        m(uid, "broadcast_done").format(s=success, f=failed)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    if query.data.startswith("lang_"):
        lang = query.data.split("_")[1]
        user_langs[uid] = lang
        await query.edit_message_text(MSGS[lang]["lang_set"])
        return

    if query.data.startswith("dl_"):
        mode = query.data.split("_")[1]
        url = pending.get(uid)

        if not url:
            await query.edit_message_text(m(uid, "expired"))
            return

        msg = await query.edit_message_text(m(uid, "downloading"))

        try:
            os.makedirs("downloads", exist_ok=True)

            ydl_opts = {
                "outtmpl": f"downloads/{uid}_%(id)s.%(ext)s",
                "quiet": True,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 Chrome/96.0.4664.45 Mobile Safari/537.36"
                },
            }

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
    all_users.add(uid)

    keyboard = [[
        InlineKeyboardButton(m(uid, "as_video"), callback_data="dl_video"),
        InlineKeyboardButton(m(uid, "as_doc"), callback_data="dl_doc"),
    ]]
    await update.message.reply_text(
        m(uid, "choose"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def on_startup(app):
    await set_commands(app)

app = ApplicationBuilder().token(TOKEN).post_init(on_startup).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("lang", lang_command))
app.add_handler(CommandHandler("stats", stats_command))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
app.run_polling()