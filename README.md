# Aashii (Telegram bridge bot)

This bot is a fork of https://github.com/j-arun-mani/Aashii.

## Initial setup

- Copy `data/setup/bot-config.example.json` to `data/setup/bot-config.json`.
- Customize all user-facing text, command descriptions, and image URLs in that file.
- Optionally set `BOT_CONFIG_PATH` to load config from a different location.

## Deployment guides

- [Host on Oracle Cloud Always Free](docs/oracle-cloud-always-free.md)
## Admin moderation commands

- `/listusers blocked` — list the latest 50 blocked users.
- `/listusers approved` — list the latest 50 users whose join requests were approved.
- `/listusers declined` — list the latest 50 users whose join requests were declined.
- `/listusers all` — print the latest 50 blocked, approved, and declined users.

> If you are upgrading an existing deployment, run `data/migrate.sql` so the `users.decision_status` column exists before using these filters.
