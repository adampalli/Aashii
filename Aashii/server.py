"""Contains the Server object."""

import logging

# import sentry_sdk
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, Defaults

from Aashii.constants import Scope
from Aashii.utils.database import Database
from Aashii.utils.misc import error_handler

# sentry_sdk.init(
#     "https://c2099f5cd64c41f0aa071d8e0844a7e8@o915566.ingest.sentry.io/5857817",
#     # Set traces_sample_rate to 1.0 to capture 100%
#     # of transactions for performance monitoring.
#     # We recommend adjusting this value in production.
#     release="BookCrushContactBot@2.0.1",
#     traces_sample_rate=0.7,
#     debug=False,
# )

ALLOWED_UPDATES = [
    Update.CALLBACK_QUERY,
    Update.CHAT_JOIN_REQUEST,
    Update.EDITED_MESSAGE,
    Update.MESSAGE,
]


class Server:
    """Server takes care of setting up the bot, handlers and getting updates."""

    def __init__(self, token: str, commands: dict, database_url: str, handlers: dict):
        """Create a new Server."""
        defaults = Defaults(parse_mode=ParseMode.HTML, allow_sending_without_reply=True)
        self.commands = commands
        self.application = (
            Application.builder()
            .token(token)
            .defaults(defaults)
            .post_init(self._setup_commands)
            .post_shutdown(self._shutdown)
            .build()
        )
        self.database = Database(database_url)
        self.application.bot_data["database"] = self.database
        self._setup_handlers(handlers)

    async def _setup_commands(self, application: Application):

        admins = self.commands["admins"] + self.commands["all"]
        private = self.commands["private"] + self.commands["all"]
        await application.bot.set_my_commands(admins, scope=Scope.ADMINS)
        await application.bot.set_my_commands(private, scope=Scope.PRIVATE)

    def _setup_handlers(self, handlers: dict):

        for handler_type, handles in handlers.items():
            for handle in handles:
                h_kwargs, d_args = handle[0], handle[1:]
                handler = handler_type(**h_kwargs)
                self.application.add_handler(handler, *d_args)

        self.application.add_error_handler(error_handler)

    def listen(self, listen: str, port: int, url: str, url_path: str):
        """Listen for incoming webhook updates."""
        logging.info("Started listening ...")
        self.application.run_webhook(
            listen=listen,
            port=port,
            url_path=url_path,
            webhook_url=f"{url}/{url_path}",
            allowed_updates=ALLOWED_UPDATES,
        )

    def poll(self, poll_interval: int = 0):
        """Poll for new updates."""
        logging.info("Started polling ...")
        self.application.run_polling(
            poll_interval=poll_interval,
            allowed_updates=ALLOWED_UPDATES,
        )

    async def _shutdown(self, _: Application):
        """Clean up resources and sign off."""
        self.database.connection.close()
        logging.info("Got an interruption, bye.")
