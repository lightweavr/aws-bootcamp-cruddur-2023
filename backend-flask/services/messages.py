from datetime import datetime, timedelta, timezone
from lib.ddb import Ddb
from lib.db import db
from flask import current_app as app

class Messages:
    def run(message_group_uuid, cognito_user_id):
        model = {"errors": None, "data": None}

        my_user_uuid = db.query_get_uuid_from_cognito_id(cognito_user_id)

        app.logger.debug(f"get messages UUID: {my_user_uuid}")

        ddb = Ddb()
        data = ddb.list_messages(message_group_uuid)
        app.logger.debug(f"list_messages: {len(data)}")
        model["data"] = data
        return model
