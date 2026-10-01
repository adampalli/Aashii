CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    full_name TEXT NOT NULL,
    blocked BOOL DEFAULT FALSE NOT NULL,
    decision_status TEXT DEFAULT 'unknown' NOT NULL
);

CREATE TABLE IF NOT EXISTS from_admins (
    message_id INTEGER NOT NULL,
    user_id BIGINT REFERENCES users,
    dest_message_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS from_users (
    user_id BIGINT REFERENCES users,
    message_id INTEGER NOT NULL,
    dest_message_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS invite_links (
    user_id BIGINT PRIMARY KEY REFERENCES users,
    message_id INTEGER NOT NULL,
    links_count INTEGER NOT NULL DEFAULT 1,
    pending BOOL NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS from_users_dest_message_id ON from_users (dest_message_id);
CREATE INDEX IF NOT EXISTS from_users_user_message ON from_users (user_id, message_id);
CREATE INDEX IF NOT EXISTS from_admins_message_id ON from_admins (message_id);
CREATE INDEX IF NOT EXISTS from_admins_user_dest_message ON from_admins (user_id, dest_message_id);
