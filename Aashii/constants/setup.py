"""Runtime setup configuration loaded from JSON."""

import json
import os
from pathlib import Path


CONFIG_PATH = Path(os.getenv("BOT_CONFIG_PATH", "data/setup/bot-config.json"))

with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
    BOT_SETUP = json.load(config_file)

MESSAGES = BOT_SETUP["messages"]
IMAGES = BOT_SETUP["images"]
COMMAND_DESCRIPTIONS = BOT_SETUP["command_descriptions"]
LABELS = BOT_SETUP["labels"]
