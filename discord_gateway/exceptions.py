"""
Gateway exceptions
"""
from typing import Optional

__all__ = (
    'TooManyRequests',
    'InvalidFunctionArguments',
    'CooldownException',
    'UsernameTooCommon',
    'ItemNotFound',
    'CheckFailed',
    'CommandNotFound',
    'MissingArgumentsException'
)


class TooManyRequests(Exception):
    """
    Calls when sending too many http requests
    """

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "You're sending too many requests")


class InvalidFunctionArguments(Exception):
    """
    Calls when you send invalid arguments to a function
    """

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "You sent an invalid argument to a function")


class CooldownException(Exception):
    """
    Calls when user execute a command whilst still on cooldown
    """

    def __init__(self, message: Optional[str] = None, *, user: str = '') -> None:
        super().__init__(message or f"User {user} is still on cooldown")


class UsernameTooCommon(Exception):
    """
    Calls when changing to a very common username
    """

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "Username is too common, try a different one")


class ItemNotFound(Exception):
    """
    Calls when searching for unknown item
    """

    def __init__(self, message: Optional[str] = None, *, item: Optional[str] = None) -> None:
        super().__init__(message or f"{item} not found")


class CheckFailed(Exception):
    """
    Calls when command check has failed
    """

    def __init__(self, message: Optional[str] = None, *, user: Optional[str] = None) -> None:
        super().__init__(message or f"Check failed for user {user or 'unknown'}")


class CommandNotFound(Exception):
    """
    Calls when command check has failed
    """

    def __init__(self, message: Optional[str] = None, *, command: Optional[str] = None) -> None:
        super().__init__(message or f"Command not found: {command}")


class MissingArgumentsException(Exception):
    """
    Calls when command missing required arguments
    """

    def __init__(self, message: Optional[str] = None, *, command: Optional[str] = None) -> None:
        super().__init__(message or f"Command {command} missing required arguments")
