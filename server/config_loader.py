import json
import os

from loguru import logger

from .constants import DEFAULT_LOG_CONFIG


class Configurator:
    """
    find and configurate webserver and logs
    """

    def __init__(self):
        """
        find config file in project directory and configurate logs
        """
        self.config_path = self.find_config()
        self.config = self.parse_config()
        self.configurate_logs()

    @staticmethod
    def find_config() -> str:
        """
        find config.json file in project root directory
        :return:
        """
        directory = os.path.dirname(__file__)[:-6]

        for filename in os.listdir(directory):
            if filename.endswith("config.json"):
                path = os.path.join(directory, filename)
                logger.info(f"Found config file, path: {path}")
                return path

        raise FileNotFoundError(
            "Configuration file was not found. Create or move config.json file in project root directory."
        )

    def parse_config(self) -> dict:
        """
        parse config.json
        :return:
        """
        if self.config_path is not None and os.path.exists(self.config_path):
            with open(self.config_path, "r") as file:
                config = json.load(file)
                if type(config) is dict:
                    logger.info(f"Load config file, path: {self.config_path}")
                    return config
                raise TypeError("config.json should be a dict.")
        raise FileNotFoundError(
            "Configuration file was not found. Create or move config.json file in project root directory."
        )

    def configurate_logs(self) -> None:
        """
        configurate logging

        using Loguru for logging, for docs look on GitHub: https://github.com/Delgan/loguru

        if logs config was not determined, configuration will be standard
        :return:
        """
        try:
            logger.configure(**self.config["log"])
            logger.info("Logger configured from server config")
            return
        except KeyError:
            logger.info("Logger config not found")
        except TypeError as exception:
            logger.error(f"Logger config wrong: {exception}")
        except Exception as exception:
            logger.error(f"Fatal error: {exception}")

        logger.configure(**DEFAULT_LOG_CONFIG)

        logger.info("Standard logger configuration")

    def get_servers_config(self) -> list:
        """
        get servers configuration
        :return:
        """
        if "servers" in self.config and type(self.config["servers"]) is list:
            return self.config["servers"]
        raise KeyError("servers config was not found.")
