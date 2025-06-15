import os

import server


def remove_log() -> None:
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
    server.run_all()
