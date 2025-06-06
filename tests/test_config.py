import json
import os
import unittest

from loguru import logger
from server import Configurator

PROJECT_DIR = os.path.dirname(__file__)[:-5]


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.delete_log()
        self.rename_file("config.json", "config_temp.json")

    def tearDown(self):
        if os.path.exists(path := os.path.join(PROJECT_DIR, "config.json")):
            os.remove(path)
        self.rename_file("config_temp.json", "config.json")

    @staticmethod
    def create_config(config):
        path = os.path.join(PROJECT_DIR, "config.json")

        with open(path, "w") as file:
            json.dump(config, file)

    @staticmethod
    def delete_log():
        logger.remove()
        for file in os.listdir(os.path.dirname(__file__)):
            if file.endswith(".log"):
                os.remove(file)

    @staticmethod
    def rename_file(file_to_rename: str, rename_to: str):
        project_dir = os.path.dirname(__file__)[:-5]

        for file in os.listdir(project_dir):
            if file.endswith(file_to_rename):
                os.rename(os.path.join(project_dir, file), os.path.join(project_dir, rename_to))

    def test_with_no_config(self):
        with self.assertRaises(FileNotFoundError):
            Configurator()

    def test_config_no_dict(self):
        conf = [{}, {}]
        self.create_config(conf)

        with self.assertRaises(TypeError):
            Configurator()

    def test_without_log_config(self):
        conf = {"servers": [{"listen": 8080, "server_name": "localhost"}]}
        self.create_config(conf)
        Configurator()

        for file in os.listdir(os.path.dirname(__file__)):
            if file.endswith(".log"):
                with open(os.path.join(os.path.dirname(__file__), file), "r") as f:
                    log = f.read().split(" | ")[-1].strip()
                    self.assertEqual(log, "Standard logger configuration")
                break

        self.delete_log()

    def test_with_log_error(self):
        conf = {'server': {}}
        self.create_config(conf)
        configurator = Configurator()

        with self.assertRaises(KeyError):
            configurator.get_servers_config()

        self.delete_log()


if __name__ == '__main__':
    unittest.main()
