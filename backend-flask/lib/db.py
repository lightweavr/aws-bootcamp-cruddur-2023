from psycopg_pool import ConnectionPool
from flask import current_app as app
from typing import Sequence
import re
import os
import sys

class Db:
  def __init__(self):
    connection_url = os.getenv("CONNECTION_URL")
    self.pool = ConnectionPool(connection_url)

  def query_commit(self, sql, params={}):
    pattern = r"\bRETURNING\b"
    is_returning_id = re.search(pattern, sql)

    try:
      with self.pool.connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        if is_returning_id:
          returning_id = cur.fetchone()[0]
        conn.commit()
        if is_returning_id:
          return returning_id
    except Exception as err:
      self.print_sql_err(err)

  # when we want to return a json object
  def query_array_json(self, sql, params={}) -> str:
    wrapped_sql = self.query_wrap_array(sql)
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
  def query_object_json(self, sql, params={}) -> str:
    wrapped_sql = self.query_wrap_object(sql)

    app.logger.debug(f"Running SQL query {wrapped_sql}")
    with self.pool.connection() as conn:
      with conn.cursor() as cur:
        cur.execute(wrapped_sql, params)
        json = cur.fetchone()
        if not json:
          return "{}"
        else:
          return json[0]

  def query_single(self, sql, params: Sequence):
    app.logger.debug(f"Running SQL query {sql}")
    with self.pool.connection() as conn:
      with conn.cursor() as cur:
        cur.execute(sql, params)
        result = cur.fetchone()
        return result[0]
  
  def query_get_handle_from_cognito_id(self, cognito_user_id) -> str:
    sql = "select handle from users where cognito_user_id = %(cognito_user_id)s"
    params = {"cognito_user_id": cognito_user_id}
    return self.query_single(sql, params)

  @staticmethod
  def query_wrap_object(template):
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
  def query_wrap_array(template):
    sql = f"""
    (SELECT array_to_json(array_agg(row_to_json(array_row))) FROM (
    {template.strip()}
    ) array_row);
    """
    return sql.strip()

  @staticmethod
  def print_sql_err(err: Exception) -> None:
    # get details about the exception
    err_type, err_obj, traceback = sys.exc_info()

    # get the line number when exception occured
    line_num = traceback.tb_lineno

    # print the connect() error
    app.logger.error(f"psycopg ERROR: {err} on line number: {line_num}")
    app.logger.error(f"psycopg traceback: {traceback} -- type: {err_type}")

    # print the pgcode and pgerror exceptions
    app.logger.error(f"pgerror: {err.pgerror}" )
    app.logger.error(f"pgcode: {err.pgcode}")

db = Db()
