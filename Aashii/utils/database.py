"""Module containing Database object."""

import psycopg2
from Aashii.constants import Query


class Database:
    """A common interface for all database interactions."""

    def __init__(self, database_url: str):
        """Initialize the PostgreSQL database connection."""
        self.connection = psycopg2.connect(database_url)

    def __del__(self):
        """Close the connection automatically when the reference count drops to zero."""
        self.connection.close()

    def add_admin_message(self, message_id: int, user_id: int, dest_message_id: int):
        """Add the message from admins to the database."""
        cur = self.connection.cursor()
        cur.execute(
            Query.ADD_ADMIN_MESSAGE,
            {
                "message_id": message_id,
                "user_id": user_id,
                "dest_message_id": dest_message_id,
            },
        )
        self.connection.commit()
        cur.close()

    def add_invite_link(self, user_id: int, message_id: int):
        """Add message with invite link generated for given user."""
        cur = self.connection.cursor()
        cur.execute(
            Query.ADD_INVITE_LINK,
            {
                "user_id": user_id,
                "message_id": message_id,
            },
        )
        self.connection.commit()
        cur.close()

    def add_user(self, user_id: int, username: str, full_name: str):
        """Add the user with unblocked status."""
        cur = self.connection.cursor()
        cur.execute(
            Query.ADD_USER,
            {"user_id": user_id, "username": username, "full_name": full_name},
        )
        self.connection.commit()
        cur.close()

    def add_user_message(self, message_id: int, user_id: int, dest_message_id: int):
        """Add the message from user to the database."""
        cur = self.connection.cursor()
        cur.execute(
            Query.ADD_USER_MESSAGE,
            {
                "message_id": message_id,
                "user_id": user_id,
                "dest_message_id": dest_message_id,
            },
        )
        self.connection.commit()
        cur.close()

    def get_last_user_message_id(self, user_id: int):
        """Get the latest message from given user."""
        cur = self.connection.cursor()
        cur.execute(Query.GET_LAST_USER_MESSAGE_ID, {"user_id": user_id})
        (message_id,) = next(cur, (0,))
        cur.close()
        return message_id

    def get_user(self, user_id: int):
        """Get the details of given user."""
        cur = self.connection.cursor()
        cur.execute(Query.GET_USER, {"user_id": user_id})
        (username, full_name, blocked) = next(cur, (None, None, None))
        cur.close()
        return (username, full_name, blocked)

    def get_user_full_name(self, user_id: int):
        """Get the full name of user based on the user ID."""
        cur = self.connection.cursor()
        cur.execute(Query.GET_USER_FULL_NAME, {"user_id": user_id})
        (full_name,) = next(cur, (None,))
        cur.close()
        return full_name

    def get_user_dest_message_id_from_admins(self, message_id: int):
        """Get the user and destination message ID from the message ID of admins."""
        cur = self.connection.cursor()
        cur.execute(Query.GET_USER_DEST_MESSAGE_ID_ADMINS, {"message_id": message_id})
        (user_id, dest_message_id) = next(cur, (None, None))
        cur.close()
        return (user_id, dest_message_id)

    def get_user_message_id_from_users(self, dest_message_id: int):
        """Get the user and message ID from the destination message ID of users."""
        cur = self.connection.cursor()
        cur.execute(
            Query.GET_USER_MESSAGE_ID_USERS, {"dest_message_id": dest_message_id}
        )
        (user_id, message_id) = next(cur, (None, None))
        cur.close()
        return (user_id, message_id)

    def get_dest_message_id_from_users(self, user_id: int, message_id: int):
        """Get the destination message ID from the user and message ID of users."""
        cur = self.connection.cursor()
        cur.execute(
            Query.GET_DEST_MESSAGE_ID_USERS,
            {"user_id": user_id, "message_id": message_id},
        )
        (dest_message_id,) = next(cur, (None,))
        cur.close()
        return dest_message_id

    def get_message_id_from_admins(self, user_id: int, dest_message_id: int):
        """Get the message ID from the user and destination message ID of admins."""
        cur = self.connection.cursor()
        cur.execute(
            Query.GET_MESSAGE_ID_ADMINS,
            {"user_id": user_id, "dest_message_id": dest_message_id},
        )
        (message_id,) = next(cur, (None,))
        cur.close()
        return message_id

    def get_invite_links_count(self, user_id: int):
        """Return the number of invite links for given user."""
        cur = self.connection.cursor()
        cur.execute(Query.GET_INVITE_LINKS_COUNT, {"user_id": user_id})
        (count,) = next(cur, (0,))
        cur.close()
        return count

    def get_invite_message_id(self, user_id: int):
        """Return message ID of invite message."""
        cur = self.connection.cursor()
        cur.execute(Query.GET_INVITE_MESSAGE_ID, {"user_id": user_id})
        (message_id,) = next(cur, (None,))
        cur.close()
        return message_id

    def get_invite_pending(self, user_id: int):
        """Return True if the given user has pending join request."""
        cur = self.connection.cursor()
        cur.execute(Query.GET_INVITE_PENDING, {"user_id": user_id})
        (pending,) = next(cur, (False,))
        cur.close()
        return pending

    def get_user_blocked(self, user_id: int):
        """Get the user status as True if they are blocked and False on otherwise."""
        cur = self.connection.cursor()
        cur.execute(Query.GET_USER_BLOCKED, {"user_id": user_id})
        (blocked,) = next(cur, (False,))
        cur.close()
        return blocked

    def get_users(self):
        """Get a list of all users in the database and the length of list."""
        cur = self.connection.cursor()
        cur.execute(Query.GET_USERS)
        users = [user_id for (user_id,) in cur]
        total = len(users)
        cur.close()
        return users, total

    def reset_invite_links(self, user_id: int):
        """Reset the invite links count for given user."""
        cur = self.connection.cursor()
        cur.execute(Query.RESET_INVITE_LINKS, {"user_id": user_id})
        self.connection.commit()
        cur.close()

    def set_invite_pending(self, user_id: int, pending: bool):
        """Set pending for given user."""
        cur = self.connection.cursor()
        cur.execute(
            Query.SET_INVITE_PENDING,
            {"user_id": user_id, "pending": pending},
        )
        cur.close()
        self.connection.commit()

    def set_user_blocked(self, user_id: int, blocked: bool):
        """Set the user status as True if they are blocked and False on otherwise."""
        cur = self.connection.cursor()
        cur.execute(Query.SET_USER_BLOCKED, {"user_id": user_id, "blocked": blocked})
        self.connection.commit()
        cur.close()
