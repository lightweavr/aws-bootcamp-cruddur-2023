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

            span.set_attribute("app.result_length", len(results))

            return results
