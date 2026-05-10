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
new_users = set()

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
        "3. Get your video + find the music! 🎵\n\n"
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
        "3. Получите видео + найдите музыку! 🎵\n\n"
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
        "3. Videoni oling + musiqa toping! 🎵\n\n"
        "🌐 Tilni o'zgartirish: /lang"
    ),
}

MSGS = {
    "en": {
        "choose_lang_first": "👋 Hello! Please choose your language first:",
        "downloading": "⏳ Downloading...",
        "uploading": "📤 Uploading...",
        "extracting_audio": "🎵 Extracting audio...",
        "invalid": "❌ Please send a valid link from Instagram, TikTok or Pinterest.",
        "failed": "❌ Download failed.\n\nReason: ",
        "choose_lang": "🌐 Choose your language:",
        "lang_set": "✅ Language set!",
        "broadcast_msg": "🔄 Bot has been updated!\n\nPlease press /start to use the latest version ✅",
        "broadcast_done": "📢 Broadcast done!\n✅ Sent: {s}\n❌ Failed: {f}",
        "admin_only": "⛔ Admin only.",
        "stats": "📊 Total downloads: {n}",
        "expired": "❌ Session expired. Please send the link again.",
        "music_options": "🎵 What do you want to do with the music?",
        "get_audio": "🎵 Extract Audio",
        "find_shazam": "🔍 Find on Shazam",
        "find_spotify": "🎧 Find on Spotify",
        "audio_sending": "🎵 Sending audio file...",
        "audio_failed": "❌ Could not extract audio.",
        "shazam_link": "🔍 Try to find the song on Shazam:",
        "spotify_link": "🎧 Search the song on Spotify:",
    },
    "ru": {
        "choose_lang_first": "👋 Привет! Сначала выберите язык:",
        "downloading": "⏳ Скачивание...",
        "uploading": "📤 Загрузка...",
        "extracting_audio": "🎵 Извлечение аудио...",
        "invalid": "❌ Пожалуйста, отправьте ссылку с Instagram, TikTok или Pinterest.",
        "failed": "❌ Ошибка загрузки.\n\nПричина: ",
        "choose_lang": "🌐 Выберите язык:",
        "lang_set": "✅ Язык установлен!",
        "broadcast_msg": "🔄 Бот обновлён!\n\nНажмите /start для использования новой версии ✅",
        "broadcast_done": "📢 Рассылка завершена!\n✅ Отправлено: {s}\n❌ Ошибок: {f}",
        "admin_only": "⛔ Только для администратора.",
        "stats": "📊 Всего загрузок: {n}",
        "expired": "❌ Сессия истекла. Отправьте ссылку снова.",
        "music_options": "🎵 Что сделать с музыкой?",
        "get_audio": "🎵 Извлечь аудио",
        "find_shazam": "🔍 Найти в Shazam",
        "find_spotify": "🎧 Найти в Spotify",
        "audio_sending": "🎵 Отправка аудио файла...",
        "audio_failed": "❌ Не удалось извлечь аудио.",
        "shazam_link": "🔍 Попробуйте найти песню в Shazam:",
        "spotify_link": "🎧 Найдите песню в Spotify:",
    },
    "uz": {
        "choose_lang_first": "👋 Salom! Avval tilni tanlang:",
        "downloading": "⏳ Yuklanmoqda...",
        "uploading": "📤 Yuborilmoqda...",
        "extracting_audio": "🎵 Audio ajratilmoqda...",
        "invalid": "❌ Iltimos, Instagram, TikTok yoki Pinterest havolasini yuboring.",
        "failed": "❌ Yuklash muvaffaqiyatsiz.\n\nSabab: ",
        "choose_lang": "🌐 Tilni tanlang:",
        "lang_set": "✅ Til o'rnatildi!",
        "broadcast_msg": "🔄 Bot yangilandi!\n\nEng yangi versiyadan foydalanish uchun /start bosing ✅",
        "broadcast_done": "📢 Xabar yuborildi!\n✅ Yuborildi: {s}\n❌ Xato: {f}",
        "admin_only": "⛔ Faqat admin uchun.",
        "stats": "📊 Jami yuklamalar: {n}",
        "expired": "❌ Sessiya tugadi. Havolani qayta yuboring.",
        "music_options": "🎵 Musiqa bilan nima qilmoqchisiz?",
        "get_audio": "🎵 Audioni ajratib olish",
        "find_shazam": "🔍 Shazamda topish",
        "find_spotify": "🎧 Spotifyda topish",
        "audio_sending": "🎵 Audio fayl yuborilmoqda...",
        "audio_failed": "❌ Audioni ajratib bo'lmadi.",
        "shazam_link": "🔍 Shazamda qo'shiqni toping:",
        "spotify_link": "🎧 Spotifyda qo'shiqni toping:",
    },
}

def get_lang(user_id):
    return user_langs.get(user_id, None)

def m(user_id, key):
    lang = get_lang(user_id) or "en"
    return MSGS[lang][key]

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
    await app.bot.set_my_commands(
        user_commands,
        scope=BotCommandScopeDefault()
    )
    if ADMIN_ID:
        await app.bot.set_my_commands(
            admin_commands,
            scope=BotCommandScopeChat(chat_id=int(ADMIN_ID))
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    all_users.add(uid)

    # If new user, ask language first
    if uid not in user_langs:
        new_users.add(uid)
        keyboard = [
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz")],
        ]
        await update.message.reply_text(
            "👋 Hello! / Привет! / Salom!\n\nPlease choose your language:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await update.message.reply_text(WELCOME[get_lang(uid)])

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
    await update.message.reply_text(
        m(uid, "stats").format(n=download_stats["total"])
    )

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

    # Language selection
    if query.data.startswith("lang_"):
        lang = query.data.split("_")[1]
        user_langs[uid] = lang
        all_users.add(uid)
        # If new user, show welcome after language set
        if uid in new_users:
            new_users.discard(uid)
            await query.edit_message_text(WELCOME[lang])
        else:
            await query.edit_message_text(MSGS[lang]["lang_set"])
        return

    # Download video
    if query.data == "dl_video":
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
                title = info.get("title", "")

            await msg.edit_text(m(uid, "uploading"))

            with open(file_path, "rb") as f:
                await query.message.reply_video(video=f)

            os.remove(file_path)
            download_stats["total"] += 1
            await msg.delete()

            # Show music options after video
            keyboard = [[
                InlineKeyboardButton(
                    m(uid, "get_audio"), callback_data="music_audio"
                ),
            ],[
                InlineKeyboardButton(
                    m(uid, "find_shazam"), callback_data="music_shazam"
                ),
                InlineKeyboardButton(
                    m(uid, "find_spotify"), callback_data="music_spotify"
                ),
            ]]
            await query.message.reply_text(
                m(uid, "music_options"),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await msg.edit_text(m(uid, "failed") + str(e))

    # Extract audio
    if query.data == "music_audio":
        url = pending.get(uid)
        if not url:
            await query.edit_message_text(m(uid, "expired"))
            return

        msg = await query.edit_message_text(m(uid, "extracting_audio"))

        try:
            os.makedirs("downloads", exist_ok=True)

            ydl_opts = {
                "outtmpl": f"downloads/{uid}_audio_%(id)s.%(ext)s",
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "quiet": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                audio_path = f"downloads/{uid}_audio_{info['id']}.mp3"

            await msg.edit_text(m(uid, "audio_sending"))

            with open(audio_path, "rb") as f:
                await query.message.reply_audio(audio=f)

            os.remove(audio_path)
            await msg.delete()

        except Exception as e:
            await msg.edit_text(m(uid, "audio_failed"))

    # Shazam link
    if query.data == "music_shazam":
        await query.edit_message_text(
            m(uid, "shazam_link") +
            "\nhttps://shazam.com"
        )

    # Spotify link
    if query.data == "music_spotify":
        url = pending.get(uid)
        title = ""
        if url:
            try:
                with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get("title", "")
            except:
                pass
        search_query = title.replace(" ", "+") if title else ""
        spotify_url = f"https://open.spotify.com/search/{search_query}"
        await query.edit_message_text(
            m(uid, "spotify_link") +
            f"\n{spotify_url}"
        )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    # Block if language not set yet
    if uid not in user_langs:
        keyboard = [
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz")],
        ]
        await update.message.reply_text(
            "👋 Hello! / Привет! / Salom!\n\nPlease choose your language first:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    url = update.message.text.strip()

    if not any(domain in url for domain in SUPPORTED):
        await update.message.reply_text(m(uid, "invalid"))
        return

    pending[uid] = url
    all_users.add(uid)

    keyboard = [[
        InlineKeyboardButton("⬇️ Download Video", callback_data="dl_video"),
    ]]
    await update.message.reply_text(
        "⬇️ Ready to download!",
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