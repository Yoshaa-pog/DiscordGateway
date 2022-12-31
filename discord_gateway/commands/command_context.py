from typing import Optional, Union, Callable

from discord_gateway import Embed, DiscordFile
from discord_gateway.api import HttpClient
from discord_gateway.discord_objects import DiscordMessage

__all__ = (
    'CommandContext',
)


class CommandContext(DiscordMessage):

    def __init__(self, data: Union[dict, object], client: HttpClient) -> None:
        super().__init__(data, client)
        self.api = client
        self._cooldown: Optional[Callable] = None

    @property
    def cooldown(self) -> float:
        if not self._cooldown:
            return 0
        return self._cooldown(self.author.id)

    @cooldown.setter
    def cooldown(self, value: Callable) -> None:
        self._cooldown = value

    from discord_gateway.constants import AllowedMentions

    async def send(
        self,
        content: str = '',
        *,
        tts: bool = False,
        embed: Embed = None,
        message_reference: Optional[str] = None,
        allowed_mentions: Union[AllowedMentions, bool] = None,
        file: DiscordFile = None,
        threads: bool = False
    ) -> Optional[DiscordMessage]:
        """
        Faster way to respond to a command\n
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
            self.channel.id,
            content,
            tts=tts,
            embed=embed,
            message_reference=message_reference,
            allowed_mentions=allowed_mentions,
            file=file,
            threads=threads
        )
