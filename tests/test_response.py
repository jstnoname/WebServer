import os
import unittest

from server.http_response import HTTPResponse


class ResponseTest(unittest.TestCase):
    def setUp(self):
        self.root = os.path.join(os.path.dirname(__file__)[:-5], "static")
        self.existing_file = os.path.join(self.root, "index.html")
        self.non_existing_file = os.path.join(self.root, "not_found.html")
        self.server_config = {
            "root": self.root,
            "cache": True,
            "max_cache_size": 1024,
            "autoindex": True,
            "server_name": "localhost",
            "listen": 8080,
        }
        self.response = HTTPResponse(self.server_config)

    async def test_file_caching(self):
        await self.response.caching_file(
            self.existing_file, (200, {"Content-Type": "text/html"}, b"<html>Cached</html>")
        )

        self.assertIn(self.existing_file, self.response.cache.keys())
        self.assertEqual(self.response.cache[self.existing_file][2], b"<html>Cached</html>")

    async def test_load_file_success(self):
        status, headers, body = await self.response.load_file(self.existing_file)

        self.assertEqual(status, 200)
        self.assertIn("Content-Type", headers)
        self.assertTrue(body.startswith(b"<"))

    async def test_load_file_not_found(self):
        status, headers, body = await self.response.load_file(self.non_existing_file)

        self.assertEqual(status, 404)
        self.assertIn(b"404", body)

    async def test_generate_autoindex(self):
        status, headers, body = await self.response.generate_autoindex("/")

        self.assertEqual(status, 200)
        self.assertIn(b"<html>", body)
        self.assertIn(b"<li><a href=", body)


if __name__ == '__main__':
    unittest.main()
