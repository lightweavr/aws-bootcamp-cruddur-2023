import json
import logging
import os
from time import strftime
from typing import Dict, Tuple, TypeVar

# Cloudwatch
import watchtower
from flask import Flask, request
from flask_cors import CORS, cross_origin

import routes.activities
import routes.messages
import routes.users
from lib.cognito_jwt_token import (
    CognitoJwtToken,
    TokenVerifyError,
    extract_access_token,
)
from lib.cors import init_cors
from lib.helpers import model_json
from lib.honeycomb import init_honeycomb
from lib.rollbar import init_rollbar
from lib.xray import init_xray
from services.create_activity import *
from services.create_message import *
from services.create_reply import *
from services.home_activities import *
from services.message_groups import *
from services.messages import *
from services.notifications_activities import *
from services.search_activities import *
from services.show_activity import *
from services.update_profile import *
from services.user_activities import *
from services.users_short import *

app = Flask(__name__)

T = TypeVar("T")

# Initialize tracing and an exporter that can send data to Honeycomb
init_honeycomb(app)

# Xray
init_xray(app)

# Cloudwatch - because it hooks into the logging framework, no point splitting it out
LOGGER: logging.Logger = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
cw_handler = watchtower.CloudWatchLogHandler(
    log_group="/cruddur/backend-flask/server",
    log_stream_name="{machine_name}/{logger_name}",
    log_group_retention_days=7,
)
LOGGER.addHandler(cw_handler)
LOGGER.info("cruddur backend running")


# Log non-200 responses
@app.after_request
def after_request(response: T) -> T:
    # This only works when debug mode is off - https://stackoverflow.com/a/15004612
    if response.status_code == 200:
        return response
    timestamp = strftime("[%Y-%b-%d %H:%M]")
    LOGGER.error(
        "%s %s %s %s %s %s",
        timestamp,
        request.remote_addr,
        request.method,
        request.scheme,
        request.full_path,
        response.status,
    )
    return response


# Rollbar
init_rollbar(app)

# CORS handling
init_cors(app)

routes.activities.load(app)
routes.users.load(app)
routes.messages.load(app)


@app.route("/api/health-check")
def health_check() -> Tuple[Dict[str, bool], int]:
    return {"success": True}, 200


if __name__ == "__main__":
    debug = os.getenv("FLASK_ENV", "prod") == "development"
    app.run(debug=debug)
