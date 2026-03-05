"""Contains Label object."""

from .setup import LABELS


class Label:
    """Label contains labels used in inline keyboard buttons."""

    APPROVE = LABELS["APPROVE"]
    BLOCK = LABELS["BLOCK"]
    CONNECT = LABELS["CONNECT"]
    DECLINE = LABELS["DECLINE"]
    PENDING_REQUEST = LABELS["PENDING_REQUEST"]
    UNBLOCK = LABELS["UNBLOCK"]
