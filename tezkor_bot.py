import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = os.environ.get("TOKEN", "8814913893:AAG2T7ZVb93Rgu5jjqXrbM7EA9KIvlYXaGE")
ADMIN_ID = 1110117109
CARD_NUMBER = "5614 6867 0306 9024"
CARD_NAME = "Abdumalikov A"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICES = {
    "obunachi": {
        "name": "👥 Obunachi",
        "packages": [
            {"id": "ob_1k", "amount": "1 000", "price": 15000},
            {"id": "ob_3k", "amount": "3 000", "price": 45000},
            {"id": "ob_5k", "amount": "5 000", "price": 75000},
            {"id": "ob_10k", "amount": "10 000", "price": 150000},
        ]
    },
    "like": {
        "name": "❤️ Like",
        "packages": [
            {"id": "lk_1k", "amount": "1 000", "price": 5000},
            {"id": "lk_3k", "amount": "3 000", "price": 15000},
            {"id": "lk_5k", "amount": "5 000", "price": 25000},
            {"id": "lk_10k", "amount": "10 000", "price": 50000},
            {"id": "lk_20k", "amount": "20 000", "price": 100000},
        ]
    },
    "prosmotr": {
        "name": "👀 Prosmotr",
        "packages": [
            {"id": "pr_1k", "amount": "1 000", "price": 3000},
            {"id": "pr_3k", "amount": "3 000", "price": 9000},
            {"id": "pr_5k", "amount": "5 000", "price": 15000},
            {"id": "pr_10k", "amount": "10 000", "price": 25000},
        ]
    },
}

ALL_PACKAGES = {}
for svc_key, svc in SERVICES.items():
    for pkg in svc["packages"]:
        ALL_PACKAGES[pkg["id"]] = {**pkg, "service": svc_key, "service_name": svc["name"]}

user_states = {}

def fmt(p):
    return f"{p:,}".replace(",", " ")

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Obunachi", callback_data="svc_obunachi"),
         InlineKeyboardButton("❤️ Like", callback_data="svc_like")],
        [InlineKeyboardButton("👀 Prosmotr", callback_data="svc_prosmotr")],
        [InlineKeyboardButton("❓ Yordam", callback_data="help")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states.pop(user_id, None)
    text = (
        "🚀 *Tezkor SMM Xizmati*\n\n"
        "Instagram xizmatlarimiz:\n"
        "👥 Obunachi | ❤️ Like | 👀 Prosmotr\n\n"
        "✅ Tezkor • 🛡 Xavfsiz • 🔄 Kafolat\n\n"
        "Xizmat tanlang:"
    )
    await update.message.reply_text(text, reply_markup=main_kb(), parse_mode="Markdown")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "main":
        user_states.pop(user_id, None)
        await query.edit_message_text(
            "🚀 *Tezkor SMM Xizmati*\n\nXizmat tanlang:",
            reply_markup=main_kb(), parse_mode="Markdown"
        )

    elif data.startswith("svc_"):
        svc_key = data[4:]
        svc = SERVICES.get(svc_key, {})
        keyboard = []
        for pkg in svc.get("packages", []):
            keyboard.append([InlineKeyboardButton(
                f"{pkg['amount']} {svc['name'].split()[0]} — {fmt(pkg['price'])} so'm",
                callback_data=f"pkg_{pkg['id']}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="main")])
        await query.edit_message_text(
            f"*{svc['name']}*\n\nPaket tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data.startswith("pkg_"):
        pkg_id = data[4:]
        pkg = ALL_PACKAGES.get(pkg_id)
        if not pkg:
            return
        user_states[user_id] = {"step": "waiting_link", "pkg_id": pkg_id}
        svc_name = SERVICES[pkg["service"]]["name"]
        await query.edit_message_text(
            f"*{svc_name}* — {pkg['amount']}\n"
            f"💰 Narx: *{fmt(pkg['price'])} so'm*\n\n"
            f"📎 Instagram profilingiz yoki post havolasini yuboring:\n"
            f"_(Masalan: https://instagram.com/username)_",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data=f"svc_{pkg['service']}")
            ]]),
            parse_mode="Markdown"
        )

    elif data == "help":
        await query.edit_message_text(
            "❓ *Yordam*\n\n"
            "1️⃣ Xizmat tanlang\n"
            "2️⃣ Instagram havolangizni yuboring\n"
            "3️⃣ Kartaga to'lov qiling\n"
            "4️⃣ Chek rasmini yuboring\n"
            "5️⃣ Admin tasdiqlaydi ✅\n\n"
            "📞 Muammo: @alibekadmin",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="main")
            ]]),
            parse_mode="Markdown"
        )

    elif data.startswith("confirm_") or data.startswith("reject_"):
        if user_id != ADMIN_ID:
            await query.answer("Siz admin emassiz!", show_alert=True)
            return

        is_confirm = data.startswith("confirm_")
        parts = data.split("_", 2)
        client_id = int(parts[1])
        status = "✅ TASDIQLANDI" if is_confirm else "❌ RAD ETILDI"

        try:
            if query.message.photo:
                await query.edit_message_caption(
                    caption=(query.message.caption or "") + f"\n\n{status}",
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    (query.message.text or "") + f"\n\n{status}",
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Edit xato: {e}")
            await query.answer(status)

        try:
            if is_confirm:
                msg = "✅ *Buyurtmangiz tasdiqlandi!*\n\nXizmat boshlanmoqda... Tez orada bajariladi! 🚀"
            else:
                msg = "❌ *Buyurtmangiz rad etildi.*\n\nTo'lov tasdiqlanmadi. Qayta urinib ko'ring yoki @alibekadmin bilan bog'laning."
            await context.bot.send_message(client_id, msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Mijozga xabar xato: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_states.get(user_id)

    if not state or state.get("step") != "waiting_link":
        await update.message.reply_text(
            "Boshlash uchun /start bosing 👇",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Bosh menyu", callback_data="main")
            ]])
        )
        return

    link = update.message.text.strip()
    if "instagram.com" not in link and "instagr.am" not in link:
        await update.message.reply_text(
            "⚠️ *Noto'g'ri havola!*\n\n"
            "Instagram havolasi bo'lishi kerak.\n"
            "Masalan: https://instagram.com/username",
            parse_mode="Markdown"
        )
        return

    pkg_id = state["pkg_id"]
    pkg = ALL_PACKAGES[pkg_id]
    svc_name = SERVICES[pkg["service"]]["name"]
    user_states[user_id]["link"] = link
    user_states[user_id]["step"] = "waiting_payment"

    await update.message.reply_text(
        f"✅ Havola qabul qilindi!\n\n"
        f"📦 *{svc_name}* — {pkg['amount']}\n"
        f"🔗 {link}\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💳 *To'lov rekvizitlari:*\n"
        f"Karta: `{CARD_NUMBER}`\n"
        f"Egasi: *{CARD_NAME}*\n"
        f"Summa: *{fmt(pkg['price'])} so'm*\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"💸 To'lovni amalga oshirib, *chek rasmini* yuboring! 📸",
        parse_mode="Markdown"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_states.get(user_id)

    if not state or state.get("step") != "waiting_payment":
        await update.message.reply_text(
            "Boshlash uchun /start bosing 👇"
        )
        return

    pkg_id = state["pkg_id"]
    pkg = ALL_PACKAGES[pkg_id]
    svc_name = SERVICES[pkg["service"]]["name"]
    link = state.get("link", "—")
    user = update.effective_user
    username = f"@{user.username}" if user.username else "username yo'q"

    admin_caption = (
        f"🔔 *YANGI BUYURTMA!*\n\n"
        f"👤 {user.full_name}\n"
        f"📱 {username}\n"
        f"🆔 `{user_id}`\n\n"
        f"📦 *{svc_name}* — {pkg['amount']}\n"
        f"🔗 {link}\n"
        f"💰 *{fmt(pkg['price'])} so'm*"
    )

    admin_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_{user_id}_ok"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{user_id}_no"),
    ]])

    photo = update.message.photo[-1].file_id

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo,
            caption=admin_caption,
            reply_markup=admin_kb,
            parse_mode="Markdown"
        )
        logger.info(f"Admin ga yuborildi: user {user_id}")
    except Exception as e:
        logger.error(f"Admin ga yuborishda XATO: {e}")

    user_states.pop(user_id, None)
    await update.message.reply_text(
        "✅ *Chek qabul qilindi!*\n\n"
        "Admin to'lovni tekshirmoqda.\n"
        "5-15 daqiqa ichida xabar beriladi! ⏳",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Bosh menyu", callback_data="main")
        ]])
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    logger.info("Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)
