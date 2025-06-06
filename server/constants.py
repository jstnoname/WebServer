from typing import Any

STATUS_CODES = {
    200: "OK",
    301: "Moved Permanently",
    302: "Found",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error",
    502: "Bad Gateway",
}

DEFAULT_LOG_CONFIG: dict[Any, Any] = {
    "handlers": [
        {
            "sink": "{time}.log",
            "format": "{time} | {level} | {message}",
            "rotation": "00:00",
            "colorize": False,
            "serialize": False,
            "encoding": "utf-8",
        }
    ]
}
