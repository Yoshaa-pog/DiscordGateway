"""
Discord Gateway framework

Check github at ...
"""

__title__ = 'DiscordGateway'
__author__ = 'zYoshaa'
__version__ = '2.0.1'

from .api import *
from .constants import *
from .discord_objects import *
from .discord_user import *
from .gatewaybot import *
from .gateway_handler import *
from .gateway import *
from .embed import *
from .request_manager import *
from .presence import *
from.guild_objects import *
from .exceptions import *
import logging as log

log.basicConfig(encoding='utf-8', level=log.ERROR)
