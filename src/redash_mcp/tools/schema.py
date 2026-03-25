import json

from redash_mcp.client import redash_request
from redash_mcp.server import mcp

_COLUMN_DETAIL_SQL = """
SELECT
  n.nspname AS schema_name,
  c.relname AS table_name,
  a.attname AS column_name,
  t.typname AS data_type,
  a.attnum AS ordinal_position
FROM pg_catalog.pg_attribute a
JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
JOIN pg_catalog.pg_type t ON a.atttypid = t.oid
WHERE a.attnum > 0
  AND NOT a.attisdropped
  AND n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_internal')
  AND c.relkind = 'r'
  {filter_clause}
ORDER BY n.nspname, c.relname, a.attnum;
"""

_FK_SQL = """
SELECT
  n.nspname AS schema_name,
  c.relname AS table_name,
  a.attname AS column_name,
  fn.nspname AS foreign_schema_name,
  fc.relname AS foreign_table_name,
  fa.attname AS foreign_column_name
FROM pg_catalog.pg_constraint con
JOIN pg_catalog.pg_class c ON con.conrelid = c.oid
JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
JOIN pg_catalog.pg_attribute a
  ON a.attrelid = con.conrelid AND a.attnum = ANY(con.conkey)
JOIN pg_catalog.pg_class fc ON con.confrelid = fc.oid
JOIN pg_catalog.pg_namespace fn ON fc.relnamespace = fn.oid
JOIN pg_catalog.pg_attribute fa
  ON fa.attrelid = con.confrelid AND fa.attnum = ANY(con.confkey)
WHERE con.contype = 'f'
  {filter_clause}
ORDER BY n.nspname, c.relname, a.attname;
"""

_INFER_RELATIONSHIPS_SQL = """
SELECT DISTINCT
  src.nspname AS source_schema,
  src_c.relname AS source_table,
  src_a.attname AS source_column,
  tgt.nspname AS target_schema,
  tgt_c.relname AS target_table,
  'id' AS target_column
FROM pg_catalog.pg_attribute src_a
JOIN pg_catalog.pg_class src_c ON src_a.attrelid = src_c.oid
JOIN pg_catalog.pg_namespace src ON src_c.relnamespace = src.oid
JOIN pg_catalog.pg_class tgt_c
  ON src_a.attname = tgt_c.relname || '_id'
  OR src_a.attname = tgt_c.relname || '_cd'
JOIN pg_catalog.pg_namespace tgt ON tgt_c.relnamespace = tgt.oid
WHERE src_a.attnum > 0
  AND NOT src_a.attisdropped
  AND src_c.relkind = 'r'
  AND tgt_c.relkind = 'r'
  AND src.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_internal')
  AND tgt.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_internal')
  {filter_clause}
ORDER BY src.nspname, src_c.relname, src_a.attname;
"""


async def _execute_sql(data_source_id: int, sql: str) -> str:
    """Execute a raw SQL query via Redash API and return the result."""
    body = {
        "data_source_id": data_source_id,
        "query": sql,
        "max_age": 3600,
    }
    return await redash_request("POST", "/api/query_results", body=body)


def _build_schema_filter(schema_name: str | None, table_name: str | None) -> str:
    clauses = []
    if schema_name:
        clauses.append(f"AND n.nspname = '{schema_name}'")
    if table_name:
        clauses.append(f"AND c.relname = '{table_name}'")
    return " ".join(clauses)


def _build_infer_filter(schema_name: str | None) -> str:
    if schema_name:
        return f"AND src.nspname = '{schema_name}'"
    return ""


@mcp.tool()
async def get_table_columns(
    data_source_id: int,
    schema_name: str | None = None,
    table_name: str | None = None,
) -> str:
    """Get detailed column information (name, data type, position) for tables.

    Queries the database catalog directly to get column types, unlike
    get_data_source_schema which only returns column names.

    Args:
        data_source_id: ID of the data source.
        schema_name: Optional schema to filter (e.g. 'public', 'external').
        table_name: Optional table name to filter.
    """
    filter_clause = _build_schema_filter(schema_name, table_name)
    sql = _COLUMN_DETAIL_SQL.format(filter_clause=filter_clause)
    return await _execute_sql(data_source_id, sql)


@mcp.tool()
async def get_foreign_keys(
    data_source_id: int,
    schema_name: str | None = None,
    table_name: str | None = None,
) -> str:
    """Get foreign key relationships defined in the database.

    Note: Data warehouses like Redshift often have few or no formal FK
    constraints. Use infer_table_relationships for convention-based discovery.

    Args:
        data_source_id: ID of the data source.
        schema_name: Optional schema to filter.
        table_name: Optional table name to filter.
    """
    filter_clause = _build_schema_filter(schema_name, table_name)
    sql = _FK_SQL.format(filter_clause=filter_clause)
    return await _execute_sql(data_source_id, sql)


@mcp.tool()
async def infer_table_relationships(
    data_source_id: int,
    schema_name: str | None = None,
) -> str:
    """Infer table relationships by matching column naming conventions.

    Looks for columns ending in '_id' or '_cd' that match existing table
    names (e.g. customer_id -> customer table). Useful for data warehouses
    that don't define formal foreign keys.

    Args:
        data_source_id: ID of the data source.
        schema_name: Optional schema to filter source tables.
    """
    filter_clause = _build_infer_filter(schema_name)
    sql = _INFER_RELATIONSHIPS_SQL.format(filter_clause=filter_clause)
    return await _execute_sql(data_source_id, sql)
