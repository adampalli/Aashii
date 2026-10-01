"""Containts Scope object."""

from telegram import BotCommandScopeAllPrivateChats, BotCommandScopeChat
from .literal import Literal


class Scope:
    """Represents the various supported command scopes."""

    ADMINS = BotCommandScopeChat(Literal.ADMINS_GROUP_ID)
    PRIVATE = BotCommandScopeAllPrivateChats()
