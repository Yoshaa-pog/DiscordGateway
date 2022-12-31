import asyncio
import threading
from typing import Optional, Any

import websocket
import json
import traceback

from dataclasses import dataclass
from types import SimpleNamespace

import logging as log

GATEWAY_URL = 'wss://gateway.discord.gg'


__all__ = (
    'GatewayMessage',
    'GatewayCon',
)


@dataclass
class GatewayMessage:
    op: int
    data: object
    sequence: int
    name: str


def decode_msg(msg: str) -> GatewayMessage:
    obj = json.loads(msg)
    op = obj['op']
    data = None
    seq = None
    name = None
    if 'd' in obj:
        try:
            data = SimpleNamespace(**obj['d'])
        except TypeError:
            pass
    if 's' in obj:
        seq = obj['s']
    if 't' in obj:
        name = obj['t']
    return GatewayMessage(op, data, seq, name)


class GatewayCon:
    def __init__(self) -> None:
        log.debug('init Gateway Connection')
        self.is_bot: bool = True
        self._token: str = ''
        self._q = asyncio.Queue()
        self._pulse: float = 1
        self._seq: Optional[int] = None
        self.ws: Optional[websocket.WebSocket] = None

    def run(self, token: str, *, bot: bool = True, log_level: int = log.ERROR) -> None:
        """
        Runs the init connection,\n
        Connects to the websocket and sends identify data.\n
        :param token: :class:`str`
            Bot token, access it through the dev portal.
        :param bot: :class:`bool`
            Toggle selfBot or Normal client, used for self botting
        :param log_level: :class:`int`
            Set log level
        """

        log.getLogger().setLevel(log_level)

        self._token = token
        self.is_bot = bot
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._run_connection())  # Inf loop

    async def _run_connection(self) -> None:
        log.info('Running connection')
        ws_url = f'{GATEWAY_URL}/?v=9&encoding=json'
        self.ws = websocket.WebSocket()
        self.ws.connect(ws_url)
        threading.Thread(target=asyncio.run, args=[self._ping_loop()]).start()  # Keepalive loop
        threading.Thread(target=asyncio.run, args=[self._recv_loop(self.ws)]).start()  # Handler loop

    async def _recv_loop(self, ws: Any) -> None:
        log.debug('Handling msg')
        for msg in ws:
            try:
                decoded = decode_msg(msg)  # Convert to simple namespace
                await self.handle_message(decoded)
            except Exception as e:
                log.error(f'Exception in receive: {e}')
                traceback.print_exc()

    async def _ping_loop(self) -> None:
        while True:
            await asyncio.sleep(self._pulse)
            ping = {'op': 1, 'd': None}
            await self.send(ping)

    async def handle_message(self, msg: GatewayMessage) -> None:
        ...  # Override

    async def send(self, msg: dict) -> None:  # Send data to websocket
        try:
            str_msg: json = json.dumps(msg)
            log.debug(f'gateway sent: {msg}')
            self.ws.send(str_msg)
        except json.JSONDecodeError:
            pass  # Ignore json error
        except Exception as e:
            log.error(f'Exception in send: {e}')
            traceback.print_exc()
