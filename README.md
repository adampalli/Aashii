# Aashii (Telegram bridge bot)

This bot is a fork of https://github.com/j-arun-mani/Aashii.

## Initial setup

- Copy `data/setup/bot-config.example.json` to `data/setup/bot-config.json`.
- Customize all user-facing text, command descriptions, and image URLs in that file.
- Optionally set `BOT_CONFIG_PATH` to load config from a different location.

## Deployment guides

- [Host on Oracle Cloud Always Free](docs/oracle-cloud-always-free.md)


## Admin moderation commands

- `/listusers blocked` — list all blocked users.
- `/listusers approved` — list users whose join requests were approved.
- `/listusers declined` — list users whose join requests were declined.
- `/listusers all` — print blocked, approved, and declined sections together.

> If you are upgrading an existing deployment, run `data/migrate.sql` so the `users.decision_status` column exists before using these filters.
