# WebServer

---
## Description
This **WebServer** is a simplified version of [nginx](https://nginx.org), implemented in Python.

---
## Downloading and Start Project

### Download project

```bash
git clone https://github.com/jstnoname/PythonTaskWebServer.git
cd PythonTaskWebServer
```

### Install Requirements
To install dependencies run ``poetry install`` in terminal.<br>
If you don't have poetry at first install it via ``pip install poetry``

### Creating Configuration of Webservers

Create file that will end with ``config.json`` in project root directory. For example ``config.json`` or
``my_servers_config.json``. Config file should have ``.json`` extension and have next structure: <br>
```
{
    "log" : {} <- optional
    "servers" :
        [
            {
                "listen" <- string or int of server port
                "timeout" <- string or int of server timeout. That need to keep-alive or proxy using
                "server_name" <- server address
                "root" : "C:\\Users\\Alexander\\PycharmProjects\\PythonTaskWebServer\\static" <- root of server
                "autoindex" <- bool. If true create autoindex
                "cache" <- bool. Creating cache of recent loaded files
                "max_cache_size" <- int | byte. Max size of files cache
                "proxy_pass" <- address that will redirect requests and response
                "return" <- return file or text on visiting server
            }, <- this dict is server config
            { } <- there can be more different servers configs
        ]
} <- dictionary
```
- The ``log`` section is optional. If omitted, the server will use default logging settings. For advanced options, see
[Loguru documentation](https://github.com/Delgan/loguru)
- The ``servers`` section is required and must contain a list of dictionaries — each dictionary defines a virtual
server.
- server config must have ``server_name`` and ``listen`` keys. ``root`` and ``timeout`` will have default value
if value not set in config
- ``proxy_pass``, ``return`` and ``autoindex`` options are mutually exclusive and should not be used together in the
same server config

### Start Server
For start server run ``main.py`` or write
```bash
python main.py
```

---
## Testing Project
To run tests write ``python -m unittest discover tests``
