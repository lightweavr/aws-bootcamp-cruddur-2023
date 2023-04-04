from datetime import datetime, timedelta, timezone
from opentelemetry import trace
from lib.db import pool, query_wrap_array 
# from psycopg.rows import dict_row

tracer = trace.get_tracer("home.activities")


class HomeActivities:
    def run(cognito_user_id=None):
        with tracer.start_as_current_span("home-activites-mock-data"):
            span = trace.get_current_span()
            now = datetime.now(timezone.utc).astimezone()
            span.set_attribute("app.now", now.isoformat())
            inner_sql = """
            SELECT
                activities.uuid,
                users.display_name,
                users.handle,
                activities.message,
                activities.replies_count,
                activities.reposts_count,
                activities.likes_count,
                activities.reply_to_activity_uuid,
                activities.expires_at,
                activities.created_at
            FROM public.activities
            LEFT JOIN public.users ON users.uuid = activities.user_uuid
            ORDER BY activities.created_at DESC
            """
            sql = query_wrap_array(inner_sql)
            
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    json = cur.fetchall()
                    # print(json[0][0])
                """
                This next bit of code returns the similar thing as the above - except with JSON serialization 
                issues with datetime and uuid objects. If there's a lot of mangling in the future, I can change 
                the code that gets run
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(inner_sql)
                    res = cur.fetchall() 
                    print(res) 
                """
            span.set_attribute("app.result_length", len(json))

            return json[0][0]
