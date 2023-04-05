import uuid
from datetime import datetime, timedelta, timezone
from lib.db import db
import lib.db_templates
from flask import current_app as app


class CreateActivity:
    def run(message, cognito_user_id, ttl):
        model = {"errors": None, "data": None}

        now = datetime.now(timezone.utc).astimezone()

        if ttl == "30-days":
            ttl_offset = timedelta(days=30)
        elif ttl == "7-days":
            ttl_offset = timedelta(days=7)
        elif ttl == "3-days":
            ttl_offset = timedelta(days=3)
        elif ttl == "1-day":
            ttl_offset = timedelta(days=1)
        elif ttl == "12-hours":
            ttl_offset = timedelta(hours=12)
        elif ttl == "3-hours":
            ttl_offset = timedelta(hours=3)
        elif ttl == "1-hour":
            ttl_offset = timedelta(hours=1)
        else:
            model["errors"] = ["ttl_blank"]

        if message == None or len(message) < 1:
            model["errors"] = ["message_blank"]
        elif len(message) > 280:
            model["errors"] = ["message_exceed_max_chars"]
        
        try:
            user_handle = db.query_get_handle_from_cognito_id(cognito_user_id)
        except Exception as ex:
            app.logger.exception(f"exception fetching handle from db: {ex}")
            model["errors"] = [f"exception fetching handle from db: {ex}"]

        if user_handle == None or len(user_handle) < 1:
            model["errors"] = ["user_handle_blank"]

        if not model["errors"]:
            expires_at = now + ttl_offset
            uuid = db.query_commit(
                lib.db_templates.create,
                {"handle": user_handle, "message": message, "expires_at": expires_at},
            )

            model["data"] = db.query_object_json(
                lib.db_templates.activities_object, {"uuid": uuid}
            )

        return model
