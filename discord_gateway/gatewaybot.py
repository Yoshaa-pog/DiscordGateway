from typing import Optional, Callable, Any, Union, AsyncIterator, Iterator

from requests import Response

from discord_gateway.discord_objects import DiscordChannel, DiscordGuild
from discord_gateway.discord_user import DiscordUser, DiscordMember
from discord_gateway.gateway_handler import Gateway
from discord_gateway.gateway import GatewayMessage
from discord_gateway.api import HttpClient
from types import SimpleNamespace
from discord_gateway.constants import Intents, Status
from discord_gateway.presence import DiscordActivity

__all__ = (
    'GatewayBot',
    'ClientUser'
)


class GatewayBot(Gateway):

    def __init__(self, *, intents: int = Intents.All, allow_dms: bool = True) -> None:
        super().__init__(intents=intents.value, allow_dms=allow_dms)
        self.api: Optional[HttpClient] = None
        self.user: Optional[ClientUser] = None
        self.add_listener(self.default_ready, event='ready', type='default')

    async def default_ready(self, msg: GatewayMessage) -> None:
        """
        Default ready,\n
        Stores user data, api and user tag.\n
        :param msg: :class:`GatewayMessage`
            The data received from the identify response
        """

        self.api = HttpClient(self._token, bot=self.is_bot)
        self.user = ClientUser(msg, self.allow_dms, client=self.api)

    def event(self, func: Callable) -> Callable[..., Any]:
        """
        **Decorator**\n
        Used to assign a function with an event\n
        :param func: The function to assign
        :return: :class:`Callable`
            Returns the function itself
        """
        self.add_listener(func, event=func.__name__.replace('on_', '', 1) if func.__name__.startswith(
            'on_') else func.__name__)
        return func

    @property
    def dms(self) -> Union[Response, dict]:
        """
        Get open dms of bot\n
        :return: :class:`Union[Response, dict]`
            Returns the open dms
        """
        return self.api.requests(method='GET', path='/users/@me/channels')

    @property
    def guilds(self) -> Iterator[DiscordGuild]:
        """
        Get current user guilds\n
        :return:
            Iterator of the guilds
        """
        for guild in self.api.requests(method='GET', path='/users/@me/guilds'):
            yield DiscordGuild(guild.get('id'), api=self.api)

    async def get_channel(self, channel_id: str) -> DiscordChannel:
        """
        Get channel by his id\n
        :param channel_id: :class:`str`
            The channel id
        :return: :class:`DiscordChannel`
            The channel
        """
        return DiscordChannel(channel_id, api=self.api)

    async def get_guild(self, guild_id: str) -> DiscordGuild:
        """
        Get guild by id\n
        :param guild_id: :class:`str`
            The guild id
        :return: :class:`DiscordGuild`
            Returns the guild
        """
        return DiscordGuild(guild_id, api=self.api)

    async def get_user(self, user_id: str) -> DiscordUser:
        """
        Get user by his id\n
        :param user_id: :class:`str`
            The user id
        :return: :class:`DiscordUser`
            Returns the user
        """
        headers = {
            'authorization': self.api.get_auth(),
            'content-type': 'application/json'
        }
        return DiscordUser(self.api.requests(method='POST', path=f'/users/@me/channels', json={"recipients": [user_id]},
                                             headers=headers), self.api)

    async def change_presence(self, activity: Optional[DiscordActivity] = None,
                              status: Union[Status, str] = Status.Online) -> None:
        """
        Change self presence\n
        :param activity:
            The activity to show
        :type activity: Optional[DiscordActivity]
        :param status:
            The status of bot ex. idle
        :type status: Union[Status, str]
        """
        payload = await self.api.manager.get_presence(activity, status)
        await self.send(payload)

    async def join(self, server_invite: str) -> Union[Response, dict]:
        """
        Join a guild by invite {SelfBot only}\n
        :param server_invite: :class:`str`
            The server invite link
        :return: :class:`Union[Response, dict]`
            The obtained server
        """
        return self.api.requests(method='POST', path=f'/invites/{server_invite}')

    async def leave(self, guild_id: str) -> None:
        """
        Leaves a guild\n
        :param guild_id: :class:`str`
            The guild id to leave
        """
        self.api.requests(method='DELETE', path=f'/users/@me/guilds/{guild_id}')

    async def create_group_chat(self, ids: list[str]) -> Union[Response, dict]:
        """
        Creates a group chat with members {SelfBot only}\n
        :param ids: :class:`list[str]`
            The list of the member ids
        :return: :class:`Union[Response, dict]`
            The opened group chat
        """
        headers = {
            'authorization': self.api.get_auth(),
            'content-type': 'application/json'
        }
        return self.api.requests(method='POST', path=f'/users/@me/channels', json={'recipients': ids}, headers=headers)

    async def members_from_guilds(self, guild_id: str) -> AsyncIterator[DiscordMember]:
        """
        Get possible members from a guild
        :param guild_id:
        :return:
        """
        if guild_id not in [guild.get('id') for guild in self.user.guilds]:
            raise AttributeError('Guild not found')
        for member in list(filter(lambda guild: guild.get('id') == guild_id, self.user.guilds))[0]['members']:
            yield DiscordMember(member, member.get('user'), guild_id, client=self.api)


class ClientUser(SimpleNamespace):
    __slots__ = 'api', 'id', 'username', 'discriminator', 'bot', 'allow_dms', 'guilds', 'tag'

    def __init__(self, msg: GatewayMessage, allow_dms: bool, client: HttpClient):
        super(ClientUser, self).__init__(**msg.data.user)
        self.api = client
        self.id: str = msg.data.user.get('id')
        self.username: str = msg.data.user.get('username')
        self.discriminator: str = msg.data.user.get('discriminator')
        self.avatar: Any = msg.data.user.get('avatar')
        self.bot: bool = msg.data.user.get('bot', False)
        self.allow_dms = allow_dms  # Check if dms are allowed in config
        self.tag = f'{self.username}#{self.discriminator}'

    async def edit(
            self,
            username: Optional[str] = None,
            *,
            avatar: Any = None
    ) -> Union[Response, dict]:
        """
        Edit a user profile\n
        :param username:
            New username
        :type username: Optional[str]
        :param avatar:
            New pfp (profile picture/avatar)
        :type avatar: Any
        :return
            The new updated user
        """
        payload: dict[str, Any] = {'username': (username or self.username)}

        if avatar:
            payload[avatar] = avatar

        return await self.api.manager.edit_bot_user(payload=payload)
