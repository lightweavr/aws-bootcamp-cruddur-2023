import json
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")

def lambda_handler(event, context):
    for record in event.pop("Records"):
        if record["eventName"] == "REMOVE":
            print("skip REMOVE event")
            continue

        pk = record["dynamodb"]["Keys"]["pk"]["S"]
        if pk.startswith("GRP#"):
            print("Skip group update")
            continue

        print(f"record: {record}")
        sk = record["dynamodb"]["Keys"]["sk"]["S"]
        if not pk.startswith("MSG#"):
            print(f"Unexpected PK type: {pk}")
            continue

        group_uuid = pk.replace("MSG#", "")
        message = record["dynamodb"]["NewImage"]["message"]["S"]
        print(f"GRUP ===> {group_uuid}: {message}")

        table_name = "cruddur-messages"
        index_name = "message-group-sk-index"
        table = dynamodb.Table(table_name)
        data = table.query(
            IndexName=index_name,
            KeyConditionExpression=Key("message_group_uuid").eq(group_uuid),
        )
        print("RESP ===>", data["Items"])

        # recreate the message group rows with new SK value
        with table.batch_writer() as batch:
            for i in data["Items"]:
                batch.delete_item(Key={"pk": i["pk"], "sk": i["sk"]})

                batch.put_item(
                    Item={
                        "pk": i["pk"],
                        "sk": sk,
                        "message_group_uuid": i["message_group_uuid"],
                        "message": message,
                        "user_display_name": i["user_display_name"],
                        "user_handle": i["user_handle"],
                        "user_uuid": i["user_uuid"],
                    }
                )
