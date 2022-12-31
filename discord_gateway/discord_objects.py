import asyncio
import threading

from requests import Response
from typing import Optional, Iterator, Union, Any, AsyncIterator
from typing_extensions import Self

from discord_gateway.api import HttpClient
from discord_gateway.constants import ChannelType, Color, Permission, AllowedMentions
from discord_gateway.embed import Embed, DiscordFile
from discord_gateway.exceptions import InvalidFunctionArguments

__all__ = (
    'DiscordMessage',
    'DiscordChannel',
    'DiscordGuild',
)

from discord_gateway.guild_objects import DiscordRole


class DiscordMessage:
    __slots__ = '__token', 'data', 'id', 'content', 'api', 'guild', 'author', 'channel'

    def __init__(self, data: Union[dict, object], client: HttpClient) -> None:
        if not data:
            return
        from discord_gateway.discord_user import DiscordMember, DiscordUser  # Circular imports
        self.__token = client.get_token()
        data = dict(data.__dict__) if type(data) is not dict else data
        self.data = data
        self.id = data.get('id')
        self.content = data.get('content')
        self.api = client
        if data.get('guild_id', False):
            self.guild = DiscordGuild(guild_id=data.get('guild_id'), api=self.api)
            self.author = DiscordMember(data.get("member", {}), data.get("author", {}), self.guild.id,
                                        self.api)
        else:
            self.author: Union[DiscordMember, DiscordUser] = DiscordUser(data.get('author', {}), self.api)
        if data.get('channel_id', False):
            self.channel = DiscordChannel(channel_id=self.data.get('channel_id'), api=self.api)

    def __repr__(self) -> str:
        return self.id

    async def delete(self, threads: bool = False) -> Union[Response, dict]:
        """
        Deletes the message\n
        :param threads:
            Weather to use threading or not
        :return: :class:`Union[Response, dict]`
            The deleted message
        """
        return self.api.requests(method='DELETE', path=f'/channels/{self.channel.id}/messages/{self.id}',
                                 data={}, threads=threads)

    async def reply(self, content: str = '', *, tts: bool = False,
                    allowed_mentions: Union[AllowedMentions, bool] = None,
                    file: DiscordFile = None, embed: Embed = None) -> Self:
        """
        Quick way to reply to a message\n
        :param content: :class:`str`
            Message content
        :param tts: :class:`bool`
            Weather or not to use text to speech
        :param embed: :class:`Embed`
            Optional embed to send
        :param allowed_mentions:
            Weather the bot should mention everyone and roles via the command
        :param file:
            Additional attachment to the message
        :return: :class:`DiscordMessage`
            The replied message
        """
        return await self.api.manager.send_message(
            self.channel.id,
            content,
            tts=tts,
            embed=embed,
            allowed_mentions=allowed_mentions,
            file=file,
            message_reference=self.id,
        )

    async def edit(self, content: str) -> Union[Response, dict]:
        """
        Edit message\n
        :param content: :class:`str`
            New content
        :return: :class:`Union[Response, dict]`
            New message
        """
        headers = {
            'Authorization': self.api.get_auth(),
            'Content-Type': 'application/json'
        }
        return self.api.requests(method='PATCH', path=f'/channels/{self.channel.id}/messages/{self.id}',
                                 headers=headers, data='{"content":"' + content + '"}')


class DiscordChannel:
    __slots__ = 'id', '__token', 'api', '_data'

    def __init__(self, channel_id: str, api: HttpClient, use_data: bool = False) -> None:
        self.id: str = channel_id
        self.__token = api.get_token()
        self.api = api
        self._data: dict = {}
        if use_data:
            threading.Thread(target=asyncio.run, args=(self.get_data(),)).start()

    def __repr__(self) -> str:
        return self.id

    async def get_data(self) -> None:
        self._data = self.api.requests(method='GET', path=f'/channels/{self.id}')

    async def edit(self, name: Optional[str] = None, type: ChannelType = None, position: Optional[int] = None,
                   topic: Optional[str] = None) -> None:
        """
        Modify a channel
        :param name:
        :param type:
        :param position:
        :param topic:
        :return:
        """
        await self.get_data()
        payload = {
            'name': name or self.name,
            'type': type or self._data.get('type'),
            'position': position or self._data.get('position'),
            'topic': topic or self._data.get('topic'),
        }

        self.api.requests('PATCH', f'/channels/{self.id}', json=payload)

    async def send(self, content: str = '', *, tts: bool = False, message_reference: str = '', embed: Embed = None,
                   threads: bool = False, allowed_mentions: Union[AllowedMentions, bool] = None,
                   file: DiscordFile = None) -> DiscordMessage:
        """
        Send message in channel\n
        :param content: :class:`str`
            The content to send
        :param tts: :class:`bool`
            Weather or not to use text to speach on send
        :param message_reference:
            The message to reply to
        :type message_reference: str
        :param embed: :class:`Embed`
            An embed to send with the message
        :param allowed_mentions:
            Weather the bot should mention everyone and roles via the command
        :param file:
            Additional attachment to the message
        :param threads: :class:`bool`
            Weather to use threads
        :return: :class:`Optional[DiscordMessage]`
            The final message (only works without threading)
        """
        return await self.api.manager.send_message(
            self.id,
            content,
            tts=tts,
            embed=embed,
            message_reference=message_reference,
            allowed_mentions=allowed_mentions,
            file=file,
            threads=threads
        )

    async def delete(self, threads: bool = False) -> None:
        """
        Delete the channel\n
        :param threads:
            Weather to use threading or not.
        """
        self.api.requests(method='DELETE', path=f'/channels/{self.id}', threads=threads)

    async def generate_invite(self, *, max_age: int = 0, max_uses: int = 0,
                              temporary: bool = False) -> Union[str, dict]:
        """
        Creates an invitation to the server\n
        :param max_age: :class:`int`
            Max age of the invite before it gets deleted
        :param max_uses: :class:`int`
            Max allowed uses of the invite
        :param temporary: :class:`bool`
            Grants temporary membership on join
        :return: :class:`Union[str, dict]`
            The generated invite
        """
        payload = {
            "max_age": max_age,
            "max_uses": max_uses,
            "temporary": temporary,
        }
        return self.api.requests(method='POST', path=f'/channels/{self.id}/invites', json=payload)

    async def purge(self, limit: int = 50) -> None:
        """
        Bulk delete messages in a channel
        :param limit:
        :return:
        """
        messages = self.fetch_messages(limit=limit)

        payload = {
            'messages': [message.id async for message in messages]
        }

        self.api.requests(method='POST', path=f'/channels/{self.id}/messages/bulk-delete', json=payload)

    async def fetch_messages(self, limit: int = 50) -> AsyncIterator[DiscordMessage]:
        """

        :param limit:
        :return:
        """
        messages = self.api.requests(method='GET', path=f'/channels/{self.id}/messages?limit={limit}')
        for msg in messages:
            yield DiscordMessage(msg, client=self.api)

    @property
    def messages(self) -> Iterator[DiscordMessage]:
        """
        Get channel messages\n
        :return: :class:`DiscordMessage`
            Every message within 100 messages limit (use async fetch messages for more or less than the limit)
        """
        r = self.api.requests(method='GET', path=f'/channels/{self.id}/messages?limit=100')
        for msg in r:
            yield DiscordMessage(msg, client=self.api)

    @property
    def name(self) -> str:
        """

        :return:
        """
        return self.api.requests(method='GET', path=f'/channels/{self.id}').get('name')


class DiscordGuild:
    __slots__ = 'id', '__token', 'api'

    def __init__(self, guild_id: str, api: HttpClient) -> None:
        self.id: str = guild_id
        self.__token = api.get_token()
        self.api = api

    def __repr__(self) -> str:
        return self.id

    @property
    def name(self) -> str:
        return self.api.requests(method='GET', path=f'/guilds/{self.id}').get('name')

    @property
    def channels(self) -> Iterator[DiscordChannel]:
        """
        Get all guild channels\n
        :return: :class:`DiscordChannel`
            The channels of the guild
        """
        for channel in self.api.requests(method='GET', path=f'/guilds/{self.id}/channels'):
            yield DiscordChannel(channel.get('id'), api=self.api, use_data=False)

    @property
    def members(self) -> object:
        from discord_gateway.discord_user import DiscordMember  # Circular import

        for member in self.api.requests(method='GET', path=f'/guilds/{self.id}/members?limit=1000'):
            yield DiscordMember(member, member.get('user'), self.id, client=self.api)

    @property
    def roles(self) -> Iterator[DiscordRole]:
        """
        Get all guild roles
        :return:
            List of role ids
        """
        for role in self.api.requests(method='GET', path=f'/guilds/{self.id}/roles'):
            yield DiscordRole(role, self.id, client=self.api)

    @property
    def data(self) -> dict:
        return self.api.requests(method='GET', path=f'/guilds/{self.id}')

    async def edit(
            self, name: Optional[str] = None,
            *,
            region: Optional[str] = None,
            icon: Any = None,
            banner: Any = None,
            description: Optional[str] = None,
            **kwargs
    ) -> Union[Response, dict]:
        """
        Edit a guild
        :param name:
        :param region:
        :param icon:
        :param banner:
        :param description:
        :param kwargs:
        :return:
        """
        data = self.data

        payload = {
            'name': name or self.name,
            'region': region or data.get('region'),
            'icon': icon or data.get('icon'),
            'banner': banner or data.get('banner'),
            'description': description or data.get('description'),
        }

        if kwargs:
            payload += {
                key: value or data.get(key) for key, value in kwargs
            }

        return self.api.requests(method='PATCH', path=f'/guilds/{self.id}', json=payload)

    def get_role(self, role_id: Optional[str] = None, *, name: Optional[str] = None,
                 role_list: Optional[list[DiscordRole]] = None) -> Optional[DiscordRole]:
        """
        Get a role by id or name
        :param role_id:
        :param name:
        :param role_list:
        :return:
        """
        roles = role_list or self.roles  # To save spam requests
        try:
            if role_id is not None:
                return next(role for role in roles if role_id == role.id)
            if name is None:
                raise InvalidFunctionArguments('You must send 1 argument for the search query')
            return next(role for role in roles if name == role.name.lower())
        except StopIteration:
            return None

    async def create_role(
            self,
            *,
            name: str = None,
            permissions: Optional[Permission] = '0',
            color: Optional[Color] = None,
            hoist: Optional[bool] = None,
            mentionable: Optional[bool] = None,
    ) -> DiscordRole:
        """
        Creates a new role
        :param name:
        :param permissions:
        :param color:
        :param hoist:
        :param mentionable:
        :return:
        """

        color = color or Color.Default

        if type(permissions) is not int:
            permissions = permissions.value

        payload: dict[str, Any] = {
            'name': name or 'new role',
            'permissions': str(permissions),
            'color': color.value,
            'mentionable': mentionable or False
        }

        if hoist is not None:
            payload['hoist'] = hoist

        data = self.api.requests('POST', f'/guilds/{self.id}/roles', json=payload)
        return DiscordRole(data, self.id, client=self.api)

    async def create_channel(self, name: str, *, channel_type: ChannelType = ChannelType.TextChannel,
                             permission_overwrites: list = (), threads: bool = False) -> Optional[DiscordChannel]:
        """
        Create a channel in the guild\n
        :param name: :class:`str`
            The name of the channel
        :param channel_type: :class:`ChannelType`
            The channel type
        :param permission_overwrites: :class:`list`
            The permissions of the channel
        :param threads: :class:`bool`
            Weather to use threads or normal async
        :return: :class:`DiscordChannel`
            The created channel
        """
        payload = {
            'name': '-'.join(name.split(' ')),
            'permission_overwrites': permission_overwrites,
            'type': channel_type.value
        }
        data = self.api.requests(method='POST', path=f'/guilds/{self.id}/channels', json=payload, threads=threads)
        if not threads:
            return DiscordChannel(data.get('id'), api=self.api)

    async def leave(self) -> None:
        """
        Leaves the guild\n
        """
        self.api.requests(method='DELETE', path=f'users/@me/guilds/{self.id}')

    from discord_gateway.discord_user import DiscordMember  # Circular import

    async def get_member(self, member_id: str) -> Optional[DiscordMember]:
        """
        Get discord member by id\n
        :param member_id:
            The id of the member
        :type member_id: str
        :return:
            The gotten member
        :rtype: DiscordMember
        """

        from discord_gateway.discord_user import DiscordMember  # Circular import + Not a type hint

        data = self.api.requests(method='GET', path=f'/guilds/{self.id}/members/{member_id}')
        if data:
            return DiscordMember(data, data.get('user'), self.id, client=self.api)

    async def kick(self, member: DiscordMember) -> None:
        """
        Kick a member from the guild\n
        :param member: :class:`DiscordMember`
            The member to kick from the guild
        """
        self.api.requests(method='DELETE', path=f'/guilds/{self.id}/members/{member.id}')

    async def ban(self, member: DiscordMember, delete_message_seconds: int = 3600) -> None:
        """
        Ban a member from the guild\n
        :param member: :class:`DiscordMember`
            The member to ban from the guild
        :param delete_message_seconds: :class:`int`
            Delete message seconds, delete all the messages from the user
            in the given time frame
        """
        payload = {
            "delete_message_seconds": delete_message_seconds
        }
        self.api.requests(method='PUT', path=f'/guilds/{self.id}/bans/{member.id}',
                          data=payload)

    async def unban(self, member_id: str) -> None:
        """
        Unbans a member from the guild\n
        :param member_id: :class:`str`
            The member id to unban
        """
        self.api.requests(method='DELETE', path=f'/guilds/{self.id}/bans/{member_id}')
