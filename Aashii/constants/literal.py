"""Contains Literal object."""

import os


class Literal:
    """Lieral contains values that are simple and never change, like admins' group ID."""

    ADMINS_GROUP_ID = int(os.getenv("ADMINS_GROUP_ID"))

    ANNOUNCEMENT_INTERVAL = float(os.getenv("ANNOUNCEMENT_INTERVAL", "0.5"))

    CHAT_GROUP_ID = int(os.getenv("CHAT_GROUP_ID"))

    DELAY_SECONDS = int(os.getenv("DELAY_SECONDS", "3"))

    FLOOD_LIMIT = int(os.getenv("FLOOD_LIMIT", "10"))

    FLOOD_WINDOW = int(os.getenv("FLOOD_WINDOW", "60"))

    GROUP_NAME = os.getenv("GROUP_NAME", "A GRoUP Of eBooKz®")

    MAX_INVITE_LINKS = int(os.getenv("MAX_INVITE_LINKS", "1"))

    NOTICE_INTERVAL = int(os.getenv("NOTICE_INTERVAL", "600"))

    REPLY_CHARACTER = os.getenv("REPLY_CHARACTER", "!")

    STEP = int(os.getenv("STEP", "10"))

