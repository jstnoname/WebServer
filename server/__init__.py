import asyncio

from loguru import logger

from .config_loader import Configurator
from .server import Server


@logger.catch
async def run_all():
    """
    start all processes
    :return:
    """
    configurator = Configurator()
    config = configurator.get_servers_config()
    tasks = []
    servers_ports = set()

    for server_config in config:
        if server_config["listen"] in servers_ports:
            logger.warning(f"Port {server_config['listen']} is already listening")
            continue
        new_server = Server(server_config)
        servers_ports.add(server_config["listen"])
        tasks.append(asyncio.create_task(new_server.start()))

    await asyncio.gather(*tasks)
