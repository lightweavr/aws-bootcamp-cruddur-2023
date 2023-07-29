from lib.ddb import Ddb
from lib.db import db

class MessageGroups:
    def run(cognito_user_id):
        model = {"errors": None, "data": None}
        my_user_uuid = db.query_get_uuid_from_cognito_id(cognito_user_id)

        ddb = Ddb()
        data = ddb.list_message_groups(my_user_uuid)
        # app.logger.debug(f"list_message_groups: {data}")
        model['data'] = data
        return model
