from enum import Enum
from types import SimpleNamespace
from typing import Optional

from typing_extensions import Self
from discord_gateway.api import HttpClient

__all__ = (
    'DiscordUser',
    'DiscordRole'
)


class DiscordUser:
    __slots__ = 'id', 'name', 'mention', 'bot'

    def __init__(self) -> None:
        self.id: str = ''
        self.name: str = ''
        self.mention: str = ''
        self.id: bool = True


class DiscordRole:
    __slots__ = 'id', 'name', 'color', 'api', 'data', '__token', 'guild_id', 'permissions', 'position'

    def __init__(self) -> None:
        self.id: str = ''
        self.name: str = ''
        self.permissions: str = ''
        self.color: int = 0
        self.position: int = 0
        self.data: Optional[SimpleNamespace] = None
        self.guild_id: str = ''
        self.api: Optional[HttpClient] = None

    def __repr__(self) -> str:
        return self.name

    async def delete(self) -> None:
        pass

    async def edit(
            self,
            name: Optional[str] = None,
            *,
            permissions: Optional[Enum] = None,
            color: Optional[int] = None,
            hoist: Optional[bool] = None,
            unicode_emoji: Optional[str] = None,
            mentionable: Optional[bool] = None
    ) -> Self:
        pass
