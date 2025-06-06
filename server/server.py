import asyncio
import os.path
from asyncio import StreamReader, StreamWriter

from loguru import logger

from .http_response import HTTPResponse


class Server:
    """
    create and manage webserver
    """

    def __init__(self, config: dict) -> None:
        """
        init and configurate server
        :param config: server configuration
        """
        self.config = config
        self.check_config()
        self.set_default_config()
        logger.info(f"{self.config['server_name']}:{self.config['listen']} configurate")

    def check_config(self) -> None:
        """
        check, that all important attributes are set, overwise throw exception
        :return:
        """
        if type(self.config) is not dict:
            raise TypeError("Server config should be a dict")

        if not self.config.get("listen"):
            raise KeyError("Server configuration must include \"listen\" attribute")

        if not self.config.get("server_name"):
            raise KeyError("Server configuration must include \"server_name\" attribute")

    def set_default_config(self) -> None:
        """
        set default attributes, if they don't exist
        :return:
        """
        if not self.config.get("timeout"):
            self.config["timeout"] = 5

        if self.config.get("proxy_pass"):
            return

        if not self.config.get("root"):
            self.config["root"] = os.path.dirname(__file__)[:-6]

    @logger.catch
    async def server_callback(self, reader: StreamReader, writer: StreamWriter) -> None:
        """
        get user request and write response
        :param reader: reader user request
        :param writer: writer response for user request
        :return:
        """
        while True:
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=self.config["timeout"])
            except asyncio.TimeoutError:
                logger.info(f"Server {self.config['server_name']}:{self.config['listen']} timed out")
                break

            if not data:
                break

            request = data.decode("utf-8")
            parsed_request = await self.parse_request(request)

            if parsed_request:
                peername = writer.get_extra_info("peername")
                logger.info(
                    f"{parsed_request.get('host')}  |  Request from {peername}  |  "
                    f"{parsed_request.get('method')} {parsed_request.get('path')} {parsed_request.get('protocol')}  |  "
                    f"{parsed_request.get('user-agent')}"
                )

            response = await self.write_response(parsed_request)

            writer.write(response)
            await writer.drain()

            if parsed_request and (
                parsed_request.get("connection", "").lower() == "close"
                or parsed_request.get("protocol", "") == "HTTP/1.0"
            ):
                break

        writer.close()
        await writer.wait_closed()

    @logger.catch
    async def write_response(self, parsed_request: dict[str, str] | None = None) -> bytes:
        """
        create response from parsed request
        :param parsed_request: request from user
        :return:
        """
        response = HTTPResponse(self.config)

        if parsed_request is None:
            logger.info(f"400 : bad request on {parsed_request}")
            return await response.build_response(400, {}, b"400 Bad Request")

        if parsed_request["method"] not in ("GET", "HEAD"):
            logger.info(f"405 : Request method {parsed_request['method']} not allowed")
            return await response.build_response(405, {"Content-Type": "text/plain"}, b"405 Method Not Allowed")

        if self.config.get("proxy_pass"):
            status_code, headers, body = await response.handle_proxy_pass(parsed_request)
        elif self.config.get("return"):
            status_code, headers, body = await response.handle_return()
        elif self.config.get("autoindex"):
            status_code, headers, body = await response.generate_autoindex(parsed_request["path"])
        else:
            code, local_path = await response.get_local_path(parsed_request["path"])
            if code == 200:
                status_code, headers, body = await response.load_file(local_path)
            else:
                status_code, headers, body = 404, {}, b"404 Not Found"

        logger.info(
            f"{parsed_request['host']}  |  Response  |  "
            f"{parsed_request['method']} {parsed_request['path']} {parsed_request['protocol']}  |  "
            f"{status_code}"
        )

        if parsed_request["method"] == "HEAD":
            return await response.build_response(status_code, headers, b"")
        return await response.build_response(status_code, headers, body)

    @logger.catch
    async def start(self) -> None:
        """
        start server
        :return:
        """
        server = await asyncio.start_server(
            client_connected_cb=self.server_callback, host=self.config["server_name"], port=self.config["listen"]
        )

        logger.info(f"{self.config['server_name']} started and listening on {self.config['listen']}")

        async with server:
            await server.serve_forever()

    @staticmethod
    @logger.catch
    async def parse_request(request: str) -> dict[str, str] | None:
        """
        turn request from string to dict
        :param request: str
        :return: dict[str, str]
        """
        try:
            lines = request.split('\n')
            method, path, protocol = lines[0].split(" ", 2)
            result = {"method": method.strip(), "path": path.strip(), "protocol": protocol.strip()}

            for line in lines[1:]:
                split_line = line.split(':', 1)
                if len(split_line) == 2:
                    result[split_line[0].strip().lower()] = split_line[1].strip()

            return result
        except Exception:
            return None
