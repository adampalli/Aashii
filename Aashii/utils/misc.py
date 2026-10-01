"""Miscellaneous functions."""

import logging
import re
import unicodedata
from telegram import Bot, InlineKeyboardMarkup, Update
from telegram.error import Forbidden, TelegramError
from telegram.ext import CallbackContext
from Aashii.constants import Button, Literal, Media, Message

_p = re.compile("<[^>]*>")

# Fancy-font Latin used in usernames and promos, e.g. "𝐇𝐞𝐥𝐥𝐨" or "ℌ".
_FANCY_LATIN = (range(0x2100, 0x2150), range(0x1D400, 0x1D6A4))
# Combining accents used by Latin text written in decomposed form, plus the
# marks emoji are built from (keycaps, variation selectors, flag tags).
_LATIN_MARKS = (
    range(0x0300, 0x0370),
    range(0x1AB0, 0x1B00),
    range(0x1DC0, 0x1E00),
    range(0x20D0, 0x2100),
    range(0xFE00, 0xFE10),
    range(0xE0000, 0xE0200),
)


def _is_latin_char(char: str) -> bool:
    """Return False if the character is a letter, mark or digit of a non-Latin script."""
    category = unicodedata.category(char)
    code = ord(char)

    if category.startswith("L"):
        name = unicodedata.name(char, "")
        if "LATIN" in name or char in "ªº" or any(code in r for r in _FANCY_LATIN):
            return True
        return category == "Lm" and name.startswith("MODIFIER LETTER")

    if category.startswith("M"):
        return any(code in r for r in _LATIN_MARKS)

    if category == "Nd":
        return code < 0x80 or "MATHEMATICAL" in unicodedata.name(char, "")

    # Punctuation, spaces, symbols and emoji are script-neutral.
    return True


def is_latin_text(text: str) -> bool:
    """Return True if text uses only the Latin script (English, Italian, French...)."""
    return all(_is_latin_char(char) for char in text or "")


async def add_user(update: Update, context: CallbackContext):
    """Add or update the user to database."""
    if not update.effective_message:
        return

    database = context.bot_data["database"]
    user = update.effective_message.from_user
    user_id = user.id
    full_name = user.full_name
    username = f"@{user.username}" if user.username else None
    database.add_user(user_id, username, full_name)


async def block_user(user_id: int, context: CallbackContext):
    """Blocks the user from contacting admins and informs the user."""
    database = context.bot_data["database"]
    database.set_user_blocked(user_id, True)
    try:
        msg = await context.bot.send_photo(
            photo=Media.BLOCKED_USER,
            chat_id=user_id,
            caption=Message.BLOCKED_USER_STATUS,
        )
    except Forbidden:
        return 0
    else:
        return msg.message_id


def dehtml(text: str):
    """Return deHTMLed string from given text."""
    return _p.sub("", text)


async def error_handler(_: object, context: CallbackContext):
    """Log errors raised by handlers, with their traceback."""
    logging.error("Error while handling an update", exc_info=context.error)


async def get_membership(user_id: int, bot: Bot):
    """Return membership of user."""
    try:
        mem = await bot.get_chat_member(Literal.CHAT_GROUP_ID, user_id)
    except TelegramError as e:
        logging.warning("Could not get membership of %s: %s", user_id, e)
        membership = Message.FALLBACK_STATUS
    else:
        membership = mem.status.title()

    return membership


def get_user_src_message(update: Update, context: CallbackContext):
    """Return user ID and source message ID if the message is a reply to user's message."""
    database = context.bot_data["database"]
    message = update.effective_message
    reply = message.reply_to_message
    user_id, src_msg_id = None, None

    if not reply:
        user_id, src_msg_id = database.get_user_message_id_from_users(
            message.message_id
        )
    elif reply.from_user.id == context.bot.id:
        user_id, src_msg_id = database.get_user_message_id_from_users(reply.message_id)
    else:
        user_id, src_msg_id = database.get_user_dest_message_id_from_admins(
            reply.message_id
        )
    return (user_id, src_msg_id)


async def request_join(update: Update, context: CallbackContext):
    """Send a message in admins group to request addition in chat group."""
    database = context.bot_data["database"]
    user = update.chat_join_request.from_user
    user_id = user.id
    username = f"@{user.username}" if user.username else None
    # Join requests carry no message, so add_user has not stored this user yet.
    database.add_user(user_id, username, user.full_name)
    blocked = database.get_user_blocked(user_id)

    if blocked:
        await context.bot.decline_chat_join_request(Literal.CHAT_GROUP_ID, user_id)
        database.set_user_decision_status(user_id, "declined")
        return

    context.bot_data.pop("lastUserId", None)
    full_name = user.full_name
    last_message_id = database.get_last_user_message_id(user_id)
    text = Message.JOIN_REQUEST.format(
        FULL_NAME=full_name,
        USER_ID=user_id,
        USERNAME=username,
        BLOCKED=blocked,
    )
    markup = InlineKeyboardMarkup([[Button.APPROVE, Button.DECLINE]])

    dest = await context.bot.send_message(
        chat_id=Literal.ADMINS_GROUP_ID,
        text=text,
        reply_markup=markup,
        reply_to_message_id=last_message_id,
    )
    database.set_invite_pending(user_id, True)
    database.add_user_message(last_message_id, user_id, dest.message_id)


async def unblock_user(user_id: int, context: CallbackContext):
    """Unblock the user from contacting admins and informs the user."""
    database = context.bot_data["database"]
    database.set_user_blocked(user_id, False)
    try:
        msg = await context.bot.send_message(
            chat_id=user_id,
            text=Message.UNBLOCKED_USER_STATUS,
        )
    except Forbidden:
        return 0
    else:
        return msg.message_id
