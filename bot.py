"""
Xitoydan uskuna va sourcing buyurtma boti
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "0"))
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    LANG,
    MAIN_MENU,
    # Uskuna branch
    EQ_TYPE,
    EQ_CAPACITY,
    EQ_BUDGET,
    # Sourcing branch
    SRC_PRODUCT,
    SRC_QUANTITY,
    SRC_PARTNERSHIP,
    # Contact info (shared)
    CONTACT_NAME,
    CONTACT_PHONE,
    CONTACT_CITY,
) = range(11)

# ─── Texts ─────────────────────────────────────────────────────────────────────

T = {
    "uz": {
        "welcome": (
            "Assalomu alaykum! 👋\n"
            "Xitoydan uskuna va ishlab chiqarish liniyalari bo'yicha xizmatimizga xush kelibsiz.\n\n"
            "Iltimos, tilni tanlang:"
        ),
        "lang_btn": ["🇺🇿 O'zbek", "🇷🇺 Русский"],
        "main_menu": (
            "Qaysi xizmatdan foydalanmoqchisiz?"
        ),
        "menu_btn": ["⚙️ Uskuna buyurtma", "🌏 Xitoydan yuk/Sourcing"],
        "eq_type": (
            "⚙️ *Uskuna / Ishlab chiqarish liniyasi*\n\n"
            "1️⃣ Qanday uskuna yoki ishlab chiqarish liniyasi kerak?\n"
            "(Masalan: suv idish to'ldirish liniyasi, kraker ishlab chiqarish, qog'oz sumka mashinasi…)"
        ),
        "eq_capacity": (
            "2️⃣ Ushbu uskuna bir kunda/soatda qancha mahsulot ishlab chiqarishi kerak?\n"
            "(Masalan: 5000 ta/soat, 2 tonna/kun)"
        ),
        "eq_budget": (
            "3️⃣ Taxminiy byudjetingiz qancha?\n"
            "(Masalan: $10,000 – $30,000, yoki aniq miqdor)"
        ),
        "src_product": (
            "🌏 *Xitoydan yuk / Sourcing*\n\n"
            "1️⃣ Qanday mahsulot olib kelmoqchisiz?\n"
            "(Masalan: kiyim-kechak, elektronika, qurilish materiallari, oziq-ovqat…)"
        ),
        "src_quantity": (
            "2️⃣ Taxminiy miqdor yoki hajm?\n"
            "(Masalan: 500 kg, 1 konteyner, 200 dona)"
        ),
        "src_partnership": (
            "3️⃣ Doimiy hamkorlik qilmoqchimisiz?\n"
            "(Bitta buyurtma yoki uzoq muddatli hamkorlik?)"
        ),
        "partnership_btn": ["✅ Ha, doimiy hamkorlik", "🔁 Hozircha bitta buyurtma"],
        "contact_name": "📋 Ism-familiyangizni kiriting:",
        "contact_phone": (
            "📞 Telefon raqamingizni yuboring:\n"
            "(Tugmani bosing yoki qo'lda kiriting)"
        ),
        "phone_btn": "📱 Raqamni yuborish",
        "contact_city": "🏙️ Qaysi shahar/viloyatdasiz?",
        "done": (
            "✅ *Rahmat! Arizangiz qabul qilindi.*\n\n"
            "Mutaxassisimiz 24 soat ichida siz bilan bog'lanadi. 🙏"
        ),
        "back": "🔙 Ortga",
        "restart": "🔄 Qayta boshlash",
    },
    "ru": {
        "welcome": (
            "Здравствуйте! 👋\n"
            "Добро пожаловать в наш сервис по оборудованию и производственным линиям из Китая.\n\n"
            "Пожалуйста, выберите язык:"
        ),
        "lang_btn": ["🇺🇿 O'zbek", "🇷🇺 Русский"],
        "main_menu": "Какой услугой хотите воспользоваться?",
        "menu_btn": ["⚙️ Заказ оборудования", "🌏 Груз/Сорсинг из Китая"],
        "eq_type": (
            "⚙️ *Оборудование / Производственная линия*\n\n"
            "1️⃣ Какое оборудование или производственная линия вам нужна?\n"
            "(Например: линия розлива воды, производство крекеров, машина для бумажных пакетов…)"
        ),
        "eq_capacity": (
            "2️⃣ Какой объём производства нужен в день/час?\n"
            "(Например: 5000 шт/час, 2 тонны/день)"
        ),
        "eq_budget": (
            "3️⃣ Ваш ориентировочный бюджет?\n"
            "(Например: $10,000 – $30,000 или точная сумма)"
        ),
        "src_product": (
            "🌏 *Груз из Китая / Сорсинг*\n\n"
            "1️⃣ Какой товар хотите привезти?\n"
            "(Например: одежда, электроника, стройматериалы, продукты питания…)"
        ),
        "src_quantity": (
            "2️⃣ Приблизительное количество или объём?\n"
            "(Например: 500 кг, 1 контейнер, 200 штук)"
        ),
        "src_partnership": (
            "3️⃣ Хотите постоянное партнёрство?\n"
            "(Разовый заказ или долгосрочное сотрудничество?)"
        ),
        "partnership_btn": ["✅ Да, постоянное партнёрство", "🔁 Пока разовый заказ"],
        "contact_name": "📋 Введите ваше имя и фамилию:",
        "contact_phone": (
            "📞 Отправьте номер телефона:\n"
            "(Нажмите кнопку или введите вручную)"
        ),
        "phone_btn": "📱 Отправить номер",
        "contact_city": "🏙️ Из какого вы города/региона?",
        "done": (
            "✅ *Спасибо! Ваша заявка принята.*\n\n"
            "Наш специалист свяжется с вами в течение 24 часов. 🙏"
        ),
        "back": "🔙 Назад",
        "restart": "🔄 Начать заново",
    },
}


# ─── Helpers ───────────────────────────────────────────────────────────────────

def lang(ctx):
    return ctx.user_data.get("lang", "uz")


def t(ctx, key):
    return T[lang(ctx)][key]


def kb(buttons, resize=True, one_time=True):
    return ReplyKeyboardMarkup([[b] for b in buttons], resize_keyboard=resize, one_time_keyboard=one_time)


def kb_row(buttons, resize=True, one_time=True):
    return ReplyKeyboardMarkup([buttons], resize_keyboard=resize, one_time_keyboard=one_time)


# ─── Handlers ──────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        T["uz"]["welcome"],
        reply_markup=kb_row(T["uz"]["lang_btn"]),
    )
    return LANG


async def choose_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text
    if "O'zbek" in txt or "Ўзбек" in txt:
        ctx.user_data["lang"] = "uz"
    else:
        ctx.user_data["lang"] = "ru"

    await update.message.reply_text(
        t(ctx, "main_menu"),
        reply_markup=kb(t(ctx, "menu_btn")),
    )
    return MAIN_MENU


async def main_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text
    if "Uskuna" in txt or "оборудовани" in txt.lower():
        ctx.user_data["service"] = "equipment"
        await update.message.reply_text(
            t(ctx, "eq_type"),
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return EQ_TYPE
    else:
        ctx.user_data["service"] = "sourcing"
        await update.message.reply_text(
            t(ctx, "src_product"),
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return SRC_PRODUCT


# ── Equipment branch ──────────────────────────────────────────────────────────

async def eq_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["eq_type"] = update.message.text
    await update.message.reply_text(t(ctx, "eq_capacity"))
    return EQ_CAPACITY


async def eq_capacity(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["eq_capacity"] = update.message.text
    await update.message.reply_text(t(ctx, "eq_budget"))
    return EQ_BUDGET


async def eq_budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["eq_budget"] = update.message.text
    await ask_name(update, ctx)
    return CONTACT_NAME


# ── Sourcing branch ───────────────────────────────────────────────────────────

async def src_product(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["src_product"] = update.message.text
    await update.message.reply_text(t(ctx, "src_quantity"))
    return SRC_QUANTITY


async def src_quantity(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["src_quantity"] = update.message.text
    await update.message.reply_text(
        t(ctx, "src_partnership"),
        reply_markup=kb(t(ctx, "partnership_btn")),
    )
    return SRC_PARTNERSHIP


async def src_partnership(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["src_partnership"] = update.message.text
    await ask_name(update, ctx)
    return CONTACT_NAME


# ── Contact info ──────────────────────────────────────────────────────────────

async def ask_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        t(ctx, "contact_name"),
        reply_markup=ReplyKeyboardRemove(),
    )


async def contact_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["name"] = update.message.text
    phone_btn = KeyboardButton(t(ctx, "phone_btn"), request_contact=True)
    await update.message.reply_text(
        t(ctx, "contact_phone"),
        reply_markup=ReplyKeyboardMarkup(
            [[phone_btn]], resize_keyboard=True, one_time_keyboard=True
        ),
    )
    return CONTACT_PHONE


async def contact_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        ctx.user_data["phone"] = update.message.contact.phone_number
    else:
        ctx.user_data["phone"] = update.message.text
    await update.message.reply_text(
        t(ctx, "contact_city"),
        reply_markup=ReplyKeyboardRemove(),
    )
    return CONTACT_CITY


async def contact_city(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["city"] = update.message.text
    await send_to_admin(update, ctx)
    await update.message.reply_text(
        t(ctx, "done"),
        parse_mode="Markdown",
        reply_markup=kb([t(ctx, "restart")]),
    )
    return ConversationHandler.END


# ─── Admin Notification ────────────────────────────────────────────────────────

async def send_to_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = ctx.user_data
    user = update.effective_user
    l = lang(ctx)

    if d.get("service") == "equipment":
        if l == "uz":
            details = (
                f"⚙️ *USKUNA BUYURTMASI*\n\n"
                f"👤 Ism: {d.get('name')}\n"
                f"📞 Tel: {d.get('phone')}\n"
                f"🏙️ Shahar: {d.get('city')}\n"
                f"─────────────────\n"
                f"🔧 Uskuna turi: {d.get('eq_type')}\n"
                f"📊 Quvvat: {d.get('eq_capacity')}\n"
                f"💰 Byudjet: {d.get('eq_budget')}\n"
                f"─────────────────\n"
                f"🆔 Telegram: @{user.username or user.id}"
            )
        else:
            details = (
                f"⚙️ *ЗАКАЗ ОБОРУДОВАНИЯ*\n\n"
                f"👤 Имя: {d.get('name')}\n"
                f"📞 Тел: {d.get('phone')}\n"
                f"🏙️ Город: {d.get('city')}\n"
                f"─────────────────\n"
                f"🔧 Оборудование: {d.get('eq_type')}\n"
                f"📊 Мощность: {d.get('eq_capacity')}\n"
                f"💰 Бюджет: {d.get('eq_budget')}\n"
                f"─────────────────\n"
                f"🆔 Telegram: @{user.username or user.id}"
            )
    else:
        if l == "uz":
            details = (
                f"🌏 *SOURCING / XUK BUYURTMASI*\n\n"
                f"👤 Ism: {d.get('name')}\n"
                f"📞 Tel: {d.get('phone')}\n"
                f"🏙️ Shahar: {d.get('city')}\n"
                f"─────────────────\n"
                f"📦 Mahsulot: {d.get('src_product')}\n"
                f"⚖️ Miqdor: {d.get('src_quantity')}\n"
                f"🤝 Hamkorlik: {d.get('src_partnership')}\n"
                f"─────────────────\n"
                f"🆔 Telegram: @{user.username or user.id}"
            )
        else:
            details = (
                f"🌏 *СОРСИНГ / ГРУЗ ИЗ КИТАЯ*\n\n"
                f"👤 Имя: {d.get('name')}\n"
                f"📞 Тел: {d.get('phone')}\n"
                f"🏙️ Город: {d.get('city')}\n"
                f"─────────────────\n"
                f"📦 Товар: {d.get('src_product')}\n"
                f"⚖️ Количество: {d.get('src_quantity')}\n"
                f"🤝 Партнёрство: {d.get('src_partnership')}\n"
                f"─────────────────\n"
                f"🆔 Telegram: @{user.username or user.id}"
            )

    await ctx.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=details,
        parse_mode="Markdown",
    )


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "❌ Bekor qilindi / Отменено",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_lang)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            # Equipment
            EQ_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, eq_type)],
            EQ_CAPACITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, eq_capacity)],
            EQ_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, eq_budget)],
            # Sourcing
            SRC_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, src_product)],
            SRC_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, src_quantity)],
            SRC_PARTNERSHIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, src_partnership)],
            # Contact
            CONTACT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_name)],
            CONTACT_PHONE: [
                MessageHandler(filters.CONTACT, contact_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, contact_phone),
            ],
            CONTACT_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_city)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)

    print("🤖 Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
