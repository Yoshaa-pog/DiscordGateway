"""
The request handler.

Saves common useful functions for the api
"""
import time
from typing import Optional, Any, Union

from requests import Response, HTTPError

from discord_gateway.discord_objects import DiscordMessage

from discord_gateway.embed import Embed, DiscordFile
from discord_gateway.constants import Status, AllowedMentions
from discord_gateway.presence import DiscordActivity
from discord_gateway.exceptions import UsernameTooCommon

__all__ = (
    'RequestsManager',
)


class RequestsManager:
    from discord_gateway.api import HttpClient  # Circular imports

    def __init__(self, api: HttpClient):
        self.api = api

    async def send_message(self, channel_id: str, content: str = '', *, tts: bool = False, embed: Embed = None,
                           message_reference: Optional[str] = None,
                           allowed_mentions: Union[AllowedMentions, bool, None] = None,
                           file: Optional[DiscordFile] = None, threads: bool = False) -> Optional[DiscordMessage]:
        """
        Head sender for discord messages
        """
        payload: dict[str, Any] = {
            'content': content or None,
            'tts': tts,
            'embeds': [embed.to_json()] if embed else [],
            'message_reference':
                {
                    "channel_id": channel_id,
                    "message_id": message_reference,
                } if message_reference else {},
        }

        if allowed_mentions is False:
            payload['allowed_mentions'] = AllowedMentions.none().payload

        if allowed_mentions:
            payload['allowed_mentions'] = allowed_mentions.payload

        r = self.api.requests(method='POST', path=f'/channels/{channel_id}/messages',
                              json=payload, threads=threads, files=file.to_json() if file else None)
        if file:
            file.path.close()

        return DiscordMessage(r, client=self.api) if not threads else None

    @staticmethod
    async def get_presence(activity: Optional[DiscordActivity], status: Optional[Status], since: float = 0) -> dict:

        if status is Status.Offline:
            status = Status.Invisible

        elif status is Status.Idle:
            since = int(time.time() * 1000)

        activities = []

        if activity:
            activities = [activity.to_json()]

        payload = {
            'op': 3,
            'd': {
                'activities': activities,
                'afk': False,
                'since': since,
                'status': status.value,
            },
        }

        return payload

    async def edit_bot_user(
            self,
            payload: dict[str, Any]
    ) -> Union[Response, dict]:
        try:
            return self.api.requests(method='PATCH', path='/users/@me', json=payload)
        except HTTPError as e:
            if not e.args[0].split(':')[0] == '400 Client Error':
                raise e
            raise UsernameTooCommon()
