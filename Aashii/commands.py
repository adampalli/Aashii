"""Contains commands used by the bot."""

from telegram import BotCommand
from Aashii.constants.setup import COMMAND_DESCRIPTIONS
from Aashii.utils.misc import dehtml


def _command(fname):
    cmd = fname
    with open(f"data/static/{fname}", "r") as staticfp:
        dsc = dehtml(staticfp.read(80)) + "…"
    return BotCommand(cmd, dsc)


commands = {
    "admins": [
        BotCommand("announce", COMMAND_DESCRIPTIONS["announce"]),
        BotCommand("block", COMMAND_DESCRIPTIONS["block"]),
        BotCommand("cancel", COMMAND_DESCRIPTIONS["cancel"]),
        BotCommand("delete", COMMAND_DESCRIPTIONS["delete"]),
        BotCommand("reset", COMMAND_DESCRIPTIONS["reset"]),
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
