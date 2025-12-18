import json
import pathlib

from loguru import logger

from .model import Config


class Configurator:
    """
    find and configurate webserver and logs
    """

    def __init__(self) -> None:
        """
        find config file in project directory and configurate logs
        """
        self._config_path = self._find_config()
        self._config = self._parse_config()
        self._configurate_logs()

    @staticmethod
    def _find_config() -> str:
        """
        find config.json file in project root directory
        :return: path to config file
        """
        directory = pathlib.Path(__file__).parent.parent

        for filename in directory.glob('*config.json'):
            logger.info(f"Found config file, path: {filename}")
            return str(filename)

        raise FileNotFoundError(
            "Configuration file was not found. Create or move configurate file in project root directory"
        )

    def _parse_config(self) -> Config:
        """
        parse config.json
        :return:
        """
        if self._config_path is not None and pathlib.Path(self._config_path).exists():
            with open(self._config_path, "r") as file:
                config_dict = json.load(file)
                config = Config(**config_dict)
                logger.info(f"Config loaded from {self._config_path}")
                return config
        raise FileNotFoundError(
            "Configuration file was not found. Create or move configurate file in project root directory"
        )

    def _configurate_logs(self) -> None:
        """
        configurate logging

        using Loguru for logging, for docs look on GitHub: https://github.com/Delgan/loguru

        if logs config was not determined, configuration will be standard
        :return:
        """
        logger.configure(**self._config.log_config)
        if "log_config" not in self._config.model_fields_set:
            logger.info("Logger configured from default configuration")
        else:
            logger.info("Logger configured from server configuration")

    def get_servers_config(self) -> list[Config.ServerConfig]:
        """
        get servers configuration
        :return:
        """
        if self._config.servers:
            return self._config.servers
        raise KeyError("Servers config not found")
