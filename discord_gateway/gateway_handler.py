import asyncio
import logging as log
import threading
import types
from inspect import signature
from typing import Callable, Literal, Union
from dataclasses import dataclass

from discord_gateway.api import HttpClient
from discord_gateway.constants import Intents
from discord_gateway.discord_objects import DiscordMessage
from types import SimpleNamespace

from discord_gateway.gateway import GatewayCon, GatewayMessage

LIB_NAME = r"Yoshaa's Getaway"

__all__ = (
    'GatewayEvent',
    'Gateway',
)


@dataclass
class GatewayEvent:  # Store events
    function: callable
    name: str
    type: str = 'global'

    def get_args(self, msg: GatewayMessage, token: str, user: SimpleNamespace,
                 is_bot: bool = True) -> Union[DiscordMessage, object, Literal[False]]:
        """
        Extracts arguments before passing to an event\n
        :param msg: :class:`GatewayMessage`
            Event message
        :param token: :class:`str`
            Bot token
        :param user: :class:`SimpleNamespace`
            User data
        :param is_bot: :class:`bool`
            Weather the user is a client or a selfBot
        :return:
            Decoded Message
        :rtype:
            DiscordMessage
        """
        args = self.extract_args(msg)
        if self.name == 'message_create':
            if not (msg.data.__dict__.get('guild_id', False) or user.allow_dms) or msg.data.author['id'] == user.id:
                log.info('Canceled event')
                return 'cancel'  # Cancel event
            return DiscordMessage(self.extract_args(msg).data, client=HttpClient(token, bot=is_bot)) if args else args
        else:
            return self.extract_args(msg).data if args else args

    def extract_args(self, msg: GatewayMessage) -> Union[GatewayMessage, Literal[False]]:
        if len(signature(self.function).parameters):
            return msg
        else:
            return False


class Gateway(GatewayCon):

    def __init__(self, intents: int = Intents.All.value, allow_dms: bool = True) -> None:
        super().__init__()
        self.user = None
        self.intents: int = intents
        self.allow_dms = allow_dms
        self._handlers: dict[str] = {}
        self.active_threads: int = 0

    async def handle_message(self, msg: GatewayMessage) -> None:
        """
        Handle gateway response/message\n
        :param msg:
            The message
        :type msg: GatewayMessage
        """
        self._seq = msg.sequence
        if msg.op == 1:
            log.info('received heartbeat')
            heartbeat = {
                'op': 1,
                'd': self._seq
            }
            await self.send(heartbeat)
        elif msg.op == 10:
            log.debug('Received Hello!')
            self._pulse = msg.data.heartbeat_interval / 1000
            identify = {
                'op': 2,
                'd': {
                    'token': self._token,
                    'properties': {
                        '$os': 'windows',
                        "$browser": LIB_NAME,
                        "$device": LIB_NAME,
                    },
                }
            }
            if self.is_bot:
                log.debug('Adding intents')
                identify['d']['intents'] = self.intents
            await self.send(identify)
            log.debug('done identify!')
        elif msg.op == 0:
            event = msg.name.lower()
            if event in self._handlers:
                for handler in self._handlers[event]:
                    func = handler.function
                    if handler.type == 'default':
                        if isinstance(func, types.FunctionType):
                            func(msg)
                        else:
                            await func(msg)
                    elif handler.type == 'global':
                        log.info(f'Running event {handler.name}')
                        args = handler.get_args(msg, token=self._token, user=self.user, is_bot=self.is_bot)
                        if args != 'cancel':
                            threading.Thread(target=asyncio.run, args=(func(args) if args else func(),)).start()
                    else:
                        raise Exception(f'Unknown type: {handler.type}')
            else:
                log.warning(f'unhandled event {event}')
        elif msg.op == 11:
            log.debug('Received op 11')
        else:
            raise Exception(f'Unknown op in msg: {msg.op}')

    def add_listener(self, func: Callable, event: str, *, type: str = 'global') -> None:
        """
        Add an event listener, *(the event will be called when
        the bot receives op 10 and the right event name*)\n
        :param func: :class:`Callable`
            Function to execute when the event runs
        :param event: :class:`str`
            The event name to listen to
        :param type: :class:`str`
            Specify default or global event
            __Global__:
                *default for decorators*
                Will be receiving the extracted version of the arguments (not always GatewayMessage)
            __Default:
                Will be receiving the full data (GatewayMessage), used for default functions and listeners
        """
        handler = GatewayEvent(function=func, name=event, type=type)
        if event in self._handlers:
            self._handlers[event].append(handler)
        else:
            self._handlers[event] = [handler]

    async def make_thread(self, function: Callable, *args, daemon: bool = False, **kwargs) -> None:
        """
        Create a thread (to run stuff faster)\n
        :param function:
            The function of the thread
            ex. "ctx.reply"
        :type function: Callable
        :param args:
            arguments for the thread
        :param daemon:
            Weather to sue daemon thread or default one
        :type daemon: bool
        :param kwargs:
            Key word args for the thread
        """

        async def count_it() -> None:
            await function(*args, **kwargs)
            self.active_threads -= 1

        threading.Thread(target=asyncio.run, args=[count_it()], daemon=daemon).start()
        self.active_threads += 1
