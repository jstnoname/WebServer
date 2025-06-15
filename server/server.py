import asyncio
from asyncio import StreamReader, StreamWriter
from http import HTTPStatus

from loguru import logger

from .http_response import HTTPResponse
from .model import Config, Response


class Server:
    """
    create and manage webserver
    """

    def __init__(self, config: Config.ServerConfig) -> None:
        """
        init and configurate server
        :param config: server configuration
        """
        self._config = config
        logger.info(f"{self._config.server_name}:{self._config.listen} configurate")

    @logger.catch
    async def _server_callback(self, reader: StreamReader, writer: StreamWriter) -> None:
        """
        get user request and write response
        :param reader: reader user request
        :param writer: writer response for user request
        :return:
        """
        while True:
            data = bytes(0)
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=self._config.timeout)
            except asyncio.TimeoutError:
                logger.info(f"Server {self._config.server_name}:{self._config.listen} timed out")
                break

            if not data:
                break

            request = data.decode("utf-8")
            parsed_request = await self._parse_request(request)

            if parsed_request:
                peername = writer.get_extra_info("peername")
                logger.info(
                    f"{parsed_request.get('host')}  |  Request from {peername}  |  "
                    f"{parsed_request.get('method')} {parsed_request.get('path')} {parsed_request.get('protocol')}  |  "
                    f"{parsed_request.get('user-agent')}"
                )

            response = await self._write_response(parsed_request)

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
    async def _write_response(self, parsed_request: dict[str, str] | None = None) -> bytes:
        """
        create response from parsed request
        :param parsed_request: request from user
        :return:
        """
        http_response = HTTPResponse(self._config)

        if parsed_request is None:
            logger.info(f"400 : bad request on {parsed_request}")
            response = Response(
                status=HTTPStatus.BAD_REQUEST, headers={"Content-Type": "text/plain"}, body=b"400 Bad Request"
            )
            return await http_response.build_response(response)

        if parsed_request["method"] not in ("GET", "HEAD"):
            logger.info(f"405 : Request method {parsed_request['method']} not allowed")
            response = Response(
                status=HTTPStatus.METHOD_NOT_ALLOWED,
                headers={"Content-Type": "text/plain"},
                body=b"405 Method Not Allowed",
            )
            return await http_response.build_response(response)

        if self._config.proxy_pass:
            response = await http_response.handle_proxy_pass(parsed_request)
        elif self._config.return_path:
            response = await http_response.handle_return()
        elif self._config.autoindex:
            response = await http_response.generate_autoindex(parsed_request["path"])
        else:
            code, local_path = await http_response.get_local_path(parsed_request["path"])
            if code == 200:
                response = await http_response.load_file(local_path)
            else:
                response = Response(
                    status=HTTPStatus.NOT_FOUND, headers={"Content-Type": "text/plain"}, body=b"404 Not Found"
                )

        logger.info(
            f"{parsed_request['host']}  |  Response  |  "
            f"{parsed_request['method']} {parsed_request['path']} {parsed_request['protocol']}  |  "
            f"{response.status}"
        )

        if parsed_request["method"] == "HEAD":
            response.body = b''
            return await http_response.build_response(response)
        return await http_response.build_response(response)

    @logger.catch
    async def start(self) -> None:
        """
        start server
        :return:
        """
        server = await asyncio.start_server(
            client_connected_cb=self._server_callback, host=self._config.server_name, port=self._config.listen
        )

        logger.info(f"{self._config.server_name} started and listening on {self._config.listen}")

        async with server:
            await server.serve_forever()

    @staticmethod
    @logger.catch
    async def _parse_request(request: str) -> dict[str, str] | None:
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
            logger.exception(f"Error on parsing request {request}")
            return None
