from datetime import datetime, timedelta, timezone

from lib.db import db
import lib.db_templates


class ShowActivity:
    def run(activity_uuid):
        return db.query_object_json(lib.db_templates.show, {"uuid": activity_uuid})
