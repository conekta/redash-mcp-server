import json

import httpx
import pytest

from redash_mcp.tools.schema import (
    get_foreign_keys,
    get_table_columns,
    infer_table_relationships,
)

_QUERY_RESULT_RESPONSE = {
    "query_result": {
        "id": 1,
        "data": {
            "columns": [
                {"name": "schema_name", "type": None},
                {"name": "table_name", "type": None},
                {"name": "column_name", "type": None},
                {"name": "data_type", "type": None},
                {"name": "ordinal_position", "type": "integer"},
            ],
            "rows": [
                {
                    "schema_name": "public",
                    "table_name": "orders",
                    "column_name": "id",
                    "data_type": "int4",
                    "ordinal_position": 1,
                },
                {
                    "schema_name": "public",
                    "table_name": "orders",
                    "column_name": "customer_id",
                    "data_type": "varchar",
                    "ordinal_position": 2,
                },
            ],
        },
    }
}

_FK_RESPONSE = {
    "query_result": {
        "id": 2,
        "data": {
            "columns": [
                {"name": "schema_name", "type": None},
                {"name": "table_name", "type": None},
                {"name": "column_name", "type": None},
                {"name": "foreign_schema_name", "type": None},
                {"name": "foreign_table_name", "type": None},
                {"name": "foreign_column_name", "type": None},
            ],
            "rows": [
                {
                    "schema_name": "public",
                    "table_name": "orders",
                    "column_name": "customer_id",
                    "foreign_schema_name": "public",
                    "foreign_table_name": "customers",
                    "foreign_column_name": "id",
                },
            ],
        },
    }
}

_INFER_RESPONSE = {
    "query_result": {
        "id": 3,
        "data": {
            "columns": [
                {"name": "source_schema", "type": None},
                {"name": "source_table", "type": None},
                {"name": "source_column", "type": None},
                {"name": "target_schema", "type": None},
                {"name": "target_table", "type": None},
                {"name": "target_column", "type": None},
            ],
            "rows": [
                {
                    "source_schema": "public",
                    "source_table": "orders",
                    "source_column": "customer_id",
                    "target_schema": "public",
                    "target_table": "customer",
                    "target_column": "id",
                },
            ],
        },
    }
}


@pytest.mark.asyncio
async def test_get_table_columns(mock_api):
    mock_api.post("/api/query_results").mock(
        return_value=httpx.Response(200, json=_QUERY_RESULT_RESPONSE)
    )
    result = await get_table_columns(data_source_id=11)
    data = json.loads(result)
    rows = data["query_result"]["data"]["rows"]
    assert len(rows) == 2
    assert rows[0]["table_name"] == "orders"
    assert rows[1]["column_name"] == "customer_id"


@pytest.mark.asyncio
async def test_get_table_columns_with_filters(mock_api):
    route = mock_api.post("/api/query_results").mock(
        return_value=httpx.Response(200, json=_QUERY_RESULT_RESPONSE)
    )
    await get_table_columns(
        data_source_id=11, schema_name="public", table_name="orders"
    )
    request_body = json.loads(route.calls[0].request.content)
    assert "n.nspname = 'public'" in request_body["query"]
    assert "c.relname = 'orders'" in request_body["query"]


@pytest.mark.asyncio
async def test_get_foreign_keys(mock_api):
    mock_api.post("/api/query_results").mock(
        return_value=httpx.Response(200, json=_FK_RESPONSE)
    )
    result = await get_foreign_keys(data_source_id=11)
    data = json.loads(result)
    rows = data["query_result"]["data"]["rows"]
    assert len(rows) == 1
    assert rows[0]["foreign_table_name"] == "customers"


@pytest.mark.asyncio
async def test_get_foreign_keys_with_filter(mock_api):
    route = mock_api.post("/api/query_results").mock(
        return_value=httpx.Response(200, json=_FK_RESPONSE)
    )
    await get_foreign_keys(data_source_id=11, schema_name="public")
    request_body = json.loads(route.calls[0].request.content)
    assert "n.nspname = 'public'" in request_body["query"]


@pytest.mark.asyncio
async def test_infer_table_relationships(mock_api):
    mock_api.post("/api/query_results").mock(
        return_value=httpx.Response(200, json=_INFER_RESPONSE)
    )
    result = await infer_table_relationships(data_source_id=11)
    data = json.loads(result)
    rows = data["query_result"]["data"]["rows"]
    assert len(rows) == 1
    assert rows[0]["source_column"] == "customer_id"
    assert rows[0]["target_table"] == "customer"


@pytest.mark.asyncio
async def test_infer_table_relationships_with_schema(mock_api):
    route = mock_api.post("/api/query_results").mock(
        return_value=httpx.Response(200, json=_INFER_RESPONSE)
    )
    await infer_table_relationships(data_source_id=11, schema_name="external")
    request_body = json.loads(route.calls[0].request.content)
    assert "src.nspname = 'external'" in request_body["query"]
