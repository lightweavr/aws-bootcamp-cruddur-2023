from datetime import datetime, timedelta, timezone

from opentelemetry import trace

import lib.db_templates
from lib.db import db

tracer = trace.get_tracer("home.activities")


class HomeActivities:
    def run(cognito_user_id=None):
        with tracer.start_as_current_span("home-activites"):
            span = trace.get_current_span()
            now = datetime.now(timezone.utc).astimezone()
            span.set_attribute("app.now", now.isoformat())
            results = db.query_array_json(lib.db_templates.home, {})

            # with pool.connection() as conn:
            #     with conn.cursor() as cur:
            #         cur.execute(sql)
            #         json = cur.fetchall()
            # print(json[0][0])
            """
            This next bit of code returns the similar thing as the above - except with JSON serialization 
            issues with datetime and uuid objects. If there's a lot of mangling in the future, I can change 
            the code that gets run
            from psycopg.rows import dict_row
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(inner_sql)
                res = cur.fetchall() 
                print(res) 
            """
            span.set_attribute("app.result_length", len(results))

            return results
