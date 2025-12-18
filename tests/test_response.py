import os
import unittest
from http import HTTPStatus
from typing import Any

from server.http_response import HTTPResponse
from server.model import Config, Response


class ResponseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = os.path.join(os.path.dirname(__file__)[:-5], "static")
        self.existing_file = os.path.join(self.root, "index.html")
        self.non_existing_file = os.path.join(self.root, "not_found.html")
        server_config: dict[Any, Any] = {
            "root": self.root,
            "_cache": True,
            "_max_cache_size": 1024,
            "autoindex": True,
            "server_name": "localhost",
            "listen": 8080,
        }
        config = Config.ServerConfig(**server_config)
        self.response = HTTPResponse(config)

    async def test_file_caching(self) -> None:
        await self.response._caching_file(
            self.existing_file,
            Response(status=HTTPStatus.OK, headers={"Content-Type": "text/html"}, body=b"<html>Cached</html>"),
        )

        self.assertIn(self.existing_file, self.response._cache.keys())
        self.assertEqual(self.response._cache[self.existing_file].body, b"<html>Cached</html>")

    async def test_load_file_success(self) -> None:
        response = await self.response.load_file(self.existing_file)

        self.assertEqual(response.status, 200)
        self.assertIn("Content-Type", response.headers)
        self.assertTrue(response.body.startswith(b"<"))

    async def test_load_file_not_found(self) -> None:
        response = await self.response.load_file(self.non_existing_file)

        self.assertEqual(response.status, 404)
        self.assertIn(b"404", response.body)

    async def test_generate_autoindex(self) -> None:
        response = await self.response.generate_autoindex("/")

        self.assertEqual(response.status, 200)
        self.assertIn(b"<html>", response.body)
        self.assertIn(b"<li><a href=", response.body)


if __name__ == '__main__':
    unittest.main()
