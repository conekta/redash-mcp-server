import os
from collections.abc import Callable

from mcp.server.lowlevel.server import request_ctx

ApiKeyProvider = Callable[[], str]
REQUEST_API_KEY_ERROR = (
    "Redash API key is not set. Send it as Authorization: Key <key>."
)


def get_env_api_key() -> str:
    key = os.environ.get("REDASH_API_KEY")
    if not key:
        raise RuntimeError(
            "REDASH_API_KEY environment variable is not set. "
            "Set it to your Redash API key before running the server."
        )
    return key


def get_request_header_api_key() -> str:
    try:
        request_context = request_ctx.get()
    except LookupError as exc:
        raise RuntimeError(REQUEST_API_KEY_ERROR) from exc

    request = request_context.request
    if request is None:
        raise RuntimeError(REQUEST_API_KEY_ERROR)

    authorization = request.headers.get("authorization")
    if not authorization:
        raise RuntimeError(REQUEST_API_KEY_ERROR)

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "key" or not token:
        raise RuntimeError("Authorization header must use Key token format.")
    return token


_api_key_provider: ApiKeyProvider = get_env_api_key


def set_api_key_provider(provider: ApiKeyProvider) -> None:
    global _api_key_provider
    _api_key_provider = provider


def reset_api_key_provider() -> None:
    set_api_key_provider(get_env_api_key)


def get_api_key() -> str:
    return _api_key_provider()
