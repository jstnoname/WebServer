import asyncio
import os
import unittest

from server import Server

PROJECT_DIR = os.path.dirname(__file__)[:-5]


class ServerTest(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def create_server_config(server_port: int | str):
        config = {
            "server_name": "localhost",
            "listen": server_port,
        }

        return config

    def test_server_config_not_dict(self):
        with self.assertRaises(TypeError):
            Server(config=[])

    def test_server_config_without_servername(self):
        config = {"listen": 80}

        with self.assertRaises(KeyError):
            Server(config=config)

    def test_server_config_without_port(self):
        config = {"server_name": "localhost"}

        with self.assertRaises(KeyError):
            Server(config=config)

    @staticmethod
    async def send_request(server_port):
        reader, writer = await asyncio.open_connection("localhost", server_port)
        writer.write(b"GET / HTTP/1.1\r\n" b"Host: localhost\r\n" b"Connection: close\r\n\r\n")
        await writer.drain()

        response = await reader.read()
        writer.close()
        await writer.wait_closed()
        return response

    @staticmethod
    async def send_bad_request(server_port):
        reader, writer = await asyncio.open_connection("localhost", server_port)
        writer.write(b"BADREQUEST /index.html\r\n\r\n")
        await writer.drain()

        response = await reader.read()
        writer.close()
        await writer.wait_closed()
        return response

    @staticmethod
    async def send_not_allowed_request(server_port):
        reader, writer = await asyncio.open_connection("localhost", server_port)
        writer.write(b"POST / HTTP/1.1\r\n" b"Host: localhost\r\n" b"Connection: close\r\n\r\n")
        await writer.drain()

        response = await reader.read()
        writer.close()
        await writer.wait_closed()
        return response

    async def test_few_servers(self):
        config1 = self.create_server_config(8080)
        config2 = self.create_server_config(8888)

        server1 = asyncio.create_task(Server(config1).start())
        server2 = asyncio.create_task(Server(config2).start())

        try:
            response1 = await self.send_request(config1["listen"])
            response2 = await self.send_request(config2["listen"])

            self.assertEqual(response1, b'HTTP/1.1 404 Not Found\r\nContent-Length: 22\r\n\r\n<h1>404 Not Found</h1>')
            self.assertEqual(response2, b'HTTP/1.1 404 Not Found\r\nContent-Length: 22\r\n\r\n<h1>404 Not Found</h1>')
        finally:
            server1.cancel()
            server2.cancel()

    async def test_send_bad_request(self):
        config = self.create_server_config(8080)
        server = asyncio.create_task(Server(config).start())

        try:
            response = await self.send_bad_request(config["listen"])

            self.assertEqual(response, b"HTTP/1.1 400 Bad Request\r\nContent-Length: 15\r\n\r\n400 Bad Request")
        finally:
            server.cancel()

    async def test_send_not_allowed_request(self):
        config = self.create_server_config(8080)
        server = asyncio.create_task(Server(config).start())

        try:
            response = await self.send_not_allowed_request(config["listen"])

            self.assertEqual(
                response,
                b"HTTP/1.1 405 Method Not Allowed\r\n"
                b"Content-Type: text/plain\r\n"
                b"Content-Length: 22\r\n"
                b"\r\n"
                b"405 Method Not Allowed",
            )
        finally:
            server.cancel()


if __name__ == '__main__':
    unittest.main()
