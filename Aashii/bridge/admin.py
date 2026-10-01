"""Contains functions to send messages from admins to users."""

from telegram import Message as TMessage, Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext
from Aashii.constants import Literal
from Aashii.utils.misc import get_user_src_message
from Aashii.utils.transfer import send_edited_message, send_message
from Aashii.utils.wrappers import check_is_blocked_by_user


def _dereply_character(message: TMessage):
    """Return a copy of the message without the leading reply character."""
    data = message.to_dict()
    key, entities_key = (
        ("caption", "caption_entities") if message.caption else ("text", "entities")
    )
    data[key] = data[key][len(Literal.REPLY_CHARACTER) :]
    # Entity offsets are counted in UTF-16 code units.
    shift = len(Literal.REPLY_CHARACTER.encode("utf-16-le")) // 2
    entities = []

    for entity in data.get(entities_key, []):
        start = max(entity["offset"] - shift, 0)
        end = entity["offset"] + entity["length"] - shift
        if end > start:
            entities.append({**entity, "offset": start, "length": end - start})

    data[entities_key] = entities
    return TMessage.de_json(data, message.get_bot())


def _get_legit_reply(message: TMessage, context: CallbackContext):
    """Return the message to send to the user, or None if it should not be sent."""
    textual = message.caption or message.text or ""
    should_reply = textual.startswith(Literal.REPLY_CHARACTER)
    reply_to_admins = message.reply_to_message.from_user.id != context.bot.id

    if not reply_to_admins:
        return message

    if should_reply:
        return _dereply_character(message)

    return None


async def _send_users(context: CallbackContext):
    database = context.bot_data["database"]
    message, user_id, reply_to = context.job.data
    dest_msg_ids = await send_message(
        context.bot, message, user_id, reply_to, True, False
    )
    database.add_admin_message(message.message_id, user_id, dest_msg_ids[0])


@check_is_blocked_by_user
async def edit_admin_message(update: Update, context: CallbackContext):
    """Edit the message of admins sent to user."""
    database = context.bot_data["database"]
    message_id = update.edited_message.message_id
    user_id, dest_message_id = database.get_user_dest_message_id_from_admins(message_id)
    message = _get_legit_reply(update.edited_message, context)

    if not message:
        return

    if user_id:
        await send_edited_message(
            context.bot, message, dest_message_id, user_id, False
        )
    else:
        user_id, reply_to = get_user_src_message(update, context)
        context.job_queue.run_once(
            callback=_send_users,
            when=Literal.DELAY_SECONDS,
            data=(message, user_id, reply_to),
        )


@check_is_blocked_by_user
async def forward_to_user(update: Update, context: CallbackContext):
    """Send the message from admins to the user."""
    context.bot_data.pop("lastUserId", None)
    if not update.message.reply_to_message:
        return
    user_id, reply_to = get_user_src_message(update, context)
    message = _get_legit_reply(update.message, context)

    if not (message and user_id):
        return

    await context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
    context.job_queue.run_once(
        callback=_send_users,
        when=Literal.DELAY_SECONDS,
        data=(message, user_id, reply_to),
    )
