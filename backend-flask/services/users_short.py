from lib.db import db
import lib.db_templates


class UsersShort:
    def run(handle):
        results = db.query_object_json(lib.db_templates.user_short, {"handle": handle})
        return results
