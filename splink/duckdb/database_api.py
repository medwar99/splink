import logging
from tempfile import TemporaryDirectory
from typing import Union

import duckdb
import pandas as pd

from ..database_api import DatabaseAPI
from ..dialects import (
    DuckDBDialect,
)
from .dataframe import DuckDBDataFrame
from .duckdb_helpers.duckdb_helpers import (
    create_temporary_duckdb_connection,
    duckdb_load_from_file,
    validate_duckdb_connection,
)

logger = logging.getLogger(__name__)


# alias for brevity:
ddb_con = duckdb.DuckDBPyConnection


class DuckDBAPI(DatabaseAPI):
    sql_dialect = DuckDBDialect()

    def __init__(
        self,
        connection: Union[str, ddb_con] = ":memory:",
        output_schema: str = None,
    ):
        super().__init__()
        validate_duckdb_connection(connection, logger)

        if isinstance(connection, str):
            con_lower = connection.lower()
        if isinstance(connection, ddb_con):
            con = connection
        elif con_lower == ":memory:":
            con = duckdb.connect(database=connection)
        elif con_lower == ":temporary:":
            con = create_temporary_duckdb_connection(self)
        else:
            con = duckdb.connect(database=connection)

        self._con = con

        if output_schema:
            self._run_sql_execution(
                f"""
                    CREATE SCHEMA IF NOT EXISTS {output_schema};
                    SET schema '{output_schema}';
                """
            )

    def _table_registration(self, input, table_name) -> None:
        if isinstance(input, dict):
            input = pd.DataFrame(input)
        elif isinstance(input, list):
            input = pd.DataFrame.from_records(input)

        # Registration errors will automatically
        # occur if an invalid data type is passed as an argument
        self._run_sql_execution(f"CREATE TABLE {table_name} AS SELECT * FROM input")

    def table_to_splink_dataframe(
        self, templated_name, physical_name
    ) -> DuckDBDataFrame:
        return DuckDBDataFrame(templated_name, physical_name, self)

    def table_exists_in_database(self, table_name):
        sql = f"PRAGMA table_info('{table_name}');"

        # From duckdb 0.5.0, duckdb will raise a CatalogException
        # which does not exist in 0.4.0 or before

        # TODO: probably we can drop this compat now?
        try:
            from duckdb import CatalogException

            error = (RuntimeError, CatalogException)
        except ImportError:
            error = RuntimeError

        try:
            self._run_sql_execution(sql)
        except error:
            return False
        return True

    def load_from_file(self, file_path: str):
        return duckdb_load_from_file(file_path)

    def _run_sql_execution(self, final_sql: str) -> duckdb.DuckDBPyRelation:
        return self._con.sql(final_sql)

    @property
    def accepted_df_dtypes(self):
        accepted_df_dtypes = [pd.DataFrame]
        try:
            # If pyarrow is installed, add to the accepted list
            import pyarrow as pa

            accepted_df_dtypes.append(pa.lib.Table)
        except ImportError:
            pass
        return accepted_df_dtypes

    def process_input_tables(self, input_tables):
        return [
            self.load_from_file(t) if isinstance(t, str) else t for t in input_tables
        ]

    # special methods for use:

    def export_to_duckdb_file(self, output_path, delete_intermediate_tables=False):
        """
        https://stackoverflow.com/questions/66027598/how-to-vacuum-reduce-file-size-on-duckdb
        """
        if delete_intermediate_tables:
            self._delete_tables_created_by_splink_from_db()
        with TemporaryDirectory() as tmpdir:
            self._run_sql_execution(f"EXPORT DATABASE '{tmpdir}' (FORMAT PARQUET);")
            new_con = duckdb.connect(database=output_path)
            new_con.execute(f"IMPORT DATABASE '{tmpdir}';")
            new_con.close()
