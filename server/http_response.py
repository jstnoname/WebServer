import mimetypes
import pathlib
from collections import OrderedDict
from http import HTTPStatus
from typing import Tuple

from aiohttp import ClientSession, ClientTimeout
from loguru import logger

from .constants import AUTOINDEX_TEMPLATE
from .model import Config, Response


class HTTPResponse:
    """
    create and manage http response
    """

    def __init__(self, server_config: Config.ServerConfig) -> None:
        """
        init http response
        :param server_config: config of server that get request
        """
        self._server_config = server_config
        self._cache: OrderedDict[str, Response] = OrderedDict()
        self._max_cache_size = server_config.max_cache_size

    @logger.catch
    async def _caching_file(self, key: str, value: Response) -> None:
        """
        put file in _cache
        :param key: path to file
        :param value: status code, headers, body
        :return:
        """
        if value.__sizeof__() > self._max_cache_size:
            logger.warning(f"{key} is bigger than {self._max_cache_size} bytes")
            return

        while self._cache.__sizeof__() + value.__sizeof__() > self._max_cache_size:
            self._cache.popitem(last=False)

        self._cache[key] = value

    @logger.catch
    async def handle_return(self) -> Response:
        """
        handle response on return config
        :return: bytes of response
        """
        content = str(self._server_config.return_path).strip()
        if pathlib.Path(content).exists():
            response = await self.load_file(content)
        else:
            status_code, headers, body = HTTPStatus.OK, {"Content-Type": "text/plain"}, content.encode("utf-8")
            response = Response(status=status_code, headers=headers, body=body)

        return response

    @logger.catch
    async def handle_proxy_pass(self, parsed_request: dict[str, str]) -> Response:
        """
        handle proxy pass
        :param parsed_request: request from user
        :return: Response
        """
        proxy_url = str(self._server_config.proxy_pass) + parsed_request["path"]
        timeout = ClientTimeout(total=self._server_config.timeout)

        async with ClientSession() as session:
            try:
                async with session.request(
                    method=parsed_request["method"],
                    url=proxy_url,
                    headers={
                        key: val for key, val in parsed_request.items() if key not in ["method", "path", "protocol"]
                    },
                    timeout=timeout,
                ) as proxy_response:
                    response = Response(
                        status=HTTPStatus(proxy_response.status),
                        headers=dict(proxy_response.headers),
                        body=await proxy_response.read(),
                    )
                    return response
            except Exception as exception:
                logger.error(f"Proxy request failed: {exception}")
                response = Response(
                    status=HTTPStatus.BAD_GATEWAY, headers={"Content-Type": "text/plain"}, body=b"502 Bad Gateway"
                )
                return response

    @logger.catch
    async def build_response(self, response: Response) -> bytes:
        """
        build response
        :param response: model of response
        :return: bytes of response
        """
        response.headers["Content-Length"] = str(len(response.body))
        status_line = f"HTTP/1.1 {response.status} {response.status.phrase}\r\n"
        headers_lines = "".join([f"{key}: {value}\r\n" for key, value in response.headers.items()]) + "\r\n"
        built_response = (status_line + headers_lines).encode("utf-8") + response.body

        return built_response

    @logger.catch
    async def load_file(self, local_path: str) -> Response:
        """
        try to load file
        :param local_path: str
        :return: Response of loading file
        """
        if self._server_config.cache and self._cache.get(local_path):
            return self._cache[local_path]

        if not (pathlib.Path(local_path).exists() and pathlib.Path(local_path).is_file()):
            logger.warning(f"File {local_path} does not exist")
            response = Response(status=HTTPStatus.NOT_FOUND, headers={}, body=b"<h1>404 Not Found</h1>")
            return response

        with open(local_path, "rb") as file:
            content = file.read()

        mime_type, _ = mimetypes.guess_type(local_path)
        headers = {"Content-Type": mime_type or "text/html"}

        response = Response(
            status=HTTPStatus.OK,
            headers=headers,
            body=content,
        )

        if self._server_config.cache:
            await self._caching_file(local_path, response)

        return response

    @logger.catch
    async def generate_autoindex(self, server_path: str) -> Response:
        """
        generate autoindex for files if parameter is directory
        :param server_path: path of current directory from server
        :return: bytes of html with autoindex
        """
        status_code, local_path = await self.get_local_path(server_path)

        if status_code == HTTPStatus.OK and pathlib.Path(local_path).is_file():
            response = await self.load_file(local_path)
            return response
        elif status_code == HTTPStatus.OK and pathlib.Path(local_path).is_dir():
            hrefs = []
            for file in pathlib.Path(local_path).iterdir():
                display_name = str(file.name) if pathlib.Path(file).is_file() else str(file.name) + '/'
                href = server_path.rstrip("/") + "/" + str(file.name)
                hrefs.append(f"<li><a href='{href}'>{display_name}</a></li>")

            html = AUTOINDEX_TEMPLATE.format(server_path, server_path, '\n'.join(hrefs)).encode("utf-8")

            response = Response(
                status=HTTPStatus.OK,
                headers={"Content-Type": "text/html"},
                body=html,
            )

            return response
        else:
            response = Response(
                status=status_code,
                headers={"Content-Type": "text/html"},
                body=f"{status_code} {status_code.phrase}".encode("utf-8"),
            )

            return response

    @logger.catch
    async def get_local_path(self, server_path: str) -> Tuple[HTTPStatus, str]:
        """
        get correct path on local machine from server request
        :param server_path: path of current directory from server
        :return: status code, path
        """
        local_path = str(pathlib.Path(self._server_config.root).joinpath(server_path.lstrip("/")))

        if not local_path.startswith(self._server_config.root):
            return HTTPStatus.FORBIDDEN, ''
        if not pathlib.Path(local_path).exists():
            return HTTPStatus.NOT_FOUND, ''
        return HTTPStatus.OK, local_path
