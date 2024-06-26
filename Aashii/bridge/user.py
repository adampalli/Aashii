"""Contains functions to send messages from users to admins."""

from datetime import datetime, timedelta
from telegram import ChatAction, Update
from telegram.ext import CallbackContext
from Aashii.constants import Literal, Message
from Aashii.utils.transfer import send_edited_message, send_message
from Aashii.utils.wrappers import check_user_status


def _send_admins(context: CallbackContext):
    database = context.bot_data["database"]
    update, context = context.job.context
    message = update.message
    user_id = message.from_user.id
    quote = context.bot_data.get("lastUserId", 0) != user_id
    reply = message.reply_to_message
    reply_to = None

    if reply:
        if reply.from_user.id == user_id:
            reply_to = database.get_dest_message_id_from_users(
                user_id, reply.message_id
            )
        else:
            reply_to = database.get_message_id_from_admins(user_id, reply.message_id)

    dest_msgs = send_message(
        context.bot, message, Literal.ADMINS_GROUP_ID, reply_to, False, quote
    )

    for dest_msg_id in dest_msgs:
        database.add_user_message(message.message_id, user_id, dest_msg_id)

    context.bot_data["lastUserId"] = user_id

    if context.user_data.pop("expectInviteAnswers", False):
        _send_invite_link(update, context)


def _send_invite_link(update: Update, context: CallbackContext):
    database = context.bot_data["database"]
    user_id = update.message.from_user.id
    expire = datetime.today() + timedelta(days=0, minutes=10)
    link = context.bot.create_chat_invite_link(
        chat_id=Literal.CHAT_GROUP_ID, expire_date=expire, creates_join_request=True
    )
    text = Message.CHAT_LINK_INFO.format(LINK=link.invite_link)
    msg_id = update.message.reply_html(text).message_id
    database.add_invite_link(user_id, msg_id)


@check_user_status
def edit_user_message(update: Update, context: CallbackContext):
    """Edit the message of user sent to admins."""
    database = context.bot_data["database"]
    user_id = update.edited_message.from_user.id
    message_id = update.edited_message.message_id
    dest_message_id = database.get_dest_message_id_from_users(user_id, message_id)
    new_dest_id = send_edited_message(
        context.bot,
        update.edited_message,
        dest_message_id,
        Literal.ADMINS_GROUP_ID,
        True,
    )

    if new_dest_id:
        database.add_user_message(message_id, user_id, new_dest_id)


@check_user_status
def forward_to_admins(update: Update, context: CallbackContext):
    """Send the user's message to admins."""
    context.bot.send_chat_action(
        chat_id=Literal.ADMINS_GROUP_ID, action=ChatAction.TYPING
    )
    context.job_queue.run_once(
        callback=_send_admins, when=Literal.DELAY_SECONDS, context=(update, context)
    )
