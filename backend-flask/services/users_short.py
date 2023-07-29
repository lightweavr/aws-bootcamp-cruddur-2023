import lib.db_templates
from lib.db import db


class UsersShort:
    def run(handle):
        results = db.query_object_json(lib.db_templates.user_short, {"handle": handle})
        return results
