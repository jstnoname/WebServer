import asyncio
import os

import server


def remove_log():
    """
    remove files with .log extension
    lazy remove logs on each start
    :return:
    """
    directory = os.path.dirname(os.path.abspath(__file__))

    for filename in os.listdir(directory):
        if filename.endswith(".log"):
            path = os.path.join(directory, filename)
            os.remove(path)


if __name__ == "__main__":
    remove_log()
    asyncio.run(server.run_all())
