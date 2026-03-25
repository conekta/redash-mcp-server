from importlib import import_module

_INITIALIZED = False
_TOOL_MODULES = (
    "queries",
    "dashboards",
    "data_sources",
    "query_results",
    "users",
    "alerts",
    "visualizations",
    "schema",
)


def initialize() -> None:
    global _INITIALIZED

    if _INITIALIZED:
        return

    for module_name in _TOOL_MODULES:
        import_module(f"redash_mcp.tools.{module_name}")

    _INITIALIZED = True
