from lib.db import db

class UsersShort:
  def run(handle):
    sql = """
    SELECT
        users.uuid,
        users.handle,
        users.display_name
        FROM public.users
    WHERE
        users.handle = %(handle)s
  """.strip()
    results = db.query_object_json(sql,{
      'handle': handle
    })
    return results
