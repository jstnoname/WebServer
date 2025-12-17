import pathlib
from http import HTTPStatus
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .constants import DEFAULT_LOG_CONFIG


class Config(BaseModel):
    class ServerConfig(BaseModel):
        server_name: str
        listen: int

        root: str = Field(default=str(pathlib.Path(__file__).parent.parent))
        autoindex: bool = False
        timeout: int = 5
        cache: bool = False
        max_cache_size: int = 0
        proxy_pass: str | None = None
        return_path: str | None = Field(default=None, alias='return')

        @classmethod
        @field_validator('listen', mode='before')
        def validate_listen(cls, value: str | int) -> int:
            if isinstance(value, str) and str.isdigit(value):
                return int(value)
            if isinstance(value, int):
                return value
            raise TypeError("Listen must be an integer")

        @classmethod
        @field_validator('max_cache_size', mode='before')
        def validate_cache_size(cls, value: str | int | bytes) -> int | bytes:
            if isinstance(value, str) and value.isdigit():
                return int(value)
            if isinstance(value, int) or isinstance(value, bytes):
                return value
            raise TypeError("Listen must be an integer or bytes")

        @classmethod
        @field_validator("server_name", mode='before')
        def validate_server_name(cls, value: str) -> str:
            if isinstance(value, str):
                return value
            raise TypeError("Server name must specified")

    servers: list[ServerConfig] = Field(alias='servers')
    log_config: dict[Any, Any] = Field(default=DEFAULT_LOG_CONFIG, alias='log')


class Response(BaseModel):
    status: HTTPStatus
    headers: dict[str, str]
    body: bytes
