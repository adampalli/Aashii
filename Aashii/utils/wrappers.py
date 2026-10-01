"""Wrappers for various handlers."""

import time
from collections import deque
from functools import wraps
from telegram import Update
from telegram.error import Forbidden
from telegram.ext import CallbackContext
from Aashii.constants import Literal, Message
from Aashii.utils.misc import get_user_src_message, is_latin_text


def check_is_blocked_by_user(func):
    """Check if the bot is blocked by the user."""

    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext):
        database = context.bot_data["database"]

        try:
            await func(update, context)
        except Forbidden:
            user_id, _ = get_user_src_message(update, context)
            full_name = database.get_user_full_name(user_id)
            text = Message.BLOCKED_BY_USER.format(USER_ID=user_id, FULL_NAME=full_name)
            msg = await update.effective_message.reply_html(text)
            database.add_user_message(1, user_id, msg.message_id)

        context.bot_data["lastUserId"] = Literal.ADMINS_GROUP_ID

    return wrapped


def check_is_group_command(func):
    """Check if the command is sent in group."""

    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext):
        message = update.edited_message or update.message
        if message.chat.type != message.chat.PRIVATE:
            await func(update, context)
            context.bot_data["lastUserId"] = Literal.ADMINS_GROUP_ID
        else:
            await message.reply_html(Message.NOT_PRIVATE_COMMAND)

    return wrapped


def check_is_reply_verbose(func):
    """Check if the message is a reply to any message and warns on otherwise."""

    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext):
        message = update.edited_message or update.message
        reply = message.reply_to_message
        if reply:
            await func(update, context)
        else:
            await message.reply_html(Message.INVALID_REPLY)

    return wrapped


async def _notice_once(message, context: CallbackContext, key: str, text: str):
    """Reply with a notice, at most once per NOTICE_INTERVAL for each kind."""
    now = time.monotonic()
    last = context.user_data.get(key)
    if last is None or now - last >= Literal.NOTICE_INTERVAL:
        context.user_data[key] = now
        await message.reply_html(text)


def check_flood(func):
    """Drop messages from users who send more than FLOOD_LIMIT per FLOOD_WINDOW."""

    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext):
        message = update.edited_message or update.message
        album = message.media_group_id
        # An album arrives as one message per photo, so count it only once.
        if not album or album != context.user_data.get("lastAlbumId"):
            now = time.monotonic()
            recent = context.user_data.setdefault("recentMessages", deque())
            while recent and now - recent[0] >= Literal.FLOOD_WINDOW:
                recent.popleft()

            if len(recent) >= Literal.FLOOD_LIMIT:
                await _notice_once(
                    message, context, "floodNoticeAt", Message.FLOOD_NOTICE
                )
                return

            recent.append(now)

        context.user_data["lastAlbumId"] = album
        await func(update, context)

    return wrapped


def check_latin_text(func):
    """Drop messages whose text or caption uses a non-Latin script and tell the user."""

    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext):
        message = update.edited_message or update.message
        if is_latin_text(message.text or message.caption):
            await func(update, context)
        else:
            await _notice_once(
                message, context, "latinNoticeAt", Message.NON_LATIN_NOTICE
            )

    return wrapped


def check_user_status(func):
    """Check if the user is blocked and ignores the message if they are."""

    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext):
        database = context.bot_data["database"]
        message = update.edited_message or update.message
        chat = message.chat
        user_id = message.from_user.id

        if chat.type == chat.PRIVATE and database.get_user_blocked(user_id):
            await message.reply_html(Message.BLOCKED_USER_STATUS)
        else:
            await func(update, context)

    return wrapped
