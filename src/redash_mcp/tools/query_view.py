import json
from typing import Any

_COMPACT_FIELDS = (
    "id",
    "name",
    "description",
    "data_source_id",
    "tags",
    "updated_at",
    "is_archived",
    "is_draft",
)

_USER_FIELDS = ("user", "last_modified_by")


def _dump(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def _load(raw: str) -> tuple[bool, Any]:
    try:
        return True, json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return False, None


def _is_error(payload: Any) -> bool:
    return isinstance(payload, dict) and payload.get("error") is True


def _public_user(user: Any) -> dict[str, Any] | None:
    if not isinstance(user, dict):
        return None
    return {"id": user.get("id"), "name": user.get("name")}


def sanitize_query(query: dict[str, Any]) -> dict[str, Any]:
    sanitized = {key: value for key, value in query.items() if key != "api_key"}
    for field in _USER_FIELDS:
        if field in sanitized:
            sanitized[field] = _public_user(sanitized[field])
    return sanitized


def compact_query(query: dict[str, Any], *, include_query: bool = False) -> dict[str, Any]:
    compact: dict[str, Any] = {field: query.get(field) for field in _COMPACT_FIELDS}
    user = query.get("user")
    compact["author"] = user.get("name") if isinstance(user, dict) else None
    if include_query:
        compact["query"] = query.get("query")
    return compact


def _compact_item(item: Any, *, include_query: bool) -> Any:
    if not isinstance(item, dict):
        return item
    return compact_query(item, include_query=include_query)


def compact_query_response(raw: str, *, include_query: bool = False) -> str:
    ok, payload = _load(raw)
    if not ok or _is_error(payload):
        return raw
    if isinstance(payload, list):
        return _dump([
            _compact_item(item, include_query=include_query) for item in payload
        ])
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        page = {
            key: payload[key]
            for key in ("count", "page", "page_size")
            if key in payload
        }
        page["results"] = [
            _compact_item(item, include_query=include_query) for item in payload["results"]
        ]
        return _dump(page)
    if isinstance(payload, dict):
        return _dump(compact_query(payload, include_query=include_query))
    return raw


def sanitize_query_response(raw: str) -> str:
    ok, payload = _load(raw)
    if not ok or _is_error(payload) or not isinstance(payload, dict):
        return raw
    return _dump(sanitize_query(payload))
