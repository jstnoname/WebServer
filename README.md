# WebServer

---
## Description
This **WebServer** is a simplified version of [nginx](https://nginx.org), implemented in Python.

---
## Author
**Александр Спирин ФТ-104**

---
## Downloading and Start Project

### Download project

```bash
git clone https://github.com/jstnoname/PythonTaskWebServer.git
cd PythonTaskWebServer
```

### Install Requirements

```bash
pip install -r requirements.txt
```

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

---
- [x] Добавлен `.gitignore`. Убедитесь, что там есть `.venv` и `.idea`
- [x] Создано виртуальное окружение
- [x] Есть файл `requirements.txt` или `pyproject.toml`. Исключения: если у вас нет внешних зависимостей.
- [x] Настроены линтеры: `mypy` и `flake8`
- [x] Настроены форматтеры: `isort` и `black`
- [x] Написаны тесты
- [x] Написана документация к каждому методу, классу и функции
- [x] Написан красивый `README.md` (для форматирования можно использовать markdown), где есть информация о том, как проект установить и запустить, что он делает и умеет, какие функции там есть
- [x] (Опционально) Есть прекоммит
