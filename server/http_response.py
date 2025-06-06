import mimetypes
import os
from collections import OrderedDict
from typing import Tuple

from aiohttp import ClientSession
from loguru import logger

from .constants import STATUS_CODES


class HTTPResponse:
    """
    create and manage http response
    """

    def __init__(self, server_config: dict) -> None:
        """
        init http response
        :param server_config: config of server that get request
        """
        self.server_config = server_config
        self.is_caching = True if server_config.get("is_caching") else False
        self.cache: OrderedDict[str, Tuple[int, dict, bytes]] = OrderedDict()
        self.max_cache_size = server_config.get("max_cache_size", 0)

    @logger.catch
    async def caching_file(self, key: str, value: Tuple[int, dict, bytes]) -> None:
        """
        put file in cache
        :param key: path to file
        :param value: status code, headers, body
        :return:
        """
        if value.__sizeof__() > self.max_cache_size:
            logger.warning(f"{key} is bigger than {self.max_cache_size} bytes")
            return

        while self.cache.__sizeof__() + value.__sizeof__() > self.max_cache_size:
            self.cache.popitem(last=False)

        self.cache[key] = value

    @logger.catch
    async def handle_return(self) -> Tuple[int, dict, bytes]:
        """
        handle response on return config
        :return: bytes of response
        """
        content = self.server_config["return"]
        if os.path.exists(content.strip()):
            status_code, headers, body = await self.load_file(content.strip())
        else:
            status_code, headers, body = 200, {"Content-Type": "text/plain"}, content.encode("utf-8")

        return status_code, headers, body

    @logger.catch
    async def handle_proxy_pass(self, parsed_request: dict[str, str]) -> Tuple[int, dict, bytes]:
        """
        handle proxy pass
        :param parsed_request: request from user
        :return: Tuple[status code, headers, body]
        """
        proxy_url = self.server_config["proxy_pass"] + parsed_request["path"]

        async with ClientSession() as session:
            try:
                async with session.request(
                    method=parsed_request["method"],
                    url=proxy_url,
                    headers={
                        key: val for key, val in parsed_request.items() if key not in ["method", "path", "protocol"]
                    },
                    timeout=self.server_config["timeout"],
                ) as response:
                    status_code, headers, body = response.status, dict(response.headers), await response.read()
                    return status_code, headers, body
            except Exception as exception:
                logger.error(f"Proxy request failed: {exception}")
                return 502, {"Content-Type": "text/plain"}, b"502 Bad Gateway"

    @logger.catch
    async def build_response(self, status_code: int, headers: dict, body: bytes) -> bytes:
        """
        build response
        :param status_code: int
        :param body: bytes
        :param headers: dict
        :return: bytes of response
        """
        headers["Content-Length"] = str(len(body))
        status_line = f"HTTP/1.1 {status_code} {STATUS_CODES[status_code]}\r\n"
        headers_lines = "".join([f"{key}: {value}\r\n" for key, value in headers.items()]) + "\r\n"
        response = (status_line + headers_lines).encode("utf-8") + body

        return response

    @logger.catch
    async def load_file(self, local_path: str) -> Tuple[int, dict, bytes]:
        """
        try to load file
        :param local_path: str
        :return: Tuple[status code, headers, file bytes]
        """
        if self.is_caching and self.cache.get(local_path):
            return self.cache[local_path]

        if not os.path.exists(local_path) or not os.path.isfile(local_path):
            logger.warning(f"File {local_path} does not exist")
            return 404, {}, b"<h1>404 Not Found</h1>"

        with open(local_path, "rb") as file:
            content = file.read()

        mime_type, _ = mimetypes.guess_type(local_path)
        headers = {"Content-Type": mime_type}

        if self.is_caching:
            await self.caching_file(local_path, (200, headers, content))

        return 200, headers, content

    @logger.catch
    async def generate_autoindex(self, server_path: str) -> Tuple[int, dict, bytes]:
        """
        generate autoindex for files if parameter is directory
        :param server_path: path of current directory from server
        :return: bytes of html with autoindex
        """
        status_code, local_path = await self.get_local_path(server_path)

        if not os.path.isdir(local_path) or status_code != 200:
            if status_code == 200:
                status_code, headers, body = await self.load_file(local_path)
                return status_code, headers, body
            else:
                return status_code, {}, f"<h1>{status_code}, {local_path}</h1>".encode("utf-8")

        hrefs = []
        for file in os.listdir(local_path):
            full_path = os.path.join(local_path, file)
            display_name = file if not os.path.isdir(full_path) else file + '/'
            href = server_path.rstrip("/") + "/" + file
            hrefs.append(f"<li><a href='{href}'>{display_name}</a></li>")

        html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Index of {server_path}</title></head>
            <body>
                <h1>
                    Index of {server_path}
                </h1>
                <ul>
                    {'\n'.join(hrefs)}
                </ul>
            </body>
            </html>
            """.encode(
            "utf-8"
        )

        return 200, {"Content-Type": "text/html"}, html

    @logger.catch
    async def get_local_path(self, server_path: str) -> Tuple[int, str]:
        """
        get correct path on local machine from server request
        :param server_path: path of current directory from server
        :return: Tuple[status code, path]
        """
        normalize_path = os.path.normpath(server_path).lstrip("/")
        local_path = self.server_config["root"] + normalize_path

        if not local_path.startswith(os.path.abspath(self.server_config["root"])):
            return 403, "Forbidden"
        if not os.path.exists(local_path):
            return 404, "Not Found"
        return 200, local_path
