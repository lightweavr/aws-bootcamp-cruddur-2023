from datetime import datetime, timezone
from lib.db import db
import lib.db_templates
from aws_xray_sdk.core import xray_recorder


class UserActivities:
    def run(user_handle, cognito_user_id=None):
        # Uncomment to force a 500 Internal Server Error
        # raise RuntimeError("testing the log")
        model = {"errors": None, "data": None}
        subsegment = xray_recorder.begin_subsegment("mock-data")

        if user_handle == None or len(user_handle) < 1:
            model["errors"] = ["blank_user_handle"]
            return model

        now = datetime.now()
        model["data"] = db.query_object_json(
            lib.db_templates.get_user_activities, {"handle": user_handle}
        )

        # Alternatively, just use xray_recorder directly
        subsegment.put_annotation("results_len", model["data"])
        # set_user only works on the segment, not subsegement
        xray_recorder.current_segment().set_user(cognito_user_id)
        xray_recorder.end_subsegment()
        return model
