import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
        "min_qty": 1000,
        "price_per_unit": 15,
        "recommended": [1000, 3000, 5000, 10000],
        "bonus_from": 5000,
        "bonus_pct": 10,
    },
    "like": {
        "name": "❤️ Like",
        "min_qty": 1000,
        "price_per_unit": 5,
        "recommended": [1000, 3000, 5000, 10000, 20000],
        "bonus_from": 10000,
        "bonus_pct": 10,
    },
    "prosmotr": {
        "name": "👀 Prosmotr",
        "min_qty": 1000,
        "price_per_unit": 3,
        "recommended": [1000, 3000, 5000, 10000],
        "bonus_from": 10000,
        "bonus_pct": 10,
    },
}

user_states = {}

def fmt(p):
    return f"{p:,}".replace(",", " ")

def get_bonus(svc, qty):
    if qty >= svc["bonus_from"]:
        return qty * svc["bonus_pct"] // 100
    return 0

def order_text(svc, qty, price, link=None):
    bonus = get_bonus(svc, qty)
    total = qty + bonus
    lines = [f"📦 *{svc['name']}* — {fmt(qty)} ta"]
    if bonus > 0:
        lines.append(f"🎁 *BONUS: +{fmt(bonus)} ta bepul!*")
        lines.append(f"✅ Jami: *{fmt(total)} ta*")
    lines.append(f"💰 To'lov: *{fmt(price)} so'm*")
    if link:
        lines.append(f"🔗 {link}")
    return "\n".join(lines)

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Obunachi", callback_data="svc_obunachi"),
         InlineKeyboardButton("❤️ Like", callback_data="svc_like")],
        [InlineKeyboardButton("👀 Prosmotr", callback_data="svc_prosmotr")],
        [InlineKeyboardButton("❓ Yordam", callback_data="help")],
    ])

def service_kb(svc_key):
    svc = SERVICES[svc_key]
    keyboard = []
    rec_row = []
    for qty in svc["recommended"]:
        price = qty * svc["price_per_unit"]
        bonus = get_bonus(svc, qty)
        label = f"{fmt(qty)} — {fmt(price)} so'm"
        if bonus > 0:
            label += f" 🎁+{fmt(bonus)}"
        rec_row.append(InlineKeyboardButton(label, callback_data=f"qty_{svc_key}_{qty}"))
        if len(rec_row) == 2:
            keyboard.append(rec_row)
            rec_row = []
    if rec_row:
        keyboard.append(rec_row)
    keyboard.append([InlineKeyboardButton("✏️ O'zim kiritaman", callback_data=f"custom_{svc_key}")])
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="main")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states.pop(user_id, None)
    await update.message.reply_text(
        "🚀 *Tezkor Obuna — SMM Xizmati*\n\n"
        "Instagram xizmatlari:\n"
        "👥 Obunachi | ❤️ Like | 👀 Prosmotr\n\n"
        "🎁 Ko'p olsang — BONUS!\n"
        "✅ Tezkor • 🛡 Xavfsiz • 🔄 Kafolat\n\n"
        "Xizmat tanlang 👇",
        reply_markup=main_kb(),
        parse_mode="Markdown"
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "main":
        user_states.pop(user_id, None)
        await query.edit_message_text(
            "🚀 *Tezkor Obuna — SMM Xizmati*\n\nXizmat tanlang 👇",
            reply_markup=main_kb(),
            parse_mode="Markdown"
        )

    elif data.startswith("svc_"):
        svc_key = data[4:]
        svc = SERVICES[svc_key]
        text = (
            f"*{svc['name']}*\n\n"
            f"💰 1 ta narxi: *{svc['price_per_unit']} so'm*\n"
            f"📦 Minimum zakaz: *{fmt(svc['min_qty'])} ta*\n"
            f"🎁 {fmt(svc['bonus_from'])} tadan yuqori → *{svc['bonus_pct']}% BONUS!*\n\n"
            f"Paket tanlang yoki o'z miqdoringizni kiriting 👇"
        )
        await query.edit_message_text(text, reply_markup=service_kb(svc_key), parse_mode="Markdown")

    elif data.startswith("qty_"):
        parts = data.split("_")
        svc_key = parts[1]
        qty = int(parts[2])
        svc = SERVICES[svc_key]
        price = qty * svc["price_per_unit"]
        bonus = get_bonus(svc, qty)
        user_states[user_id] = {"step": "waiting_link", "svc_key": svc_key, "qty": qty, "price": price, "bonus": bonus}
        text = order_text(svc, qty, price) + "\n\n📎 Instagram havolangizni yuboring:\n_(Masalan: https://instagram.com/username)_"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=f"svc_{svc_key}")]]), parse_mode="Markdown")

    elif data.startswith("custom_"):
        svc_key = data[7:]
        svc = SERVICES[svc_key]
        user_states[user_id] = {"step": "waiting_qty", "svc_key": svc_key}
        await query.edit_message_text(
            f"*{svc['name']}*\n\n"
            f"💰 1 ta narxi: *{svc['price_per_unit']} so'm*\n"
            f"📦 Minimum: *{fmt(svc['min_qty'])} ta*\n"
            f"🎁 {fmt(svc['bonus_from'])} tadan yuqori → *{svc['bonus_pct']}% BONUS!*\n\n"
            f"✏️ Nechta kerakligini yozing:\n_(Masalan: 1500)_",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=f"svc_{svc_key}")]]),
            parse_mode="Markdown"
        )

    elif data == "help":
        await query.edit_message_text(
            "❓ *Yordam*\n\n"
            "1️⃣ Xizmat tanlang\n"
            "2️⃣ Miqdor tanlang yoki kiriting\n"
            "3️⃣ Instagram havolangizni yuboring\n"
            "4️⃣ Kartaga to'lov qiling\n"
            "5️⃣ Chek rasmini yuboring\n"
            "6️⃣ Admin tasdiqlaydi ✅\n\n"
            "📞 Muammo: @anorbekovich\n"
            "📱 77-452-11-04",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="main")]]),
            parse_mode="Markdown"
        )

    elif data.startswith("confirm_") or data.startswith("reject_"):
        if user_id != ADMIN_ID:
            await query.answer("Siz admin emassiz!", show_alert=True)
            return
        is_confirm = data.startswith("confirm_")
        client_id = int(data.split("_")[1])
        status = "✅ TASDIQLANDI" if is_confirm else "❌ RAD ETILDI"
        try:
            if query.message.photo:
                await query.edit_message_caption(caption=(query.message.caption or "") + f"\n\n{status}", parse_mode="Markdown")
            else:
                await query.edit_message_text((query.message.text or "") + f"\n\n{status}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Edit xato: {e}")
            await query.answer(status)
        try:
            if is_confirm:
                msg = "✅ *Buyurtmangiz tasdiqlandi!*\n\nXizmat boshlanmoqda! Tez orada bajariladi 🚀"
            else:
                msg = "❌ *Buyurtmangiz rad etildi.*\n\nTo'lov tasdiqlanmadi. @anorbekovich bilan bog'laning."
            await context.bot.send_message(client_id, msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Mijozga xabar xato: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_states.get(user_id)
    text = update.message.text.strip()

    if not state:
        await update.message.reply_text("Boshlash uchun /start bosing 👇")
        return

    step = state.get("step")

    if step == "waiting_qty":
        svc_key = state["svc_key"]
        svc = SERVICES[svc_key]
        if not text.isdigit():
            await update.message.reply_text("⚠️ Faqat raqam kiriting!\nMasalan: *1500*", parse_mode="Markdown")
            return
        qty = int(text)
        if qty < svc["min_qty"]:
            await update.message.reply_text(
                f"⚠️ Minimum zakaz: *{fmt(svc['min_qty'])} ta*\n"
                f"Siz {fmt(qty)} ta kiritdingiz. Kamida *{fmt(svc['min_qty'])}* ta kiriting!",
                parse_mode="Markdown"
            )
            return
        price = qty * svc["price_per_unit"]
        bonus = get_bonus(svc, qty)
        user_states[user_id].update({"qty": qty, "price": price, "bonus": bonus, "step": "waiting_link"})
        text_out = "✅ " + order_text(svc, qty, price) + "\n\n📎 Instagram havolangizni yuboring:\n_(Masalan: https://instagram.com/username)_"
        await update.message.reply_text(text_out, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=f"svc_{svc_key}")]]))

    elif step == "waiting_link":
        if "instagram.com" not in text and "instagr.am" not in text:
            await update.message.reply_text("⚠️ *Instagram havolasi bo'lishi kerak!*\nMasalan: https://instagram.com/username", parse_mode="Markdown")
            return
        svc_key = state["svc_key"]
        svc = SERVICES[svc_key]
        qty = state["qty"]
        price = state["price"]
        user_states[user_id]["link"] = text
        user_states[user_id]["step"] = "waiting_payment"
        await update.message.reply_text(
            "✅ Havola qabul qilindi!\n\n" +
            order_text(svc, qty, price, text) +
            f"\n\n━━━━━━━━━━━━━━━━\n"
            f"💳 *To'lov rekvizitlari:*\n"
            f"Karta: `{CARD_NUMBER}`\n"
            f"Egasi: *{CARD_NAME}*\n"
            f"Summa: *{fmt(price)} so'm*\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"💸 To'lovni amalga oshirib, *chek rasmini* yuboring! 📸",
            parse_mode="Markdown"
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_states.get(user_id)
    if not state or state.get("step") != "waiting_payment":
        await update.message.reply_text("Boshlash uchun /start bosing 👇")
        return

    svc_key = state["svc_key"]
    svc = SERVICES[svc_key]
    qty = state["qty"]
    price = state["price"]
    bonus = state.get("bonus", 0)
    total = qty + bonus
    link = state.get("link", "—")
    user = update.effective_user
    username = f"@{user.username}" if user.username else "username yo'q"

    caption = (
        f"🔔 *YANGI BUYURTMA!*\n\n"
        f"👤 {user.full_name}\n"
        f"📱 {username}\n"
        f"🆔 `{user_id}`\n\n"
        f"📦 *{svc['name']}* — {fmt(qty)} ta\n"
    )
    if bonus > 0:
        caption += f"🎁 Bonus: +{fmt(bonus)} ta → Jami: *{fmt(total)} ta*\n"
    caption += f"🔗 {link}\n💰 *{fmt(price)} so'm*"

    admin_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_{user_id}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{user_id}"),
    ]])

    try:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=caption, reply_markup=admin_kb, parse_mode="Markdown")
        logger.info(f"Adminga yuborildi: {user_id}, {svc['name']}, {qty} ta, {price} so'm")
    except Exception as e:
        logger.error(f"Adminga yuborishda XATO: {e}")

    user_states.pop(user_id, None)
    await update.message.reply_text(
        "✅ *Chek qabul qilindi!*\n\nAdmin to'lovni tekshirmoqda.\n5-15 daqiqa ichida xabar beriladi! ⏳",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main")]])
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    logger.info("✅ Tezkor Obuna Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)
