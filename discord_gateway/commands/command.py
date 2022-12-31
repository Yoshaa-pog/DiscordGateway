"""
Command object
"""

__all__ = (
    'ClientCommand',
    'CommandThread',
)

import asyncio
import threading
import time
from typing import Callable, Optional, Any
from discord_gateway import CooldownException
from .command_context import CommandContext


class CommandThread(threading.Thread):

    def __init__(self, target, args=None, kwargs=None) -> None:
        threading.Thread.__init__(self, target=target, args=args, kwargs=kwargs)
        self.exc: Optional[BaseException] = None

    def run(self) -> None:
        self.exc = None
        try:
            self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self.exc = e

    def join(self, timeout=None) -> None:
        super(CommandThread, self).join(timeout)
        if self.exc:
            raise self.exc


class ClientCommand:
    __slots__ = 'function', 'description', 'cooldown', '_check', 'track_cooldown', 'error_allocator'

    def __init__(self, function: Callable, description: str, cooldown: int = 0) -> None:
        self.function = function
        self.description = description
        self.cooldown = cooldown
        self._check: Optional[Callable] = None
        self.track_cooldown: dict[str, float] = {}
        self.error_allocator: Optional[Callable] = None

    def error(self, allocator: Callable) -> Callable[..., Any]:
        self.error_allocator = allocator
        return allocator

    def dispatch(self, context: CommandContext, args: list, bot: Optional[Any] = None) -> None:
        user_id: str = context.author.id
        if self.cooldown:
            if user_id not in self.track_cooldown:
                self.track_cooldown[user_id] = time.time()
            elif time.time() - self.track_cooldown[user_id] < self.cooldown:
                context.cooldown = self.get_cooldown
                if not self.error_allocator:
                    return bot.raise_error(context, CooldownException(user=user_id))
                return threading.Thread(target=asyncio.run,
                                        args=(self.error_allocator(context, CooldownException(user=user_id)),)).start()
            else:
                self.track_cooldown[user_id] = time.time()
        command_thread = CommandThread(target=asyncio.run, args=(self.function(context, *args),))
        # Running thread
        command_thread.start()
        try:
            command_thread.join()
        except BaseException as e:
            if not self.error_allocator:
                return bot.raise_error(context, e)
            threading.Thread(target=asyncio.run, args=(self.error_allocator(context, e),)).start()

    def get_cooldown(self, user_id: str) -> Optional[float]:
        if user_id not in self.track_cooldown or not self.cooldown:
            return None
        return self.cooldown - (time.time() - self.track_cooldown.get(user_id))

    def set_check(self, check: Callable) -> None:
        self._check = check

    def eval_check(self, ctx: CommandContext) -> bool:
        if self._check is None:
            return True
        return self._check(ctx)
