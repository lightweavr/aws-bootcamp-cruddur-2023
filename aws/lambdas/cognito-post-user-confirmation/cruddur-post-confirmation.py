import boto3
import json
import psycopg2
import os

client = boto3.client("ssm")
params = {}
for param in client.get_parameters(
    Names=["/cruddur/db/password", "/cruddur/db/endpoint", "/cruddur/db/user"],
    WithDecryption=True,
).get("Parameters"):
    name = param["Name"].split("/")[-1]
    params[name] = param["Value"]


def lambda_handler(event, context):
    user = event["request"]["userAttributes"]
    print("userAttributes")
    print(user)
    try:
        conn = psycopg2.connect(
            dbname="cruddur",
            user=params["user"],
            password=params["password"],
            host=params["endpoint"],
            port=5432,
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO public.users (display_name, email, handle, cognito_user_id) VALUES(%s, %s, %s, %s)",
            (user["name"], user["email"], user["preferred_username"], user["sub"]),
        )
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    finally:
        if conn is not None:
            cur.close()
            conn.close()
            print("Database connection closed.")
    # Cognito seems to expect that you return the event? I can't find a doc on this
    return event
