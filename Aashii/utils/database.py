"""Module containing Database object."""

import logging
import psycopg2
from Aashii.constants import Query


class Database:
    """A common interface for all database interactions."""

    def __init__(self, database_url: str):
        """Initialize the PostgreSQL database connection."""
        self.database_url = database_url
        self.connection = psycopg2.connect(database_url)

    def _execute(self, query: str, params: dict = None, fetch: str = None):
        """Run a query in its own transaction and return fetched rows, if any.

        The transaction is committed on success and rolled back on error, so a
        failed query never leaves the connection unusable. A lost connection is
        reopened and the query retried once.
        """
        for attempt in range(2):
            if self.connection.closed:
                self.connection = psycopg2.connect(self.database_url)
            try:
                with self.connection, self.connection.cursor() as cur:
                    cur.execute(query, params)
                    if fetch == "one":
                        return cur.fetchone()
                    if fetch == "all":
                        return cur.fetchall()
                    return None
            except (psycopg2.OperationalError, psycopg2.InterfaceError):
                if attempt:
                    raise
                logging.warning("Database connection lost, reconnecting ...")
                self.connection.close()

    def _fetch_one(self, query: str, params: dict, default: tuple):
        return self._execute(query, params, "one") or default

    def add_admin_message(self, message_id: int, user_id: int, dest_message_id: int):
        """Add the message from admins to the database."""
        self._execute(
            Query.ADD_ADMIN_MESSAGE,
            {
                "message_id": message_id,
                "user_id": user_id,
                "dest_message_id": dest_message_id,
            },
        )

    def add_invite_link(self, user_id: int, message_id: int):
        """Add message with invite link generated for given user."""
        self._execute(
            Query.ADD_INVITE_LINK, {"user_id": user_id, "message_id": message_id}
        )

    def add_user(self, user_id: int, username: str, full_name: str):
        """Add the user with unblocked status."""
        self._execute(
            Query.ADD_USER,
            {"user_id": user_id, "username": username, "full_name": full_name},
        )

    def add_user_message(self, message_id: int, user_id: int, dest_message_id: int):
        """Add the message from user to the database."""
        self._execute(
            Query.ADD_USER_MESSAGE,
            {
                "message_id": message_id,
                "user_id": user_id,
                "dest_message_id": dest_message_id,
            },
        )

    def get_last_user_message_id(self, user_id: int):
        """Get the latest message from given user."""
        (message_id,) = self._fetch_one(
            Query.GET_LAST_USER_MESSAGE_ID, {"user_id": user_id}, (0,)
        )
        return message_id

    def get_stats(self):
        """Return user and message counts for the /stats command."""
        return self._execute(Query.GET_STATS, None, "one")

    def get_user(self, user_id: int):
        """Get the details of given user."""
        return self._fetch_one(
            Query.GET_USER, {"user_id": user_id}, (None, None, None)
        )

    def get_user_full_name(self, user_id: int):
        """Get the full name of user based on the user ID."""
        (full_name,) = self._fetch_one(
            Query.GET_USER_FULL_NAME, {"user_id": user_id}, (None,)
        )
        return full_name

    def get_user_dest_message_id_from_admins(self, message_id: int):
        """Get the user and destination message ID from the message ID of admins."""
        return self._fetch_one(
            Query.GET_USER_DEST_MESSAGE_ID_ADMINS,
            {"message_id": message_id},
            (None, None),
        )

    def get_user_message_id_from_users(self, dest_message_id: int):
        """Get the user and message ID from the destination message ID of users."""
        return self._fetch_one(
            Query.GET_USER_MESSAGE_ID_USERS,
            {"dest_message_id": dest_message_id},
            (None, None),
        )

    def get_dest_message_id_from_users(self, user_id: int, message_id: int):
        """Get the destination message ID from the user and message ID of users."""
        (dest_message_id,) = self._fetch_one(
            Query.GET_DEST_MESSAGE_ID_USERS,
            {"user_id": user_id, "message_id": message_id},
            (None,),
        )
        return dest_message_id

    def get_message_id_from_admins(self, user_id: int, dest_message_id: int):
        """Get the message ID from the user and destination message ID of admins."""
        (message_id,) = self._fetch_one(
            Query.GET_MESSAGE_ID_ADMINS,
            {"user_id": user_id, "dest_message_id": dest_message_id},
            (None,),
        )
        return message_id

    def get_invite_links_count(self, user_id: int):
        """Return the number of invite links for given user."""
        (count,) = self._fetch_one(
            Query.GET_INVITE_LINKS_COUNT, {"user_id": user_id}, (0,)
        )
        return count

    def get_invite_message_id(self, user_id: int):
        """Return message ID of invite message."""
        (message_id,) = self._fetch_one(
            Query.GET_INVITE_MESSAGE_ID, {"user_id": user_id}, (None,)
        )
        return message_id

    def get_user_blocked(self, user_id: int):
        """Get the user status as True if they are blocked and False on otherwise."""
        (blocked,) = self._fetch_one(
            Query.GET_USER_BLOCKED, {"user_id": user_id}, (False,)
        )
        return blocked

    def get_users(self):
        """Get a list of all users in the database and the length of list."""
        users = [user_id for (user_id,) in self._execute(Query.GET_USERS, None, "all")]
        return users, len(users)

    def get_users_by_blocked(self, blocked: bool, limit: int):
        """Return users filtered by blocked state."""
        return self._execute(
            Query.GET_USERS_BY_BLOCKED, {"blocked": blocked, "limit": limit}, "all"
        )

    def get_users_by_decision_status(self, decision_status: str, limit: int):
        """Return users filtered by decision status."""
        return self._execute(
            Query.GET_USERS_BY_DECISION_STATUS,
            {"decision_status": decision_status, "limit": limit},
            "all",
        )

    def reset_invite_links(self, user_id: int):
        """Reset the invite links count for given user."""
        self._execute(Query.RESET_INVITE_LINKS, {"user_id": user_id})

    def set_invite_pending(self, user_id: int, pending: bool):
        """Set pending for given user."""
        self._execute(Query.SET_INVITE_PENDING, {"user_id": user_id, "pending": pending})

    def set_user_blocked(self, user_id: int, blocked: bool):
        """Set the user status as True if they are blocked and False on otherwise."""
        self._execute(Query.SET_USER_BLOCKED, {"user_id": user_id, "blocked": blocked})

    def set_user_decision_status(self, user_id: int, decision_status: str):
        """Set the latest approval decision status for given user."""
        self._execute(
            Query.SET_USER_DECISION_STATUS,
            {"user_id": user_id, "decision_status": decision_status},
        )
