import os
from time import strftime

import rollbar
import rollbar.contrib.flask
from flask import got_request_exception


def init_rollbar(app):
    with app.app_context():
        rollbar.init(
            access_token=os.getenv("ROLLBAR_ACCESS_TOKEN"),
            environment="production",
            # server root directory, makes tracebacks prettier
            root=os.path.dirname(os.path.realpath(__file__)),
            # flask already sets up logging
            allow_logging_basic_config=False,
        )
        rollbar.report_message("Rollbar is configured correctly", "info")
        got_request_exception.connect(rollbar.contrib.flask.report_exception, app)
