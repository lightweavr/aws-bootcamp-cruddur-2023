import boto3
import sys
from datetime import datetime, timedelta, timezone
import uuid
import os
import botocore.exceptions
from flask import current_app as app

def debug_print(message: str) -> None:
    if app:
        app.logger.debug(message)
    else:
        print(message)

class Ddb:
    def client():
        endpoint_url = os.getenv("AWS_ENDPOINT_URL")
        if endpoint_url:
            attrs = {"endpoint_url": endpoint_url}
        else:
            attrs = {}
        dynamodb = boto3.client("dynamodb", **attrs)
        return dynamodb

    def list_message_groups(client, my_user_uuid):
        year = str(datetime.now().year)
        table_name = "cruddur-messages"
        query_params = {
            "TableName": table_name,
            "KeyConditionExpression": "pk = :pk AND begins_with(sk,:year)",
            "ScanIndexForward": False,
            "Limit": 20,
            "ExpressionAttributeValues": {
                ":year": {"S": year},
                ":pk": {"S": f"GRP#{my_user_uuid}"},
            },
        }
        # debug_print(f"list message groups query-params: {query_params}")
        # query the table
        response = client.query(**query_params)
        items = response["Items"]

        results = []
        for item in items:
            last_sent_at = item["sk"]["S"]
            results.append(
                {
                    "uuid": item["message_group_uuid"]["S"],
                    "display_name": item["user_display_name"]["S"],
                    "handle": item["user_handle"]["S"],
                    "message": item["message"]["S"],
                    "created_at": last_sent_at,
                }
            )
        return results

    def list_messages(client, message_group_uuid):
        year = str(datetime.now().year)
        table_name = "cruddur-messages"
        query_params = {
            "TableName": table_name,
            "KeyConditionExpression": "pk = :pk AND begins_with(sk,:year)",
            "ScanIndexForward": False,
            "Limit": 20,
            "ExpressionAttributeValues": {
                ":year": {"S": year},
                ":pk": {"S": f"MSG#{message_group_uuid}"},
            },
        }

        response = client.query(**query_params)
        items = response["Items"]
        items.reverse()
        results = []
        for item in items:
            created_at = item["sk"]["S"]
            results.append(
                {
                    "uuid": item["message_uuid"]["S"],
                    "display_name": item["user_display_name"]["S"],
                    "handle": item["user_handle"]["S"],
                    "message": item["message"]["S"],
                    "created_at": created_at,
                }
            )
        return results

    def create_message(
        client,
        message_group_uuid,
        message,
        my_user_uuid,
        my_user_display_name,
        my_user_handle,
    ):
        now = datetime.now(timezone.utc).astimezone().isoformat()
        created_at = now
        message_uuid = str(uuid.uuid4())

        record = {
            "pk": {"S": f"MSG#{message_group_uuid}"},
            "sk": {"S": created_at},
            "message": {"S": message},
            "message_uuid": {"S": message_uuid},
            "user_uuid": {"S": my_user_uuid},
            "user_display_name": {"S": my_user_display_name},
            "user_handle": {"S": my_user_handle},
        }
        # insert the record into the table
        table_name = "cruddur-messages"
        response = client.put_item(TableName=table_name, Item=record)
        # print the response
        debug_print(f"create message: {response}")
        return {
            "message_group_uuid": message_group_uuid,
            "uuid": message_uuid,
            "display_name": my_user_display_name,
            "handle": my_user_handle,
            "message": message,
            "created_at": created_at,
        }

    def create_message_group(
        client,
        message,
        my_user_uuid,
        my_user_display_name,
        my_user_handle,
        other_user_uuid,
        other_user_display_name,
        other_user_handle,
    ) -> str:
        table_name = "cruddur-messages"

        # Check to see if a message group already exists
        # In theory this shouldn't be possible since the UI has a message group ID assigned, but just in case...

        # Look up GRP#{my_id} and user_uuid=other_user_uuid to see if *I* have a conversation
        # Looking up GRP#{their id} and my user_uuid would see if _they_ have a conversation
        # THIS DOESN'T SUPPORT PAGINATION RIGHT NOW
        existing_group = False
        query_params = {
            "TableName": table_name,
            "KeyConditionExpression": "pk = :pk",
            "FilterExpression": "user_uuid = :other_user_uuid",
            "ProjectionExpression": "message_group_uuid",
            "ExpressionAttributeValues": {
                ":pk": {"S": f"GRP#{my_user_uuid}"},
                ":other_user_uuid": {"S": other_user_uuid},
            },
            "ScanIndexForward": False,
            "ReturnConsumedCapacity": "TOTAL",
        }
        response = client.query(**query_params)

        if response["Count"] > 0:
            debug_print(f"Check for existing group for {my_user_display_name}/{other_user_display_name} found a result: {response['Items']}")
            if response["Count"] > 1:
                debug_print(f"WARNING: More than one message group exists for {my_user_display_name}/{other_user_display_name}!")
            message_group_uuid = response["Items"][0]["message_group_uuid"]["S"]
            existing_group = True

        if not message_group_uuid:
            message_group_uuid = str(uuid.uuid4())
        message_uuid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).astimezone().isoformat()
        last_message_at = now
        created_at = now

        my_message_group = {
            "pk": {"S": f"GRP#{my_user_uuid}"},
            "sk": {"S": last_message_at},
            "message_group_uuid": {"S": message_group_uuid},
            "message": {"S": message},
            "user_uuid": {"S": other_user_uuid},
            "user_display_name": {"S": other_user_display_name},
            "user_handle": {"S": other_user_handle},
        }

        other_message_group = {
            "pk": {"S": f"GRP#{other_user_uuid}"},
            "sk": {"S": last_message_at},
            "message_group_uuid": {"S": message_group_uuid},
            "message": {"S": message},
            "user_uuid": {"S": my_user_uuid},
            "user_display_name": {"S": my_user_display_name},
            "user_handle": {"S": my_user_handle},
        }

        message = {
            "pk": {"S": f"MSG#{message_group_uuid}"},
            "sk": {"S": created_at},
            "message": {"S": message},
            "message_uuid": {"S": message_uuid},
            "user_uuid": {"S": my_user_uuid},
            "user_display_name": {"S": my_user_display_name},
            "user_handle": {"S": my_user_handle},
        }

        items = {
            table_name: [{"PutRequest": {"Item": message}}]
        }
        if not existing_group:
            items[table_name].extend([
                {"PutRequest": {"Item": my_message_group}},
                {"PutRequest": {"Item": other_message_group}},
            ])

        try:
            response = client.batch_write_item(RequestItems=items)
            return {"message_group_uuid": message_group_uuid}
        except botocore.exceptions.ClientError as e:
            debug_print(f"create_message_group.try: {e}")
