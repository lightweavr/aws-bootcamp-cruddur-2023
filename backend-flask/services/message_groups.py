from lib.ddb import Ddb
from lib.db import db

class MessageGroups:
    def run(cognito_user_id):
        model = {"errors": None, "data": None}
        my_user_uuid = db.query_get_handle_from_cognito_id(cognito_user_id)

        print("UUID",my_user_uuid)

        ddb = Ddb.client()
        data = Ddb.list_message_groups(ddb, my_user_uuid)
        print("list_message_groups:",data)
        model['data'] = data
        return model
