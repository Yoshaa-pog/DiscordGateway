from __future__ import annotations

import asyncio
import inspect
import re
import threading
from inspect import signature
from typing import Callable, Optional, Any

import discord_gateway
from .command_context import CommandContext
from .command import ClientCommand
from discord_gateway import GatewayBot, GatewayMessage, Embed, Color, DiscordUser, DiscordMember, CommandNotFound
from discord_gateway.exceptions import ItemNotFound, CheckFailed

from itertools import zip_longest
from requests import HTTPError
import logging as log

__all__ = (
    'CommandsBot',
)


async def _conv(bot: GatewayBot, ctx: CommandContext, item: str, anno: type) -> Any:
    """
    Converts annotations to items\n
    :param bot:
        The user object
    :param ctx:
        The message context
    :param item:
        The item to convert
    :param anno:
        The annotation
    :return:
        Item after convertion
    """
    if anno is DiscordUser:
        try:
            if type(item) is inspect.Parameter:
                return item.default
            return await bot.get_user(re.sub(r'[@!<>]', '', item))
        except HTTPError:
            raise ItemNotFound(item='User')
    if anno is DiscordMember:
        if not ctx.guild:
            raise ItemNotFound(item='Member')
        try:
            if type(item) is inspect.Parameter:
                return item.default
            return await ctx.guild.get_member(re.sub(r'[@!<>]', '', item))
        except HTTPError:
            raise ItemNotFound(item='Member')
    return anno(item)


class CommandsBot(GatewayBot):

    def __init__(self, *args, command_prefix: str, case_sensitivity: bool = False, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.case_sensitivity = case_sensitivity
        self.prefix = command_prefix
        self.__commands: dict[str, ClientCommand] = {}
        self._check: Optional[Callable] = None

        # Default listeners and commands
        self.add_listener(self.message_listener, event='message_create', type='default')
        self.add_command(self.default_help, command='help', description='Shows this message')

    async def message_listener(self, msg: GatewayMessage) -> None:
        """
        Default on_message_create,\n
        register messages as commands\n
        :param msg: :class:`GatewayMessage`
            The message to check for
        """
        if not msg.data.content.startswith(self.prefix) or not (
                msg.data.__dict__.get('guild_id', False) or self.allow_dms) \
                or msg.data.author['id'] == self.user.id:
            return
        await self.register_commands(CommandContext(msg.data, self.api))

    async def default_help(self, ctx: CommandContext) -> None:
        """
        Default help function.\n
        Shows help manu\n
        :param ctx: The given context
        :type ctx: CommandContext
        """
        embed = Embed(title='Bot Commands', color=Color.Blue)
        aliases: list[str] = []

        # Checking aliases
        seen: list[Callable] = []
        for name, command in self.__commands.items():
            if command.function not in seen:
                seen.append(command.function)
            else:
                aliases.append(name)

        commands = {key: self.__commands[key] for key in sorted(self.__commands.keys())}
        for command_name, command in commands.items():
            if command_name in aliases or not command.eval_check(ctx):
                continue
            sig = signature(command.function)
            args = '' if len(list(sig.parameters)) <= 1 else f" ({', '.join(list(sig.parameters.keys())[1:])})"
            embed.add_field(name=command_name.title() + args, value=f'{command.description}', inline=False)
        await ctx.send(embed=embed)

    def raise_error(self, ctx: CommandContext, error: BaseException) -> None:
        """
        Raise an error safely\n
        :param ctx:
            Context for the error
        :param error:
            The error
        """
        if 'command_error' in self._handlers:
            for error_handler in map(lambda handler: handler.function, self._handlers['command_error']):
                threading.Thread(target=asyncio.run, args=(error_handler(ctx, error),)).start()
        else:
            raise error

    def set_check(self, check: Callable) -> None:
        """
        Sets a check\n
        :param check:
            The check to assign
        """
        self._check = check

    def clear_check(self) -> None:
        """
        Resets Checks
        """
        self._check = None

    def add_command(self, func: Callable, command: str, description: str = '', cooldown: int = 0,
                    check: Optional[Callable] = None) -> None:
        """
        Add a command by name.\n
        :param func:
            The function to assign with the command
        :type func: Callable
        :param command:
            The command name.
        :type command: str
        :param description:
            A description for the command
        :type description: str
        :param cooldown:
            The cooldown for the command
        :type cooldown: int
        :param check:
            Local check for the specified command
            will take context as a param
        :type check: Callable
        """
        self.__commands[command] = ClientCommand(func, description or 'No description provided', cooldown)
        if check is not None:
            self.__commands[command].set_check(check)

    def remove_command(self, command: str) -> bool:
        """
        Removes a command by name.\n
        :param command:
            The command to remove
        :type command: str
        :return
            Success or failure
        """
        if command in self.__commands:
            del self.__commands[command]
            return True
        return False

    def command(
            self,
            name: str = '',
            aliases: list = (),
            description: Optional[str] = None,
            cooldown: int = 0,
            check: Optional[Callable[..., bool]] = None
    ) -> Callable[..., ClientCommand]:
        """
        **Decorator**\n
        Used to assign a function with a command\n
        :param name: :class:`str`
            Name for the command
        :param aliases: :class:`list[str]`
            Aliases for the given command
        :param description: :class:`str`
            A description for the command
        :param cooldown: :class:`int`
            The cooldown for the command
        :param check: :class:`Callable`
            Local check for the command, takes context as argument
        :return: :class:`Callable[[{__name__}], None]`
            The nested function
        """

        def decorator(command: Callable) -> ClientCommand:
            """
            **Nested Decorator**\n
            Takes a function and assign with a command\n
            :param command: :class:`Callable`
                The function to assign
            """
            command_name = name or command.__name__
            self.add_command(command, command_name, description, cooldown, check)
            for alias in aliases:
                self.add_command(command, str(alias), description, cooldown, check)
            return self.__commands[command_name]

        return decorator

    async def register_commands(self, msg: CommandContext) -> None:
        """
        Checks for available assigned commands\n
        if true:
        \tExecutes the commands\n
        if false:
        \tIgnores or raises an error depends on your settings\n
        :param msg: :class:`CommandContext`
            The command, data
        """
        command_name: str = msg.content.replace(self.prefix, '', 1).split(' ')[0]

        if not self.case_sensitivity:
            command_name = command_name.lower()

        if command_name in self.__commands:

            command = self.__commands[command_name]
            func = command.function
            allocator = command.error_allocator
            sig = signature(func).parameters

            # Checking process..
            if (self._check and not self._check(msg)) or not command.eval_check(msg):
                e = CheckFailed(user=msg.author.id)
                if allocator:
                    threading.Thread(target=asyncio.run, args=(allocator(msg, e),)).start()
                    return
                return self.raise_error(msg, e)

            non_default = filter(lambda sign: sign.default is sign.empty and sign.kind is not sign.VAR_POSITIONAL,
                                 sig.values())
            args = msg.content.split(' ')[1:len(sig)]
            if len(list(non_default)) - 1 > len(args):
                return self.raise_error(msg, discord_gateway.MissingArgumentsException(command=command_name))
            else:
                args = msg.content.replace(self.prefix, '', 1).split(' ')[1:]
            values = list(sig.values())
            log.info(f'running command {command_name}({", ".join(args)})')
            try:
                args = [
                    (str(arg) if sign.kind != sign.VAR_POSITIONAL else arg)
                    if sign.annotation is sign.empty else await _conv(self, msg, arg, sign.annotation)
                    for arg, sign in zip_longest(args, values[1:], fillvalue=values[-1])
                    if len(values) - 1
                ]
            except Exception as e:
                if allocator:
                    threading.Thread(target=asyncio.run, args=(allocator(msg, e),)).start()
                    return
                return self.raise_error(msg, e)
            command.dispatch(msg, args, bot=self)
        else:
            self.raise_error(msg, CommandNotFound(f'Unknown command {command_name!r}'))
