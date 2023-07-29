import json
import os

import boto3
import psycopg2

"""
This method uses a hardcoded postgres_iam user for RDS authentication via IAM:
https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.DBAccounts.html#UsingWithRDS.IAMDBAuth.DBAccounts.PostgreSQL

## Can't fetch the details at runtime:
* The DB is inside a VPC, and one of the attached Security Groups, the VPC itself, or the Lambda execution seems to be denying access to SSM via the internet
* Could add a VPC endpoint for SSM, but that's $0.01/AZ/hour

## Can't fetch the secured details at CFN
* Can't use {{resolve:ssm-secure:/cruddur/db/password}} because Environment isn't a supported resource: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/dynamic-references.html#template-parameters-dynamic-patterns-resources

* Secure strings aren't supported by Parameter input

## Solution?
Use IAM to generate a database auth token: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.html

Python Guide: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.Connecting.Python.html
"""


def lambda_handler(event, context):
    user = event["request"]["userAttributes"]
    print("userAttributes")
    print(user)

    client = boto3.client("rds")

    host = os.getenv("dbHost")
    port = 5432
    username = "postgres_iam"

    token = client.generate_db_auth_token(
        DBHostname=host, Port=port, DBUsername=username
    )

    try:
        conn = psycopg2.connect(
            dbname="cruddur",
            user=username,
            password=token,
            host=host,
            port=port,
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
