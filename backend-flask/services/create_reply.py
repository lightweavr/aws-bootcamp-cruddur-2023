import uuid
from datetime import datetime, timedelta, timezone

from lib.db import db
import lib.db_templates


class CreateReply:
    @staticmethod
    def run(message, cognito_user_id, activity_uuid):
        model = {"errors": None, "data": None}

        if not cognito_user_id or len(cognito_user_id) < 1:
            model["errors"] = ["cognito_user_id_blank"]

        if not activity_uuid or len(activity_uuid) < 1:
            model["errors"] = ["activity_uuid_blank"]

        if not message or len(message) < 1:
            model["errors"] = ["message_blank"]
        elif len(message) > 1024:
            model["errors"] = ["message_exceed_max_chars_1024"]

        if model["errors"]:
            # return what we provided
            model["data"] = {
                "message": message,
                "reply_to_activity_uuid": activity_uuid,
            }
        else:
            uuid = CreateReply.create_reply(cognito_user_id, activity_uuid, message)

            object_json = CreateReply.query_object_activity(uuid)
            model["data"] = object_json
        return model

    @staticmethod
    def create_reply(cognito_user_id, activity_uuid, message):
        uuid = db.query_commit(
            lib.db_templates.reply,
            {
                "cognito_user_id": cognito_user_id,
                "reply_to_activity_uuid": activity_uuid,
                "message": message,
            },
        )
        return uuid

    @staticmethod
    def query_object_activity(uuid):
        return db.query_object_json(lib.db_templates.activities_object, {"uuid": uuid})
