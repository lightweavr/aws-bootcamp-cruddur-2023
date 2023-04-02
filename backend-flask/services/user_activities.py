from datetime import datetime, timedelta, timezone
from aws_xray_sdk.core import xray_recorder


class UserActivities:
    def run(user_handle, cognito_user_id=None):
        # Uncomment to force a 500 Internal Server Error
        # raise RuntimeError("testing the log")
        model = {"errors": None, "data": None}
        subsegment = xray_recorder.begin_subsegment("mock-data")
        now = datetime.now(timezone.utc).astimezone()

        if user_handle == None or len(user_handle) < 1:
            model["errors"] = ["blank_user_handle"]
            return model

        now = datetime.now()
        results = [
            {
                "uuid": "248959df-3079-4947-b847-9e0892d1bab4",
                "handle": "Andrew Brown",
                "message": "Cloud is fun!",
                "created_at": (now - timedelta(days=1)).isoformat(),
                "expires_at": (now + timedelta(days=31)).isoformat(),
            }
        ]
        model["data"] = results
        # Alternatively, just use xray_recorder directly
        subsegment.put_annotation("results_len", len(results))
        # set_user only works on the segment, not subsegement
        xray_recorder.current_segment().set_user(cognito_user_id)
        xray_recorder.end_subsegment()
        return model
