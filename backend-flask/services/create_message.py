import uuid
from datetime import datetime, timedelta, timezone
from flask import current_app as app

from lib.db import db
from lib.ddb import Ddb


class CreateMessage:
    # mode indicates if we want to create a new message_group or using an existing one
    def run(
        mode,
        message,
        cognito_user_id,
        message_group_uuid=None,
        user_receiver_handle=None,
    ):
        model = {"errors": None, "data": None}
        if mode == "update":
            if message_group_uuid == None or len(message_group_uuid) < 1:
                model["errors"] = ["message_group_uuid_blank"]

        if mode == "create":
            if user_receiver_handle == None or len(user_receiver_handle) < 1:
                model["errors"] = ["user_reciever_handle_blank"]

        if cognito_user_id == None or len(cognito_user_id) < 1:
            model["errors"] = ["cognito_user_id_blank"]

        if message == None or len(message) < 1:
            model["errors"] = ["message_blank"]
        elif len(message) > 1024:
            model["errors"] = ["message_exceed_max_chars"]

        if model["errors"]:
            # return what we provided
            model["data"] = {
                "display_name": "Andrew Brown",
                "handle": user_sender_handle,
                "message": message,
            }
        else:
            if user_receiver_handle == None:
                rev_handle = ""
            else:
                rev_handle = user_receiver_handle
            users = db.query_create_message_users(cognito_user_id, rev_handle)
            app.logger.debug("USERS =-=-=-=-==")
            app.logger.debug(users)

            my_user = next((item for item in users if item["kind"] == "sender"), None)
            other_user = next((item for item in users if item["kind"] == "recv"), None)

            app.logger.debug("USERS=[my-user]==")
            app.logger.debug(my_user)
            app.logger.debug("USERS=[other-user]==")
            app.logger.debug(other_user)

            ddb = Ddb.client()

            if mode == "update":
                data = Ddb.create_message(
                    client=ddb,
                    message_group_uuid=message_group_uuid,
                    message=message,
                    my_user_uuid=my_user["uuid"],
                    my_user_display_name=my_user["display_name"],
                    my_user_handle=my_user["handle"],
                )
            elif mode == "create":
                data = Ddb.create_message_group(
                    client=ddb,
                    message=message,
                    my_user_uuid=my_user["uuid"],
                    my_user_display_name=my_user["display_name"],
                    my_user_handle=my_user["handle"],
                    other_user_uuid=other_user["uuid"],
                    other_user_display_name=other_user["display_name"],
                    other_user_handle=other_user["handle"],
                )
            model["data"] = data
        return model
