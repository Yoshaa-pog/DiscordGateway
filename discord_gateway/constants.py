import random
from enum import Enum
from typing import Union, Any, Optional, Iterator

from typing_extensions import Self
from discord_gateway.types import DiscordUser, DiscordRole

__all__ = (
    'Intents',
    'Permission',
    'Color',
    'ChannelType',
    'Status',
    'ActivityType',
    'AllowedMentions'
)


class Intents(Enum):  # Discord intents
    Guilds: int = 1 << 0
    GuildMembers: int = 1 << 1
    GuildBans: int = 1 << 2
    GuildEmojiAndStickers: int = 1 << 3
    GuildIntegrations: int = 1 << 4
    GuildWebhooks: int = 1 << 5
    GuildInvites: int = 1 << 6
    GuildVoiceStates: int = 1 << 7
    GuildPresences: int = 1 << 8
    GuildMessages: int = 1 << 9
    GuildMessageReactions: int = 1 << 10
    GuildStartTyping: int = 1 << 11
    DirectMessages: int = 1 << 12
    DirectMessageReactions: int = 1 << 13
    DirectMessageTyping: int = 1 << 14
    MessageContent: int = 1 << 15
    GuildScheduledEvents: int = 1 << 16
    AutoModerationConfiguration: int = 1 << 20
    AutoModerationExecution: int = 1 << 21
    GuildsAll: int = 69631
    DirectMessagesAll: int = 28672
    AutoModerationAll: int = 3145728
    All: int = 3244031


class Permission(Enum):
    CreateInstantInvites: int = 1 << 0
    KickMembers: int = 1 << 1
    BanMembers: int = 1 << 2
    Administrator: int = 1 << 3
    ManageChannels: int = 1 << 4
    ManageGuild: int = 1 << 5
    AddReactions: int = 1 << 6
    ViewAuditLog: int = 1 << 7
    PrioritySpeaker: int = 1 << 8
    Stream: int = 1 << 9
    ViewChannel: int = 1 << 10
    SendMessages: int = 1 << 11
    SendTTSMessages: int = 1 << 12
    ManageMessages: int = 1 << 13
    EmbedLinks: int = 1 << 14
    AttachFiles: int = 1 << 15
    ReadMessageHistory: int = 1 << 16
    MentionEveryone: int = 1 << 17
    UseExternalEmojis: int = 1 << 18
    ViewGuildInsights: int = 1 << 19
    Connect: int = 1 << 20
    Speak: int = 1 << 21
    MuteMembers: int = 1 << 22
    DeafenMembers: int = 1 << 23
    MoveMembers: int = 1 << 24
    UseVAD: int = 1 << 25
    ChangeNickname: int = 1 << 26
    ManageNicknames: int = 1 << 27
    ManageRoles: int = 1 << 28
    ManageWebhooks: int = 1 << 29
    ManageEmojisAndStickers: int = 1 << 30
    UseApplicationCommands: int = 1 << 31
    RequestToSpeak: int = 1 << 32
    ManageEvents: int = 1 << 33
    ManageThreads: int = 1 << 34
    CreatePublicThreads: int = 1 << 35
    CreatePrivateThreads: int = 1 << 36
    UseExternalStickers: int = 1 << 37
    SendMessagesInThreads: int = 1 << 38
    UseEmbeddedActivities: int = 1 << 39
    ModerateMembers: int = 1 << 40

    @classmethod
    def all(cls) -> int:
        return sum(map(lambda p: p.value, list(cls)))

    @classmethod
    def from_int(cls, number: Union[str, int]) -> Optional[Iterator[Self]]:
        number = int(number)
        if not number:
            return
        for permission in list(cls):
            if number & permission.value:
                yield permission

    def __repr__(self) -> str:
        return self.name


class ChannelType(Enum):
    TextChannel: int = 0
    DirectChannel: int = 1
    VoiceChannel: int = 2
    GroupChannel: int = 3
    CategoryChannel: int = 4
    AnnouncementChannel: int = 5
    AnnouncementThread: int = 10
    PublicThread: int = 11
    PrivateThread: int = 12
    StageChannel: int = 13
    GuildDirectory: int = 14
    ForumChannel: int = 15


class Color(Enum):
    Blue: int = 0x3498DB
    Green: int = 0x2ECC71
    Yellow: int = 0xFEE75C
    Red: int = 0xE74C3C
    Default: int = 0x8b8b8b
    Orange: int = 0xE67E22
    Gray: int = 0x898989
    Gold: int = 0xeb8c26
    Purple: int = 0xb024f1
    Pink: int = 0xff2ebd

    @classmethod
    def random(cls) -> Self:
        return random.choice(list(cls))


class Status(Enum):
    Online: str = 'online',
    Offline: str = 'offline',
    Idle: str = 'idle'
    DND: str = 'dnd'
    Invisible: str = 'invisible'


class ActivityType(Enum):
    Playing: int = 0
    Streaming: int = 1
    Listening: int = 2
    Watching: int = 3
    Custom: int = 4
    Competing: int = 5


class AllowedMentions:
    __slots__ = 'payload'

    def __init__(self, *, everyone: bool = True, roles: Union[list[DiscordRole], bool] = True,
                 users: Union[list[DiscordUser], bool] = True, replied_user: bool = True) -> None:
        self.payload: dict[str, Any] = {'parse': []}

        if everyone:
            self.payload['parse'].append('everyone')
        if roles:
            self.payload['parse'].append('roles')
        if users:
            self.payload['parse'].append('users')

        # Appending to parse

        if type(roles) is list:
            self.payload['roles'] = [role.id for role in roles]

        if type(users) is list:
            self.payload['users'] = [user.id for user in users]

        if replied_user:
            self.payload['replied_user'] = True

    @classmethod
    def all(cls) -> Self:
        return cls(everyone=True, roles=True, users=True, replied_user=True)

    @classmethod
    def none(cls) -> Self:
        return cls(everyone=False, roles=False, users=False, replied_user=False)
