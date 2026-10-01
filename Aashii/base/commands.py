"""Contains handlers related to commands."""

from pathlib import Path
from telegram import ChatMember, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import CallbackContext
from Aashii.constants import Button, Literal, Media, Message
from Aashii.utils.broadcast import announce
from Aashii.utils.misc import (
    block_user,
    get_membership,
    get_user_src_message,
    unblock_user,
)
from Aashii.utils.wrappers import (
    check_is_group_command,
    check_is_reply_verbose,
    check_user_status,
)

STATIC_DIR = Path("data/static")


@check_is_group_command
@check_is_reply_verbose
async def announce_users(update: Update, context: CallbackContext):
    """Announce the replied message to every user in database."""
    if context.bot_data.get("announcement"):
        await update.message.reply_html(Message.ANNOUNCEMENT_IN_DUE)
        return

    database = context.bot_data["database"]
    context.bot_data["announcement"] = update.message.reply_to_message
    context.bot_data["sent"] = context.bot_data["failed"] = 0
    context.bot_data["users"], context.bot_data["total"] = database.get_users()
    step = context.bot_data["total"] // Literal.STEP
    context.bot_data["steps"] = [(step * i) for i in range(1, Literal.STEP + 1)]
    text = Message.ANNOUNCEMENT_INIT.format(TOTAL=context.bot_data["total"])
    context.bot_data["log_message"] = await update.message.reply_html(text)
    context.job_queue.run_repeating(
        announce, interval=Literal.ANNOUNCEMENT_INTERVAL, name="announcement"
    )


@check_is_group_command
async def block_user_cl(update: Update, context: CallbackContext):
    """Block the user from contacting the admins based on command."""
    database = context.bot_data["database"]

    if context.args and context.args[0].isdigit():
        user_id = int(context.args[0])
    else:
        user_id, _ = get_user_src_message(update, context)
        if not user_id:
            await update.message.reply_html(Message.INVALID_REPLY)
            return

    msg_id = await block_user(user_id, context)

    full_name = database.get_user_full_name(user_id)
    text = Message.BLOCKED_USER.format(USER_ID=user_id, FULL_NAME=full_name)
    message = await update.message.reply_html(text)
    database.add_admin_message(update.message.message_id, user_id, msg_id)
    database.add_user_message(1, user_id, message.message_id)


@check_is_group_command
async def cancel_announcement(update: Update, context: CallbackContext):
    """Cancel an announcement if scheduled."""
    if context.bot_data.pop("announcement", None):
        job = context.job_queue.get_jobs_by_name("announcement")[0]
        job.schedule_removal()
        log_message = context.bot_data.pop("log_message")
        sent = context.bot_data.pop("sent")
        failed = context.bot_data.pop("failed")
        total = context.bot_data.pop("total")
        percent = int(((sent + failed) / max(total, 1)) * 100)
        edit_text = Message.ANNOUNCEMENT_CANCELLED.format(
            SENT=sent, FAILED=failed, PROGRESS=percent
        )
        text = Message.CANCELLED_ANNOUNCEMENT.format(PROGRESS=percent)
        await log_message.edit_text(edit_text)
        del context.bot_data["users"]
    else:
        text = Message.NO_ANNOUNCEMENT

    await update.message.reply_html(text)


@check_is_group_command
@check_is_reply_verbose
async def delete(update: Update, context: CallbackContext):
    """Delete the message sent by admins to users."""
    database = context.bot_data["database"]
    reply = update.message.reply_to_message

    user_id, dest_msg_id = database.get_user_dest_message_id_from_admins(
        reply.message_id
    )

    if user_id:
        try:
            await context.bot.delete_message(user_id, dest_msg_id)
        except TelegramError:
            await update.message.reply_html(Message.DELETE_FAILED)
        else:
            await update.message.reply_html(Message.DELETE_DONE)
    else:
        await update.message.reply_html(Message.NOT_LINKED)


@check_user_status
async def invite_user(update: Update, context: CallbackContext):
    """Invite user to group and handle other use cases."""
    database = context.bot_data["database"]
    user_id = update.message.from_user.id
    chat_mem = await context.bot.get_chat_member(Literal.CHAT_GROUP_ID, user_id)
    in_group = chat_mem.status in (
        ChatMember.ADMINISTRATOR,
        ChatMember.OWNER,
        ChatMember.MEMBER,
    )
    is_restricted = chat_mem.status == ChatMember.RESTRICTED
    is_kicked = chat_mem.status == ChatMember.BANNED

    if in_group:
        await update.message.reply_html(Message.ALREADY_IN_GROUP)
    elif is_kicked:
        await update.message.reply_html(Message.KICKED_IN_GROUP)
    elif is_restricted:
        await update.message.reply_html(Message.MUTED_IN_GROUP)
    else:
        count = database.get_invite_links_count(user_id)
        if count < Literal.MAX_INVITE_LINKS:
            await static_command(update, context)
            context.user_data["expectInviteAnswers"] = True
        else:
            await update.message.reply_html(Message.EXHAUSTED_INVITE_LINKS)


@check_is_group_command
async def reset(update: Update, context: CallbackContext):
    """Reset count of invite links for a user."""
    database = context.bot_data["database"]

    if context.args and context.args[0].isdigit():
        user_id = int(context.args[0])
    else:
        user_id, _ = get_user_src_message(update, context)
        if not user_id:
            await update.message.reply_html(Message.INVALID_REPLY)
            return

    database.reset_invite_links(user_id)
    full_name = database.get_user_full_name(user_id)
    text = Message.RESET_COUNT.format(FULL_NAME=full_name, USER_ID=user_id)
    src_msg = await context.bot.send_message(
        chat_id=user_id, text=Message.INVITE_LINKS_RESET
    )
    dst_msg = await update.effective_message.reply_html(text)
    src_msg_id, dst_msg_id = src_msg.message_id, dst_msg.message_id
    database.add_user_message(src_msg_id, user_id, dst_msg_id)


async def send_help(update: Update, context: CallbackContext):
    """Send the bot's usage guide intended for private or\
    group depending upon the place of invocation."""
    if update.message.chat.type == update.message.chat.PRIVATE:
        await update.message.reply_photo(
            photo=Media.HELP_PRIVATE,
            caption=Message.HELP_PRIVATE.format(GROUP_NAME=Literal.GROUP_NAME),
        )
    else:
        await update.message.reply_html(text=Message.HELP_GROUP)
        context.bot_data["lastUserId"] = Literal.ADMINS_GROUP_ID


@check_user_status
async def send_start(update: Update, context: CallbackContext):
    """Connect the user with admins group in case of private chat,\
    else show the bot's description."""
    context.bot_data.pop("lastUserId", None)
    if update.message.chat.type != update.message.chat.PRIVATE:
        await update.message.reply_html(Message.START_GROUP)
        return

    buttons = [Button.BLOCK, Button.CONNECT]
    database = context.bot_data["database"]
    keyboard = InlineKeyboardMarkup.from_row(buttons)
    user = update.message.from_user
    user_id = user.id
    full_name = user.full_name
    membership = await get_membership(user_id, context.bot)
    username = f"@{user.username}" if user.username else None
    text = Message.USER_CONNECTED.format(
        FULL_NAME=full_name,
        USER_ID=user_id,
        USERNAME=username,
        MEMBERSHIP=membership,
        BLOCKED=False,
    )

    await update.message.reply_photo(
        photo=Media.START_PRIVATE,
        caption=Message.START_PRIVATE.format(GROUP_NAME=Literal.GROUP_NAME),
    )
    message = await context.bot.send_message(
        chat_id=Literal.ADMINS_GROUP_ID,
        text=text,
        reply_markup=keyboard,
    )
    database.add_user_message(update.message.message_id, user_id, message.message_id)


async def static_command(update: Update, context: CallbackContext):
    """Send static command mentioned in static folder."""
    command = update.message.text.split()[0][1:].split("@")[0]
    static_files = {path.name for path in STATIC_DIR.iterdir() if path.is_file()}

    if command in static_files:
        text = (STATIC_DIR / command).read_text(encoding="utf-8")
        await update.message.reply_html(text)
    else:
        await update.message.reply_html(Message.INVALID_COMMAND)

    if update.message.chat.type != update.message.chat.PRIVATE:
        context.bot_data["lastUserId"] = Literal.ADMINS_GROUP_ID


@check_is_group_command
async def unblock_user_cl(update: Update, context: CallbackContext):
    """Unblock the user from contacting the admins based on command."""
    database = context.bot_data["database"]

    if context.args and context.args[0].isdigit():
        user_id = int(context.args[0])
    else:
        user_id, _ = get_user_src_message(update, context)
        if not user_id:
            await update.message.reply_html(Message.INVALID_REPLY)
            return

    msg_id = await unblock_user(user_id, context)

    full_name = database.get_user_full_name(user_id)
    text = Message.UNBLOCKED_USER.format(USER_ID=user_id, FULL_NAME=full_name)
    message = await update.message.reply_html(text)
    database.add_admin_message(update.message.message_id, user_id, msg_id)
    database.add_user_message(1, user_id, message.message_id)


LIST_USERS_LIMIT = 50


@check_is_group_command
async def list_users(update: Update, context: CallbackContext):
    """List blocked/approved/declined users."""
    database = context.bot_data["database"]
    category = context.args[0].lower() if context.args else "all"

    if category == "blocked":
        users = database.get_users_by_blocked(True, LIST_USERS_LIMIT)
        heading = Message.LIST_BLOCKED_USERS
    elif category == "approved":
        users = database.get_users_by_decision_status("approved", LIST_USERS_LIMIT)
        heading = Message.LIST_APPROVED_USERS
    elif category == "declined":
        users = database.get_users_by_decision_status("declined", LIST_USERS_LIMIT)
        heading = Message.LIST_DECLINED_USERS
    elif category == "all":
        await _reply_user_list(
            update,
            Message.LIST_BLOCKED_USERS,
            database.get_users_by_blocked(True, LIST_USERS_LIMIT),
        )
        await _reply_user_list(
            update,
            Message.LIST_APPROVED_USERS,
            database.get_users_by_decision_status("approved", LIST_USERS_LIMIT),
        )
        await _reply_user_list(
            update,
            Message.LIST_DECLINED_USERS,
            database.get_users_by_decision_status("declined", LIST_USERS_LIMIT),
        )
        return
    else:
        await update.message.reply_html(Message.LIST_USERS_USAGE)
        return

    await _reply_user_list(update, heading, users)


async def _reply_user_list(update: Update, heading, users):
    lines = [heading]
    lines.extend(_format_users(users))
    await update.message.reply_html("\n".join(lines))


def _format_users(users):
    if not users:
        return [Message.LIST_USERS_EMPTY]

    return [
        Message.LIST_USERS_ENTRY.format(
            USER_ID=user_id,
            FULL_NAME=full_name,
            USERNAME=username or "-",
        )
        for (user_id, username, full_name) in users
    ]


@check_is_group_command
async def whois(update: Update, context: CallbackContext):
    """Get information about user replied to or given as argument."""
    database = context.bot_data["database"]

    if context.args and context.args[0].isdigit():
        user_id = int(context.args[0])
    else:
        user_id, _ = get_user_src_message(update, context)
        if not user_id:
            await update.message.reply_html(Message.INVALID_REPLY)
            return

    username, full_name, blocked = database.get_user(user_id)
    membership = await get_membership(user_id, context.bot)
    text = Message.USER.format(
        FULL_NAME=full_name,
        USER_ID=user_id,
        USERNAME=username,
        MEMBERSHIP=membership,
        BLOCKED=blocked,
    )
    await update.effective_message.reply_html(text)
