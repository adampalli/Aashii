"""Contains commands used by the bot."""

from telegram import BotCommand
from Aashii.constants.setup import COMMAND_DESCRIPTIONS


commands = {
    "admins": [
        BotCommand("announce", COMMAND_DESCRIPTIONS["announce"]),
        BotCommand("block", COMMAND_DESCRIPTIONS["block"]),
        BotCommand("cancel", COMMAND_DESCRIPTIONS["cancel"]),
        BotCommand("delete", COMMAND_DESCRIPTIONS["delete"]),
        BotCommand("listusers", COMMAND_DESCRIPTIONS["listusers"]),
        BotCommand("reset", COMMAND_DESCRIPTIONS["reset"]),
        BotCommand("stats", COMMAND_DESCRIPTIONS["stats"]),
        BotCommand("unblock", COMMAND_DESCRIPTIONS["unblock"]),
        BotCommand("whois", COMMAND_DESCRIPTIONS["whois"]),
    ],
    "all": [
        BotCommand("help", COMMAND_DESCRIPTIONS["help"]),
        BotCommand("start", COMMAND_DESCRIPTIONS["start"]),
    ],
    "private": [
        ("invite", COMMAND_DESCRIPTIONS["invite"]),
        ("query", COMMAND_DESCRIPTIONS["query"]),
    ],
}
