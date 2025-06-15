from typing import Any

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


AUTOINDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Index of {}</title></head>
<body>
    <h1>
        Index of {}
    </h1>
    <ul>
        {}
    </ul>
</body>
</html>
"""
