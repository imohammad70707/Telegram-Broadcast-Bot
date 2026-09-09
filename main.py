import asyncio
import logging

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, ADMIN_ID

from bot.storage import (
    add_group,
    remove_group,
    get_group,
    get_active_groups,
    get_disabled_groups,
    get_group_count,
    get_active_group_count,
    get_disabled_group_count,
    toggle_group,
    update_group_title,
)

from bot.reports import (
    create_report,
    get_last_report,
)


# =========================================================
# Logging
# =========================================================

logging.basicConfig(
    format=(
        "%(asctime)s - "
        "%(name)s - "
        "%(levelname)s - "
        "%(message)s"
    ),
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# Conversation States
# =========================================================

WAITING_MESSAGE = 1
CONFIRM_MESSAGE = 2


# =========================================================
# Keyboards
# =========================================================

ADMIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📢 ارسال پیام"],
        ["👥 مدیریت گروه‌ها", "📊 گزارش‌ها"],
    ],
    resize_keyboard=True,
    is_persistent=True,
)


GROUPS_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📋 لیست گروه‌ها"],
        ["📊 آمار گروه‌ها"],
        ["🔄 بروزرسانی گروه‌ها"],
        ["⬅️ بازگشت"],
    ],
    resize_keyboard=True,
    is_persistent=True,
)


CONFIRM_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["✅ تأیید ارسال"],
        ["❌ لغو"],
    ],
    resize_keyboard=True,
)


# =========================================================
# Admin Check
# =========================================================

def is_admin(user_id):
    return user_id == ADMIN_ID


def is_admin_update(update: Update):
    user = update.effective_user

    if user is None:
        return False

    return is_admin(user.id)


# =========================================================
# /start
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.message is None:
        return

    if not is_admin_update(update):

        await update.message.reply_text(
            "⛔ شما اجازه استفاده از این ربات را ندارید."
        )

        return

    await update.message.reply_text(
        "🔐 پنل مدیریت\n\n"
        "سلام مدیر 👋\n"
        "به پنل مدیریت خوش آمدی.\n\n"
        "یکی از گزینه‌های زیر را انتخاب کن:",
        reply_markup=ADMIN_KEYBOARD,
    )


# =========================================================
# Bot Join / Leave Detection
# =========================================================

async def my_chat_member_update(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    chat_member = update.my_chat_member

    if chat_member is None:
        return

    chat = chat_member.chat

    # فقط گروه و سوپرگروه
    if chat.type not in (
        "group",
        "supergroup",
    ):
        return

    new_status = chat_member.new_chat_member.status

    # -----------------------------------------------------
    # Bot Joined
    # -----------------------------------------------------

    if new_status in (
        "member",
        "administrator",
    ):

        added = add_group(
            chat.id,
            chat.title or "بدون نام",
        )

        if added:

            logger.info(
                "Group added: %s (%s)",
                chat.title,
                chat.id,
            )

    # -----------------------------------------------------
    # Bot Left / Kicked
    # -----------------------------------------------------

    elif new_status in (
        "left",
        "kicked",
    ):

        removed = remove_group(
            chat.id
        )

        if removed:

            logger.info(
                "Group removed: %s (%s)",
                chat.title,
                chat.id,
            )


# =========================================================
# Start Broadcast
# =========================================================

async def start_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin_update(update):
        return ConversationHandler.END

    if update.message is None:
        return ConversationHandler.END

    active_groups = get_active_groups()

    if not active_groups:

        await update.message.reply_text(
            "⚠️ هیچ گروه فعالی برای ارسال وجود ندارد.",
            reply_markup=ADMIN_KEYBOARD,
        )

        return ConversationHandler.END

    await update.message.reply_text(
        "📢 ارسال پیام\n\n"
        "📝 متن کامل پیام را در پیام بعدی ارسال کن.\n\n"
        "ℹ️ فاصله‌ها، Enterها، پاراگراف‌ها و "
        "ایموجی‌ها حفظ خواهند شد.\n\n"
        "برای لغو، دکمه «❌ لغو» را بزن.",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["❌ لغو"],
            ],
            resize_keyboard=True,
        ),
    )

    return WAITING_MESSAGE


# =========================================================
# Receive Broadcast Message
# =========================================================

async def receive_broadcast_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin_update(update):
        return ConversationHandler.END

    message = update.message

    if message is None:
        return WAITING_MESSAGE

    # -----------------------------------------------------
    # Cancel
    # -----------------------------------------------------

    if message.text == "❌ لغو":

        context.user_data.pop(
            "broadcast_text",
            None,
        )

        await message.reply_text(
            "❌ ارسال پیام لغو شد.",
            reply_markup=ADMIN_KEYBOARD,
        )

        return ConversationHandler.END

    # -----------------------------------------------------
    # Text Only
    # -----------------------------------------------------

    if not message.text:

        await message.reply_text(
            "⚠️ لطفاً پیام را به‌صورت متنی ارسال کن."
        )

        return WAITING_MESSAGE

    # -----------------------------------------------------
    # IMPORTANT
    #
    # هیچ strip یا split روی متن اصلی انجام نمی‌دهیم.
    # بنابراین فاصله‌ها و خط‌های خالی حفظ می‌شوند.
    # -----------------------------------------------------

    broadcast_text = message.text

    context.user_data[
        "broadcast_text"
    ] = broadcast_text

    active_groups = get_active_groups()

    # -----------------------------------------------------
    # Preview
    # -----------------------------------------------------

    preview = broadcast_text

    if len(preview) > 1500:

        preview = (
            preview[:1500]
            + "\n\n…"
        )

    await message.reply_text(
        "👀 پیش‌نمایش پیام:\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{preview}\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 گروه‌های فعال: "
        f"{len(active_groups)}\n"
        f"📝 تعداد کاراکتر: "
        f"{len(broadcast_text)}\n\n"
        "آیا پیام ارسال شود؟",
        reply_markup=CONFIRM_KEYBOARD,
    )

    return CONFIRM_MESSAGE


# =========================================================
# Split Long Messages
# =========================================================

def split_text(
    text,
    max_length=4000,
):

    if len(text) <= max_length:
        return [text]

    parts = []
    start = 0

    while start < len(text):

        remaining_length = len(text) - start

        if remaining_length <= max_length:

            parts.append(
                text[start:]
            )

            break

        end = start + max_length

        # -------------------------------------------------
        # اول تلاش برای شکستن روی newline
        # -------------------------------------------------

        cut = text.rfind(
            "\n",
            start,
            end,
        )

        # -------------------------------------------------
        # اگر newline پیدا نشد، روی space
        # -------------------------------------------------

        if cut <= start:

            cut = text.rfind(
                " ",
                start,
                end,
            )

        # -------------------------------------------------
        # اگر هیچ نقطه مناسبی پیدا نشد
        # -------------------------------------------------

        if cut <= start:

            cut = end

        else:

            # newline را در بخش فعلی نگه می‌داریم
            cut += 1

        parts.append(
            text[start:cut]
        )

        start = cut

    return parts


# =========================================================
# Confirm Broadcast
# =========================================================

async def confirm_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin_update(update):
        return ConversationHandler.END

    message = update.message

    if message is None:
        return CONFIRM_MESSAGE

    button_text = message.text

    # -----------------------------------------------------
    # Cancel
    # -----------------------------------------------------

    if button_text == "❌ لغو":

        context.user_data.pop(
            "broadcast_text",
            None,
        )

        await message.reply_text(
            "❌ ارسال پیام لغو شد.",
            reply_markup=ADMIN_KEYBOARD,
        )

        return ConversationHandler.END

    # -----------------------------------------------------
    # Confirmation
    # -----------------------------------------------------

    if button_text != "✅ تأیید ارسال":

        await message.reply_text(
            "⚠️ لطفاً یکی از گزینه‌های "
            "«✅ تأیید ارسال» یا «❌ لغو» را انتخاب کن."
        )

        return CONFIRM_MESSAGE

    # -----------------------------------------------------
    # Get Stored Message
    # -----------------------------------------------------

    broadcast_text = context.user_data.get(
        "broadcast_text"
    )

    if not broadcast_text:

        await message.reply_text(
            "❌ متن ارسال پیدا نشد.\n"
            "لطفاً دوباره تلاش کن.",
            reply_markup=ADMIN_KEYBOARD,
        )

        return ConversationHandler.END

    # -----------------------------------------------------
    # Get Active Groups
    # -----------------------------------------------------

    active_groups = get_active_groups()

    if not active_groups:

        await message.reply_text(
            "⚠️ هیچ گروه فعالی وجود ندارد.",
            reply_markup=ADMIN_KEYBOARD,
        )

        return ConversationHandler.END

    # -----------------------------------------------------
    # Start Sending
    # -----------------------------------------------------

    await message.reply_text(
        "📤 ارسال شروع شد...\n\n"
        f"👥 تعداد گروه‌های فعال: "
        f"{len(active_groups)}\n\n"
        "⏳ لطفاً تا پایان عملیات صبر کن.",
        reply_markup=ADMIN_KEYBOARD,
    )

    success = 0
    failed = 0

    results = []

    # -----------------------------------------------------
    # Split Message
    # -----------------------------------------------------

    parts = split_text(
        broadcast_text,
        max_length=4000,
    )

    logger.info(
        "Broadcast started | groups=%s | parts=%s",
        len(active_groups),
        len(parts),
    )

    # -----------------------------------------------------
    # Send To Groups
    # -----------------------------------------------------

    for group in active_groups:

        chat_id = group.get("chat_id")

        title = group.get(
            "title",
            "بدون نام",
        )

        if chat_id is None:
            continue

        try:

            for part in parts:

                await context.bot.send_message(
                    chat_id=chat_id,
                    text=part,
                )

                # فاصله کوتاه بین قسمت‌های پیام بلند
                if len(parts) > 1:
                    await asyncio.sleep(0.3)

            success += 1

            results.append({
                "chat_id": chat_id,
                "title": title,
                "status": "success",
                "error": None,
            })

            logger.info(
                "Message sent successfully: %s (%s)",
                title,
                chat_id,
            )

        except Exception as error:

            failed += 1

            error_text = str(error)

            results.append({
                "chat_id": chat_id,
                "title": title,
                "status": "failed",
                "error": error_text,
            })

            logger.error(
                "Failed to send to %s (%s): %s",
                title,
                chat_id,
                error_text,
            )

        # فاصله بین گروه‌ها
        await asyncio.sleep(0.5)

    # -----------------------------------------------------
    # Save Report
    # -----------------------------------------------------

    report = create_report(
        message_text=broadcast_text,
        total_groups=len(active_groups),
        success=success,
        failed=failed,
        results=results,
    )

    # -----------------------------------------------------
    # Clear Temporary Data
    # -----------------------------------------------------

    context.user_data.pop(
        "broadcast_text",
        None,
    )

    # -----------------------------------------------------
    # Final Report
    # -----------------------------------------------------

    await message.reply_text(
        "📊 گزارش ارسال\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🆔 شماره گزارش: "
        f"#{report['id']}\n"
        f"🕐 زمان: "
        f"{report['time']}\n"
        f"📝 کاراکترها: "
        f"{report['message_length']}\n\n"
        f"👥 کل گروه‌ها: "
        f"{report['total_groups']}\n"
        f"🟢 موفق: "
        f"{report['success']}\n"
        f"🔴 ناموفق: "
        f"{report['failed']}\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🏁 عملیات ارسال تمام شد.",
        reply_markup=ADMIN_KEYBOARD,
    )

    return ConversationHandler.END


# =========================================================
# Group Management Menu
# =========================================================

async def show_group_management(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin_update(update):
        return

    if update.message is None:
        return

    await update.message.reply_text(
        "👥 مدیریت گروه‌ها\n\n"
        "از گزینه‌های زیر استفاده کن:",
        reply_markup=GROUPS_KEYBOARD,
    )


# =========================================================
# Build Group Buttons
# =========================================================

def build_group_buttons(groups):

    buttons = []

    for group in groups:

        chat_id = group.get("chat_id")

        title = group.get(
            "title",
            "بدون نام",
        )

        enabled = group.get(
            "enabled",
            True,
        )

        icon = (
            "🟢"
            if enabled
            else
            "🔴"
        )

        buttons.append([
            InlineKeyboardButton(
                f"{icon} {title}",
                callback_data=f"group:{chat_id}",
            )
        ])

    return buttons


# =========================================================
# Show Groups
# =========================================================

async def show_groups(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin_update(update):
        return

    if update.message is None:
        return

    active_groups = get_active_groups()
    disabled_groups = get_disabled_groups()

    all_groups = (
        active_groups
        + disabled_groups
    )

    if not all_groups:

        await update.message.reply_text(
            "📭 هنوز هیچ گروهی ثبت نشده است.",
            reply_markup=GROUPS_KEYBOARD,
        )

        return

    buttons = build_group_buttons(
        all_groups
    )

    await update.message.reply_text(
        "📋 لیست گروه‌ها\n\n"
        "🟢 فعال\n"
        "🔴 غیرفعال\n\n"
        "برای مدیریت هر گروه روی نام آن بزن:",
        reply_markup=InlineKeyboardMarkup(
            buttons
        ),
    )


# =========================================================
# Group Statistics
# =========================================================

async def show_group_stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin_update(update):
        return

    if update.message is None:
        return

    total = get_group_count()
    active = get_active_group_count()
    disabled = get_disabled_group_count()

    await update.message.reply_text(
        "📊 آمار گروه‌ها\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👥 کل گروه‌ها: {total}\n"
        f"🟢 فعال: {active}\n"
        f"🔴 غیرفعال: {disabled}\n"
        "━━━━━━━━━━━━━━━━━━",
        reply_markup=GROUPS_KEYBOARD,
    )


# =========================================================
# Group Details
# =========================================================

async def show_group_details(
    query,
    chat_id,
):

    group = get_group(chat_id)

    if group is None:

        await query.edit_message_text(
            "⚠️ این گروه دیگر در لیست وجود ندارد."
        )

        return

    title = group.get(
        "title",
        "بدون نام",
    )

    enabled = group.get(
        "enabled",
        True,
    )

    status = (
        "🟢 فعال"
        if enabled
        else
        "🔴 غیرفعال"
    )

    toggle_text = (
        "🔴 غیرفعال کردن"
        if enabled
        else
        "🟢 فعال کردن"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                toggle_text,
                callback_data=f"toggle:{chat_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 بروزرسانی نام",
                callback_data=f"refresh:{chat_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 حذف گروه",
                callback_data=f"delete:{chat_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت به لیست",
                callback_data="group_list",
            )
        ],
    ])

    await query.edit_message_text(
        "👥 اطلاعات گروه\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📌 نام: {title}\n"
        f"🆔 شناسه: {chat_id}\n"
        f"📊 وضعیت: {status}\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "عملیات موردنظر را انتخاب کن:",
        reply_markup=keyboard,
    )


# =========================================================
# Group Details Callback
# =========================================================

async def group_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )

        return

    await query.answer()

    try:

        chat_id = int(
            query.data.split(
                ":",
                1,
            )[1]
        )

    except (
        ValueError,
        IndexError,
    ):

        await query.edit_message_text(
            "❌ شناسه گروه نامعتبر است."
        )

        return

    await show_group_details(
        query,
        chat_id,
    )


# =========================================================
# Toggle Group Callback
# =========================================================

async def toggle_group_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )

        return

    try:

        chat_id = int(
            query.data.split(
                ":",
                1,
            )[1]
        )

    except (
        ValueError,
        IndexError,
    ):

        await query.answer(
            "❌ شناسه نامعتبر است.",
            show_alert=True,
        )

        return

    new_status = toggle_group(
        chat_id
    )

    if new_status is None:

        await query.answer(
            "⚠️ گروه پیدا نشد.",
            show_alert=True,
        )

        return

    await query.answer(
        "🟢 گروه فعال شد."
        if new_status
        else
        "🔴 گروه غیرفعال شد."
    )

    await show_group_details(
        query,
        chat_id,
    )


# =========================================================
# Delete Group Callback
# =========================================================

async def delete_group_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )

        return

    try:

        chat_id = int(
            query.data.split(
                ":",
                1,
            )[1]
        )

    except (
        ValueError,
        IndexError,
    ):

        await query.answer(
            "❌ شناسه نامعتبر است.",
            show_alert=True,
        )

        return

    group = get_group(
        chat_id
    )

    if group is None:

        await query.answer(
            "⚠️ گروه پیدا نشد.",
            show_alert=True,
        )

        return

    title = group.get(
        "title",
        "بدون نام",
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ بله، حذف شود",
                callback_data=(
                    f"confirm_delete:{chat_id}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "❌ لغو",
                callback_data=f"group:{chat_id}",
            )
        ],
    ])

    await query.answer()

    await query.edit_message_text(
        "⚠️ تأیید حذف گروه\n\n"
        f"📌 {title}\n"
        f"🆔 {chat_id}\n\n"
        "آیا مطمئن هستی که می‌خواهی این گروه "
        "از لیست مدیریت حذف شود؟",
        reply_markup=keyboard,
    )


# =========================================================
# Confirm Delete Group
# =========================================================

async def confirm_delete_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )

        return

    try:

        chat_id = int(
            query.data.split(
                ":",
                1,
            )[1]
        )

    except (
        ValueError,
        IndexError,
    ):

        await query.answer(
            "❌ شناسه نامعتبر است.",
            show_alert=True,
        )

        return

    removed = remove_group(
        chat_id
    )

    if removed:

        await query.answer(
            "🗑 گروه حذف شد."
        )

        await query.edit_message_text(
            "✅ گروه با موفقیت حذف شد.\n\n"
            "برای مشاهده لیست جدید، "
            "دوباره «📋 لیست گروه‌ها» را انتخاب کن."
        )

    else:

        await query.answer(
            "⚠️ گروه پیدا نشد.",
            show_alert=True,
        )


# =========================================================
# Refresh Group Callback
# =========================================================

async def refresh_group_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )

        return

    try:

        chat_id = int(
            query.data.split(
                ":",
                1,
            )[1]
        )

    except (
        ValueError,
        IndexError,
    ):

        await query.answer(
            "❌ شناسه نامعتبر است.",
            show_alert=True,
        )

        return

    group = get_group(
        chat_id
    )

    if group is None:

        await query.answer(
            "⚠️ گروه پیدا نشد.",
            show_alert=True,
        )

        return

    try:

        chat = await context.bot.get_chat(
            chat_id
        )

        title = chat.title or "بدون نام"

        update_group_title(
            chat_id,
            title,
        )

        await query.answer(
            "🔄 نام گروه بروزرسانی شد."
        )

        await show_group_details(
            query,
            chat_id,
        )

    except Exception as error:

        logger.error(
            "Failed to refresh group %s: %s",
            chat_id,
            error,
        )

        await query.answer(
            "❌ بروزرسانی انجام نشد.",
            show_alert=True,
        )


# =========================================================
# Group List Callback
# =========================================================

async def group_list_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )

        return

    await query.answer()

    active_groups = get_active_groups()
    disabled_groups = get_disabled_groups()

    all_groups = (
        active_groups
        + disabled_groups
    )

    if not all_groups:

        await query.edit_message_text(
            "📭 هیچ گروهی ثبت نشده است."
        )

        return

    buttons = build_group_buttons(
        all_groups
    )

    await query.edit_message_text(
        "📋 لیست گروه‌ها\n\n"
        "🟢 فعال\n"
        "🔴 غیرفعال\n\n"
        "برای مدیریت گروه انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(
            buttons
        ),
    )


# =========================================================
# Refresh All Groups
# =========================================================

async def refresh_all_groups(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin_update(update):
        return

    if update.message is None:
        return

    active_groups = get_active_groups()
    disabled_groups = get_disabled_groups()

    groups = (
        active_groups
        + disabled_groups
    )

    if not groups:

        await update.message.reply_text(
            "📭 هیچ گروهی برای بروزرسانی وجود ندارد.",
            reply_markup=GROUPS_KEYBOARD,
        )

        return

    updated = 0
    failed = 0

    await update.message.reply_text(
        "🔄 بروزرسانی گروه‌ها شروع شد..."
    )

    for group in groups:

        chat_id = group.get("chat_id")

        if chat_id is None:
            failed += 1
            continue

        try:

            chat = await context.bot.get_chat(
                chat_id
            )

            title = chat.title or "بدون نام"

            if update_group_title(
                chat_id,
                title,
            ):

                updated += 1
            else:

                failed += 1

        except Exception as error:

            failed += 1

            logger.error(
                "Refresh failed for %s: %s",
                chat_id,
                error,
            )

    await update.message.reply_text(
        "✅ بروزرسانی تمام شد.\n\n"
        f"🟢 موفق: {updated}\n"
        f"🔴 ناموفق: {failed}",
        reply_markup=GROUPS_KEYBOARD,
    )


# =========================================================
# Last Report
# =========================================================

async def show_last_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin_update(update):
        return

    if update.message is None:
        return

    report = get_last_report()

    if report is None:

        await update.message.reply_text(
            "📭 هنوز هیچ گزارشی ثبت نشده است.",
            reply_markup=ADMIN_KEYBOARD,
        )

        return

    await update.message.reply_text(
        "📊 آخرین گزارش\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🆔 گزارش: #{report['id']}\n"
        f"🕐 زمان: {report['time']}\n"
        f"📝 کاراکترها: "
        f"{report['message_length']}\n\n"
        f"👥 کل گروه‌ها: "
        f"{report['total_groups']}\n"
        f"🟢 موفق: {report['success']}\n"
        f"🔴 ناموفق: {report['failed']}\n"
        "━━━━━━━━━━━━━━━━━━",
        reply_markup=ADMIN_KEYBOARD,
    )


# =========================================================
# Admin Buttons
# =========================================================

async def admin_buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin_update(update):
        return

    if update.message is None:
        return

    text = update.message.text

    # -----------------------------------------------------
    # Group Management
    # -----------------------------------------------------

    if text == "👥 مدیریت گروه‌ها":

        await show_group_management(
            update,
            context,
        )

        return

    # -----------------------------------------------------
    # Reports
    # -----------------------------------------------------

    if text == "📊 گزارش‌ها":

        await show_last_report(
            update,
            context,
        )

        return

    # -----------------------------------------------------
    # Group List
    # -----------------------------------------------------

    if text == "📋 لیست گروه‌ها":

        await show_groups(
            update,
            context,
        )

        return

    # -----------------------------------------------------
    # Group Statistics
    # -----------------------------------------------------

    if text == "📊 آمار گروه‌ها":

        await show_group_stats(
            update,
            context,
        )

        return

    # -----------------------------------------------------
    # Refresh Groups
    # -----------------------------------------------------

    if text == "🔄 بروزرسانی گروه‌ها":

        await refresh_all_groups(
            update,
            context,
        )

        return

    # -----------------------------------------------------
    # Back
    # -----------------------------------------------------

    if text == "⬅️ بازگشت":

        await update.message.reply_text(
            "🏠 پنل اصلی",
            reply_markup=ADMIN_KEYBOARD,
        )

        return


# =========================================================
# Error Handler
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    logger.error(
        "Unhandled exception:",
        exc_info=context.error,
    )


# =========================================================
# Main
# =========================================================

def main():

    # -----------------------------------------------------
    # Config Validation
    # -----------------------------------------------------

    if (
        not BOT_TOKEN
        or BOT_TOKEN == "YOUR_BOT_TOKEN"
    ):

        raise ValueError(
            "❌ BOT_TOKEN را در config.py وارد کن."
        )

    if ADMIN_ID == 123456789:

        raise ValueError(
            "❌ ADMIN_ID را در config.py وارد کن."
        )

    # -----------------------------------------------------
    # Application
    # -----------------------------------------------------

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # -----------------------------------------------------
    # /start
    # -----------------------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    # -----------------------------------------------------
    # Bot Group Membership
    #
    # ChatMemberHandler.MY_CHAT_MEMBER
    # وضعیت عضویت خود ربات را دریافت می‌کند.
    # -----------------------------------------------------

    application.add_handler(
        ChatMemberHandler(
            my_chat_member_update,
            ChatMemberHandler.MY_CHAT_MEMBER,
        )
    )

    # -----------------------------------------------------
    # Broadcast Conversation
    # -----------------------------------------------------

    broadcast_conversation = ConversationHandler(

        entry_points=[
            MessageHandler(
                filters.Regex(
                    r"^📢 ارسال پیام$"
                ),
                start_broadcast,
            )
        ],

        states={

            WAITING_MESSAGE: [
                MessageHandler(
                    filters.TEXT
                    & ~filters.COMMAND,
                    receive_broadcast_message,
                )
            ],

            CONFIRM_MESSAGE: [
                MessageHandler(
                    filters.TEXT
                    & ~filters.COMMAND,
                    confirm_broadcast,
                )
            ],
        },

        fallbacks=[
            CommandHandler(
                "start",
                start,
            )
        ],

        allow_reentry=True,
    )

    application.add_handler(
        broadcast_conversation
    )

    # -----------------------------------------------------
    # Group Callbacks
    # -----------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            group_callback,
            pattern=r"^group:-?\d+$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            toggle_group_callback,
            pattern=r"^toggle:-?\d+$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            delete_group_callback,
            pattern=r"^delete:-?\d+$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            confirm_delete_callback,
            pattern=r"^confirm_delete:-?\d+$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            refresh_group_callback,
            pattern=r"^refresh:-?\d+$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            group_list_callback,
            pattern=r"^group_list$",
        )
    )

    # -----------------------------------------------------
    # Admin Buttons
    # -----------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            admin_buttons,
        )
    )

    # -----------------------------------------------------
    # Error Handler
    # -----------------------------------------------------

    application.add_error_handler(
        error_handler
    )

    # -----------------------------------------------------
    # Start
    # -----------------------------------------------------

    print(
        "=========================================="
    )

    print(
        " Telegram Broadcast Bot"
    )

    print(
        " Phase 6 - Group Management"
    )

    print(
        "=========================================="
    )

    print(
        "🤖 Bot is running..."
    )

    print(
        "⏹ برای توقف Ctrl+C را بزنید."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# =========================================================
# Entry Point
# =========================================================

if __name__ == "__main__":
    main()
