import os
import re
import sys
from typing import Mapping, Optional

import psycopg
from flask import current_app as app
from psycopg_pool import ConnectionPool


class Db:
    def __init__(self) -> None:
        if "CONNECTION_URL" in os.environ:
            connection_url = os.getenv("CONNECTION_URL")
        else:
            user = os.getenv("DB_USER")
            password = os.getenv("DB_PASSWORD")
            host = os.getenv("DB_ENDPOINT")
            connection_url = f"postgresql://{user}:{password}@{host}:5432/cruddur"
        self.pool = ConnectionPool(connection_url) # pyre-ignore [6]

    def query_commit(self, sql: str, params: Mapping[str, str]) -> Optional[str]:
        pattern = r"\bRETURNING\b"
        is_returning_id = re.search(pattern, sql)
        try:
            with self.pool.connection() as conn:
                cur = conn.cursor()
                cur.execute(psycopg.sql.SQL(sql), params) # pyre-ignore [6]
                if is_returning_id:
                    returning_id = cur.fetchone()[0]
                    conn.commit()
                    return returning_id
                else:
                    conn.commit()
        except psycopg.Error as err:
            self.print_sql_err(err)

    # when we want to return a json object
    def query_array_json(self, sql: str, params: Mapping[str, str], verbose: bool=False) -> str:
        wrapped_sql = self.query_wrap_array(sql)
        if app and verbose:
            app.logger.debug(f"Running SQL query {wrapped_sql}")
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(wrapped_sql, params)
                json = cur.fetchone()
                if not json:
                    return "[]"
                else:
                    return json[0]

    # When we want to return an array of json objects
    def query_object_json(self, sql: str, params: Mapping[str, str], verbose: bool=False) -> str:
        wrapped_sql = self.query_wrap_object(sql)

        if app and verbose:
            app.logger.debug(f"Running SQL query {wrapped_sql}")
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(wrapped_sql, params)
                json = cur.fetchone()
                if not json:
                    return "{}"
                else:
                    return json[0]

    def query_single(self, sql: str, params: Mapping[str, str], verbose: bool=False) -> str:
        if app and verbose:
            app.logger.debug(f"Running SQL query {sql} with params {params}")
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(psycopg.sql.SQL(sql), params)
                result = cur.fetchone()
                return result[0]

    def query_single_noreturn(self, sql:str, params: Mapping[str, str], verbose: bool=False) -> None:
        if app and verbose:
            app.logger.debug(f"Running SQL query {sql}")
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(psycopg.sql.SQL(sql), params)

    def query_get_handle_from_cognito_id(self, cognito_user_id: str) -> str:
        sql = "select handle from users where cognito_user_id = %(cognito_user_id)s"
        params = {"cognito_user_id": cognito_user_id}
        return self.query_single(sql, params)

    def query_get_uuid_from_cognito_id(self, cognito_user_id: str) -> str:
        sql = "select uuid from users where cognito_user_id = %(cognito_user_id)s"
        params = {"cognito_user_id": cognito_user_id}
        return self.query_single(sql, params)

    def query_get_uuid_from_handle(self, handle: str) -> str:
        sql = "select uuid from users where handle = %(handle)s"
        params = {"handle": handle}
        return self.query_single(sql, params)

    def query_create_message_users(self, cognito_user_id: str, user_receiver_handle: str) -> str:
        sql = """
      SELECT
        users.uuid,
        users.display_name,
        users.handle,
        CASE users.cognito_user_id = %(cognito_user_id)s
        WHEN TRUE THEN
          'sender'
        WHEN FALSE THEN
          'recv'
        ELSE
          'other'
        END as kind
      FROM public.users
      WHERE
        users.cognito_user_id = %(cognito_user_id)s
        OR
        users.handle = %(user_receiver_handle)s
    """
        return db.query_array_json(
            sql,
            {
                "cognito_user_id": cognito_user_id,
                "user_receiver_handle": user_receiver_handle,
            },
        )

    @staticmethod
    def query_wrap_object(template: str) -> str:
        """
        This does the same thing as conn.cursor(row_factory=dict_row), except it coerces everything
        to strings before being returned

        This used to have COALESCE, but the need for that was removed when the function checked for "is there a result"
        I removed it to make the SQL function simpler
        """
        sql = f"""
    (SELECT row_to_json(object_row) FROM (
    {template.strip()}
    ) object_row);
    """
        return sql.strip()

    @staticmethod
    def query_wrap_array(template: str) -> str:
        sql = f"""
    (SELECT array_to_json(array_agg(row_to_json(array_row))) FROM (
    {template.strip()}
    ) array_row);
    """
        return sql.strip()

    @staticmethod
    def print_sql_err(err: psycopg.Error) -> None:
        # get details about the exception
        err_type, err_obj, traceback = sys.exc_info()

        # get the line number when exception occured
        line_num = traceback.tb_lineno if traceback else -1

        if app:
            log = app.logger.error
        else:
            log = print

        # print the connect() error
        log(f"psycopg ERROR: {err} on line number: {line_num}")
        log(f"psycopg traceback: {traceback} -- type: {err_type}")

        # print the pgcode and pgerror exceptions
        if err.pgerror:
            log(f"pgerror: {err.pgerror}")
        if err.pgcode:
            log(f"pgcode: {err.pgcode}")


db = Db()
