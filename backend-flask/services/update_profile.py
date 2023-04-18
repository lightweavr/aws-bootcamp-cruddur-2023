from lib.db import db
import lib.db_templates


class UpdateProfile:
    def run(cognito_user_id, bio, display_name):
        model = {"errors": None, "data": None}

        if display_name == None or len(display_name) < 1:
            model["errors"] = ["display_name_blank"]

        if model["errors"]:
            model["data"] = {"bio": bio, "display_name": display_name}
        else:
            handle = UpdateProfile.update_profile(bio, display_name, cognito_user_id)
            data = UpdateProfile.query_users_short(handle)
            model["data"] = data
        return model

    def update_profile(bio, display_name, cognito_user_id):
        if bio == None:
            bio = ""

        handle = db.query_commit(
            lib.db_templates.update_user_profile,
            {
                "cognito_user_id": cognito_user_id,
                "bio": bio,
                "display_name": display_name,
            },
        )

    def query_users_short(handle):
        data = db.query_object_json(lib.db_templates.user_short, {"handle": handle})
        return data
