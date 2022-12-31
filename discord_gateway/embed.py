import os
from dataclasses import dataclass
from typing import Union, Optional, Any

from discord_gateway import constants

__all__ = (
    'Embed',
    'DiscordFile',
)


@dataclass
class Author:
    __slots__ = 'name', 'url', 'icon_url'

    name: str
    url: Optional[str]
    icon_url: Optional[bytes]


class Embed:
    __slots__ = 'title', 'description', 'url', 'color', 'timestamp', 'fields', 'author', 'footer'

    def __init__(self, title: str, description: str = '', *, url: str = '',
                 color: Union[constants.Color, int] = constants.Color.Default) -> None:
        self.title = title
        self.description = description
        self.url = url
        self.color = color.value
        self.author: Optional[dict] = None
        self.footer: Optional[dict] = None
        self.fields: list[dir] = []

    def add_field(self, name: str, value: str, inline: bool = True) -> None:
        """
        Add a field to the embed\n
        :param name:
            Name of field
        :type name: str
        :param value:
            Value of field
        :type value: str
        :param inline:
            Weather or not the field should be inlined
        :type inline: bool
        """
        self.fields.append(
            {
                'name': name,
                'value': value,
                'inline': inline,
            }
        )

    def set_author(self, name: str, url: Optional[str] = None, icon_url: Optional[str] = None) -> None:
        """
        Sets the author for the embed\n
        :param name:
            Name of author
        :type name: str
        :param url:
            url for author
        :type url: Optional[str]
        :param icon_url:
            Avatar url of author
        :type icon_url: Optional[str]
        """
        author = Author(name, url, bytes(icon_url) if icon_url else None)
        self.author: dict = {
            attr: getattr(author, attr)
            for attr in author.__slots__
            if hasattr(author, attr)
        }

    def set_footer(self, *, content: Optional[str] = None, icon_url: Optional[Any] = None) -> None:
        """
        Sets the footer of the embed\n
        :param content:
            The footer text
        :param icon_url:
            Url for the footer icon
        """
        self.footer = {}

        if content is not None:
            self.footer['text'] = content

        if icon_url:
            self.footer['icon_url'] = str(icon_url)

    def to_json(self) -> dict:
        """
        Converts the embed to dict\n
        :return:
            Dict formatted embed
        """
        return {
            key: getattr(self, key)
            for key in self.__slots__
            if hasattr(self, key)
        }


class DiscordFile:

    def __init__(self, path: Union[str, bytes, os.PathLike], filename: Optional[str] = None) -> None:
        self.path = open(path, 'rb')
        self.filename = filename or self.path.name

    def to_json(self) -> dict:
        return {
            'file': (self.filename, self.path)
        }
