import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler

TOKEN = os.environ.get("TOKEN", "8814913893:AAG2T7ZVb93Rgu5jjqXrbM7EA9KIvlYXaGE")
ADMIN_ID = 1110117109
CARD_NUMBER = "5614 6867 0306 9024"
CARD_NAME = "Abdumalikov A"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ===== XIZMATLAR =====
SERVICES = {
    "obunachi": {
        "name": "👥 Obunachi",
        "emoji": "👥",
        "packages": [
            {"id": "ob_1k", "amount": "1 000", "price": 15000, "min_link": True},
            {"id": "ob_3k", "amount": "3 000", "price": 45000, "min_link": True},
            {"id": "ob_5k", "amount": "5 000", "price": 75000, "min_link": True},
            {"id": "ob_10k", "amount": "10 000", "price": 150000, "min_link": True},
        ]
    },
    "like": {
        "name": "❤️ Like",
        "emoji": "❤️",
        "packages": [
            {"id": "lk_1k", "amount": "1 000", "price": 5000, "min_link": True},
            {"id": "lk_3k", "amount": "3 000", "price": 15000, "min_link": True},
            {"id": "lk_5k", "amount": "5 000", "price": 25000, "min_link": True},
            {"id": "lk_10k", "amount": "10 000", "price": 50000, "min_link": True},
            {"id": "lk_20k", "amount": "20 000", "price": 100000, "min_link": True},
        ]
    },
    "prosmotr": {
        "name": "👀 Prosmotr",
        "emoji": "👀",
        "packages": [
            {"id": "pr_1k", "amount": "1 000", "price": 3000, "min_link": True},
            {"id": "pr_3k", "amount": "3 000", "price": 9000, "min_link": True},
            {"id": "pr_5k", "amount": "5 000", "price": 15000, "min_link": True},
            {"id": "pr_10k", "amount": "10 000", "price": 25000, "min_link": True},
        ]
    },
}

# Barcha paketlar
ALL_PACKAGES = {}
for svc_key, svc in SERVICES.items():
    for pkg in svc["packages"]:
        ALL_PACKAGES[pkg["id"]] = {**pkg, "service": svc_key, "service_name": svc["name"]}

# Foydalanuvchi holatlari
user_states = {}  # {user_id: {"step": ..., "package_id": ..., "link": ..., "receipt": ...}}

def fmt(p):
    return f"{p:,}".replace(",", " ")

# ===== KLAVIATURALAR =====
def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Obunachi", callback_data="svc_obunachi"),
         InlineKeyboardButton("❤️ Like", callback_data="svc_like")],
        [InlineKeyboardButton("👀 Prosmotr", callback_data="svc_prosmotr")],
        [InlineKeyboardButton("📋 Mening buyurtmalarim", callback_data="my_orders")],
        [InlineKeyboardButton("❓ Yordam", callback_data="help")],
    ])

def packages_keyboard(svc_key):
    svc = SERVICES[svc_key]
    keyboard = []
    for pkg in svc["packages"]:
        keyboard.append([InlineKeyboardButton(
            f"{pkg['amount']} {svc['emoji']} — {fmt(pkg['price'])} so'm",
            callback_data=f"pkg_{pkg['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="main")])
    return InlineKeyboardMarkup(keyboard)

def back_keyboard(to="main"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=to)]])

# ===== HANDLERS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states.pop(user_id, None)

    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "👨‍💼 *ADMIN PANEL*\n\n"
            "Siz admin sifatida kirgansiz.\n"
            "Buyurtmalar sizga avtomatik keladi.\n\n"
            "Mijoz sifatida ko'rish uchun /menu buyrug'ini bosing.",
            parse_mode="Markdown"
        )
        return

    text = (
        "🚀 *Tezkor Obuna Bot*\n\n"
        "Instagram xizmatlarimiz:\n"
        "👥 Obunachi\n"
        "❤️ Like\n"
        "👀 Prosmotr\n\n"
        "✅ Tezkor yetkazib berish\n"
        "🛡 Xavfsiz to'lov\n"
        "🔄 1 yil kafolat\n\n"
        "Quyidagi xizmatlardan birini tanlang:"
    )
    await update.message.reply_text(text, reply_markup=main_keyboard(), parse_mode="Markdown")

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states.pop(user_id, None)
    text = "🚀 *Tezkor Obuna Bot*\n\nXizmat tanlang:"
    await update.message.reply_text(text, reply_markup=main_keyboard(), parse_mode="Markdown")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "main":
        user_states.pop(user_id, None)
        await query.edit_message_text(
            "🚀 *Tezkor Obuna Bot*\n\nXizmat tanlang:",
            reply_markup=main_keyboard(), parse_mode="Markdown"
        )

    elif data.startswith("svc_"):
        svc_key = data[4:]
        svc = SERVICES.get(svc_key)
        if not svc:
            return
        text = f"*{svc['name']}*\n\nPaketni tanlang:"
        await query.edit_message_text(text, reply_markup=packages_keyboard(svc_key), parse_mode="Markdown")

    elif data.startswith("pkg_"):
        pkg_id = data[4:]
        pkg = ALL_PACKAGES.get(pkg_id)
        if not pkg:
            return
        user_states[user_id] = {"step": "waiting_link", "package_id": pkg_id}
        svc = SERVICES[pkg["service"]]
        text = (
            f"*{svc['name']}* — {pkg['amount']}\n"
            f"💰 Narx: *{fmt(pkg['price'])} so'm*\n\n"
            f"📎 Instagram havolangizni yuboring:\n"
            f"_(Masalan: https://instagram.com/username)_"
        )
        await query.edit_message_text(
            text,
            reply_markup=back_keyboard(f"svc_{pkg['service']}"),
            parse_mode="Markdown"
        )

    elif data == "my_orders":
        await query.edit_message_text(
            "📋 *Mening buyurtmalarim*\n\n"
            "Bu bo'lim tez orada ishga tushadi.\n"
            "Buyurtma holati haqida admin siz bilan bog'lanadi.",
            reply_markup=back_keyboard(), parse_mode="Markdown"
        )

    elif data == "help":
        await query.edit_message_text(
            "❓ *Yordam*\n\n"
            "🔹 Xizmat tanlang\n"
            "🔹 Instagram havolangizni yuboring\n"
            "🔹 To'lovni amalga oshiring\n"
            "🔹 Chekni yuboring\n"
            "🔹 Admin tasdiqlaydi va xizmat boshlanadi\n\n"
            "📞 Muammo bo'lsa: @alibekadmin",
            reply_markup=back_keyboard(), parse_mode="Markdown"
        )

    elif data.startswith("admin_confirm_") or data.startswith("admin_reject_"):
        if user_id != ADMIN_ID:
            await query.answer("Siz admin emassiz!", show_alert=True)
            return
        
        is_confirm = data.startswith("admin_confirm_")
        order_id = data[14:] if is_confirm else data[13:]
        status_text = "✅ TASDIQLANDI" if is_confirm else "❌ RAD ETILDI"
        
        # Xabar turini tekshir (rasm yoki matn)
        try:
            if query.message.photo:
                old_caption = query.message.caption or ""
                await query.edit_message_caption(
                    caption=old_caption + f"\n\n{status_text}",
                    parse_mode="Markdown"
                )
            else:
                old_text = query.message.text or ""
                await query.edit_message_text(
                    old_text + f"\n\n{status_text}",
                    parse_mode="Markdown"
                )
        except Exception as e:
            logging.error(f"Xabar tahrirlashda xato: {e}")
            await query.answer(status_text)
        
        # Mijozga xabar
        try:
            parts = order_id.split("_")
            client_id = int(parts[0])
            if is_confirm:
                msg = "✅ *Buyurtmangiz tasdiqlandi!*\n\nXizmat yaqin orada boshlanadi.\nRahmat! 🙏"
            else:
                msg = "❌ *Buyurtmangiz rad etildi.*\n\nTo'lov tasdiqlanmadi. Chekni qayta yuboring yoki admin bilan bog'laning."
            await context.bot.send_message(client_id, msg, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Mijozga xabar yuborishda xato: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_states.get(user_id)

    if not state:
        await update.message.reply_text(
            "Xizmat tanlash uchun /start bosing",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Bosh menyu", callback_data="main")
            ]])
        )
        return

    step = state.get("step")

    # === LINK KUTILMOQDA ===
    if step == "waiting_link":
        link = update.message.text.strip()
        if "instagram.com" not in link and "instagr.am" not in link:
            await update.message.reply_text(
                "⚠️ Instagram havolasi noto'g'ri!\n\n"
                "Havola instagram.com dan boshlanishi kerak.\n"
                "Masalan: https://instagram.com/username",
                reply_markup=back_keyboard()
            )
            return

        pkg_id = state["package_id"]
        pkg = ALL_PACKAGES[pkg_id]
        svc = SERVICES[pkg["service"]]
        user_states[user_id]["link"] = link
        user_states[user_id]["step"] = "waiting_payment"

        text = (
            f"✅ Havola qabul qilindi!\n\n"
            f"📦 *{svc['name']}* — {pkg['amount']}\n"
            f"🔗 {link}\n"
            f"💰 To'lov miqdori: *{fmt(pkg['price'])} so'm*\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💳 *To'lov rekvizitlari:*\n"
            f"Karta: `{CARD_NUMBER}`\n"
            f"Egasi: *{CARD_NAME}*\n"
            f"Summa: *{fmt(pkg['price'])} so'm*\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"To'lovni amalga oshirib, *chek rasmini* yuboring! 📸"
        )
        await update.message.reply_text(text, parse_mode="Markdown",
            reply_markup=back_keyboard()
        )

    # === TO'LOV CHEKI KUTILMOQDA ===
    elif step == "waiting_payment":
        if not update.message.photo:
            await update.message.reply_text(
                "📸 Iltimos, to'lov cheki *rasmini* yuboring!\n"
                "(Screenshot yoki foto shaklida)",
                parse_mode="Markdown"
            )
            return

        pkg_id = state["package_id"]
        pkg = ALL_PACKAGES[pkg_id]
        svc = SERVICES[pkg["service"]]
        link = state.get("link", "—")
        user = update.effective_user
        username = f"@{user.username}" if user.username else "yo'q"
        order_id = f"{user_id}_{pkg_id}"

        # Adminga yuborish
        admin_text = (
            f"🔔 *YANGI BUYURTMA!*\n\n"
            f"👤 Mijoz: {user.full_name}\n"
            f"📱 Username: {username}\n"
            f"🆔 ID: `{user_id}`\n\n"
            f"📦 Xizmat: *{svc['name']}*\n"
            f"📊 Miqdor: *{pkg['amount']}*\n"
            f"🔗 Havola: {link}\n"
            f"💰 Summa: *{fmt(pkg['price'])} so'm*\n\n"
            f"Chekni tekshirib, tasdiqlang:"
        )

        admin_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin_confirm_{order_id}"),
                InlineKeyboardButton("❌ Rad etish", callback_data=f"admin_reject_{order_id}"),
            ]
        ])

        photo = update.message.photo[-1].file_id
        try:
            await context.bot.send_photo(
                ADMIN_ID,
                photo=photo,
                caption=admin_text,
                reply_markup=admin_keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Adminga yuborishda xato: {e}")

        # Mijozga tasdiqlash
        user_states.pop(user_id, None)
        await update.message.reply_text(
            "✅ *Chek qabul qilindi!*\n\n"
            "Admin to'lovni tekshirmoqda.\n"
            "Tez orada xabar beriladi! ⏳\n\n"
            "Odatda 5-15 daqiqa ichida bajariladi.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Bosh menyu", callback_data="main")
            ]])
        )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))
    print("✅ Tezkor Obuna Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)
