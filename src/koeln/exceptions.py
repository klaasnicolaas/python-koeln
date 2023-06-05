"""Asynchronous Python client providing Open Data information of Köln."""


class ODPKoelnError(Exception):
    """Generic Open Data Platform Köln exception."""


class ODPKoelnConnectionError(ODPKoelnError):
    """Open Data Platform Köln - connection error."""
