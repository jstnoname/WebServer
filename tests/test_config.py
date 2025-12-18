import json
import os
import pathlib
import unittest
from typing import Any

from loguru import logger
from server import Configurator

PROJECT_DIR = pathlib.Path(__file__).parent.parent


class ConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.delete_log()
        self.rename_file("config.json", "config_temp.json")

    def tearDown(self) -> None:
        if os.path.exists(path := os.path.join(PROJECT_DIR, "config.json")):
            os.remove(path)
        self.rename_file("config_temp.json", "config.json")

    @staticmethod
    def create_config(config: dict[Any, Any] | list[dict[Any, Any]]) -> None:
        path = os.path.join(PROJECT_DIR, "config.json")

        with open(path, "w") as file:
            json.dump(config, file)

    @staticmethod
    def delete_log() -> None:
        logger.remove()
        for file in os.listdir(os.path.dirname(__file__)):
            if file.endswith(".log"):
                os.remove(file)

    @staticmethod
    def rename_file(file_to_rename: str, rename_to: str) -> None:
        for file in os.listdir(PROJECT_DIR):
            if file.endswith(file_to_rename):
                os.rename(os.path.join(PROJECT_DIR, file), os.path.join(PROJECT_DIR, rename_to))

    def test_with_no_config(self) -> None:
        with self.assertRaises(FileNotFoundError):
            Configurator()

    def test_config_no_dict(self) -> None:
        conf: list[dict[Any, Any]] = [{}, {}]
        self.create_config(conf)

        with self.assertRaises(TypeError):
            Configurator()

    def test_without_log_config(self) -> None:
        conf = {"servers": [{"listen": 8080, "server_name": "localhost"}]}
        self.create_config(conf)
        Configurator()

        for file in os.listdir(os.path.dirname(__file__)):
            if file.endswith(".log"):
                with open(os.path.join(os.path.dirname(__file__), file), "r") as f:
                    log = f.read().split(" | ")[-1].strip()
                    self.assertEqual(log, "Logger configured from default configuration")
                break

        self.delete_log()


if __name__ == '__main__':
    unittest.main()
