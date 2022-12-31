from types import SimpleNamespace
from typing import Optional

from typing_extensions import Self

from discord_gateway.api import HttpClient
from discord_gateway.constants import Permission

__all__ = (
    'DiscordRole',
)


class DiscordRole:
    __slots__ = 'id', 'name', 'color', 'api', 'data', '__token', 'guild_id', 'permissions', 'position'

    def __init__(self, data: dict, guild_id: str, client: HttpClient) -> None:
        self.id: str = data.get('id')
        self.name: str = data.get('name')
        self.permissions: list[Permission] = list(Permission.from_int(data.get('permissions', 0)))
        if Permission.Administrator in self.permissions:
            self.permissions = list(Permission)
        self.color: int = data.get('color', 0)
        self.position: int = data.get('position', 0)
        self.data = SimpleNamespace(**data)
        self.guild_id = guild_id
        self.api = client
        self.__token = client.get_token()

    def __repr__(self) -> str:
        return self.name

    async def delete(self) -> None:
        self.api.requests(method='DELETE', path=f'/guilds/{self.guild_id}/roles/{self.id}')

    async def edit(
            self,
            name: Optional[str] = None,
            *,
            permissions: Optional[Permission] = None,
            color: Optional[int] = None,
            hoist: Optional[bool] = None,
            unicode_emoji: Optional[str] = None,
            mentionable: Optional[bool] = None
    ) -> Self:
        """

        :param name:
        :param permissions:
        :param color:
        :param hoist:
        :param unicode_emoji:
        :param mentionable:
        :return:
        """

        if type(permissions) is not int:
            permissions = permissions.value

        payload = {
            'name': name or self.name,
            'permissions': str(permissions) or self.permissions,
            'color': color or self.color,
            'hoist': hoist or self.data.hoist,
            'unicode_emoji': unicode_emoji or self.data.unicode_emoji,
            'mentionable': mentionable or self.data.mentionable,
        }

        data = self.api.requests(method='PATCH', path=f'/guilds/{self.guild_id}/roles/{self.id}', json=payload)

        return self.__init__(data, self.guild_id, client=self.api)
