"""
Discord Presence classes
"""

from typing import Union

from discord_gateway import ActivityType


__all__ = (
    'DiscordActivity',
)


class DiscordActivity:

    """
    Class for discord activities displayed in profile and in status
    """

    __slots__ = 'type', 'name', 'url', 'assets'

    def __init__(self, type: Union[ActivityType, int], name: str = '', url: str = '', assets: dict = ()) -> None:
        self.type = type.value
        self.name = name or None
        self.url = url or None
        self.assets = assets

    def to_json(self) -> dict:
        """
        Converts the activity data to dict\n
        :return:
            Activity data as a dict
        """
        return {
            key: getattr(self, key)
            for key in self.__slots__
            if hasattr(self, key)
        }
