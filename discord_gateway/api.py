import logging as log
import json
import threading
from typing import Optional, Union

import requests
from requests import Response, JSONDecodeError

DISCORD_API = 'https://discord.com/api/v9'  # Current gateway api

__all__ = (
    'HttpClient',
)


def handle_api_response(resp: requests.Response) -> Union[Response, dict]:
    resp.raise_for_status()  # Raise errors
    try:
        body: json = resp.json()
        if 'errors' in body:
            raise Exception(body)
        return body
    except TypeError:
        return resp
    except JSONDecodeError:
        return resp


class HttpClient:
    def __init__(self, token: str, bot: bool = True) -> None:

        from discord_gateway.request_manager import RequestsManager  # Circular imports

        self._token: str = token
        self.is_bot = bot
        self.headers = {'Authorization': f'{"Bot " if bot else ""}{self._token}'}
        self.manager = RequestsManager(self)  # Request manager

    def requests(self, method: str, path: str, *, data: Union[str, dict, None] = None, headers: Optional[dict] = None,
                 threads: bool = False,
                 **kwargs) -> Union[Response, dict, None]:
        """
        Send a request using self api\n
        :param method: :class:`str`
            The method to use {uppercase}
        :param path: :class:`str`
            The path of the request
        :param data: :class:`Optional[Union[dict, str]]`
            Additional data for the requests
        :param headers: :class:`Optional[dict]`
            Headers to override
        :param threads: :class:`bool`
            Weather to use threads when requesting
        :param kwargs: :class:`dict`
            Additional params
        :return: :class:`Union[Response, dict]
            The response
        """
        url = f'{DISCORD_API}{path}'

        headers = headers or self.headers

        if threads:
            return threading.Thread(target=self.send, args=(method, url, data, headers), kwargs={**kwargs}).start()
        else:
            return self.send(method, url, data, headers, **kwargs)

    @staticmethod
    def send(method: str, url: str, data: Union[str, dict, None], headers: Optional[dict],
             **kwargs) -> Union[Response, dict, bool]:
        if 'json' in kwargs:
            log.debug(f'Sending payload - {kwargs["json"]} via method - {method}')
        elif data:
            log.debug(f'Sending payload - {data} via method - {method}')
        try:
            if method == "GET":
                resp = requests.get(url, headers=headers, **kwargs)
                return handle_api_response(resp)
            elif method == "PUT":
                resp = requests.put(url, headers=headers, **kwargs)
                return handle_api_response(resp)
            elif method == "POST":
                resp = requests.post(url, headers=headers, data=data, **kwargs)
                return handle_api_response(resp)
            elif method == "DELETE":
                resp = requests.delete(url, headers=headers, data=data, **kwargs)
                return handle_api_response(resp)
            elif method == "PATCH":
                session = requests.Session()
                resp = session.patch(url, headers=headers, data=data, **kwargs)
                return handle_api_response(resp)

            else:
                raise Exception("Unsupported HTTP method {method}")

        except requests.exceptions.HTTPError as e:

            from discord_gateway.exceptions import TooManyRequests

            match e.args[0].split(':')[0]:
                case '429 Client Error':
                    raise TooManyRequests()
                case _:
                    raise e

    def get_token(self) -> str:
        """
        Gets the api token\n
        :return: :class:`str`
            API token
        """
        return self._token

    def get_auth(self) -> str:
        """
        Get auth header\n
        :return: :class:`str`
            The formatted authorize header
        """
        return f'{"Bot " if self.is_bot else ""}{self._token}'
