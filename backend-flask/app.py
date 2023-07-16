from flask import Flask
from flask import request
from flask_cors import CORS, cross_origin
import json, logging, os
from time import strftime

from services.home_activities import *
from services.notifications_activities import *
from services.user_activities import *
from services.create_activity import *
from services.create_reply import *
from services.search_activities import *
from services.message_groups import *
from services.messages import *
from services.create_message import *
from services.show_activity import *
from services.users_short import *
from services.update_profile import *

from lib.cognito_jwt_token import (
    CognitoJwtToken,
    extract_access_token,
    TokenVerifyError,
)

# HoneyComb
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Xray
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

# Cloudwatch
import watchtower

# Rollbar
import rollbar
import rollbar.contrib.flask
from flask import got_request_exception

app = Flask(__name__)

# Initialize tracing and an exporter that can send data to Honeycomb
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)

trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Xray
xray_url = os.getenv("AWS_XRAY_URL")
xray_recorder.configure(service="backend-flask", dynamic_naming=xray_url)
XRayMiddleware(app, xray_recorder)
logging.getLogger("aws_xray_sdk").setLevel(logging.DEBUG)

# Cloudwatch
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
cw_handler = watchtower.CloudWatchLogHandler(
    log_group="cruddur", log_stream_name="{machine_name}/{program_name}/{logger_name}"
)
LOGGER.addHandler(cw_handler)
LOGGER.info("cruddur backend running")

# Cognito auth
cognito_jwt_token = CognitoJwtToken(
    user_pool_id=os.getenv("AWS_COGNITO_USER_POOL_ID"),
    user_pool_client_id=os.getenv("AWS_COGNITO_USER_POOL_CLIENT_ID"),
    region=os.getenv("AWS_DEFAULT_REGION"),
)


# Log non-200 responses
@app.after_request
def after_request(response):
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
def init_rollbar():
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


# CORS handling
frontend = os.getenv("FRONTEND_URL")
backend = os.getenv("BACKEND_URL")
origins = [frontend, backend]
cors = CORS(
    app,
    resources={r"/api/*": {"origins": origins}},
    headers=["Content-Type", "Authorization"],
    expose_headers="Authorization",
    methods="OPTIONS,GET,HEAD,POST",
)


@app.route("/api/health-check")
def health_check():
    return {"success": True}, 200


@app.route("/api/message_groups", methods=["GET"])
def data_message_groups():
    access_token = extract_access_token(request.headers)
    try:
        claims = cognito_jwt_token.verify(access_token)
        cognito_user_id = claims["sub"]
    except TokenVerifyError as e:
        return {}, 401
    model = MessageGroups.run(cognito_user_id=cognito_user_id)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/messages/<string:message_group_uuid>", methods=["GET"])
def data_messages(message_group_uuid):
    access_token = extract_access_token(request.headers)
    try:
        claims = cognito_jwt_token.verify(access_token)
        cognito_user_id = claims["sub"]
    except TokenVerifyError as e:
        # unauthenicatied request
        app.logger.debug(e)
        return {}, 401

    model = Messages.run(
        cognito_user_id=cognito_user_id, message_group_uuid=message_group_uuid
    )
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/messages", methods=["POST", "OPTIONS"])
@cross_origin()
def data_create_message():
    message_group_uuid = request.json.get("message_group_uuid", None)
    user_receiver_handle = request.json.get("user_receiver_handle", None)
    message = request.json["message"]

    access_token = extract_access_token(request.headers)
    try:
        claims = cognito_jwt_token.verify(access_token)
        cognito_user_id = claims["sub"]
    except TokenVerifyError as e:
        # unauthenicatied request
        app.logger.debug(e)
        return {}, 401

    # This is sent by frontend-react-js/src/components/MessageForm.js
    app.logger.debug(request.json)
    if message_group_uuid == None:
        # Create for the first time
        model = CreateMessage.run(
            mode="create",
            message=message,
            cognito_user_id=cognito_user_id,
            user_receiver_handle=user_receiver_handle,
        )
    else:
        # Push onto existing Message Group
        model = CreateMessage.run(
            mode="update",
            message=message,
            message_group_uuid=message_group_uuid,
            cognito_user_id=cognito_user_id,
        )

    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/activities/home", methods=["GET"])
@xray_recorder.capture("activities_home")
def data_home():
    cognito_user_id = None
    access_token = extract_access_token(request.headers)
    try:
        claims = cognito_jwt_token.verify(access_token)
        cognito_user_id = claims["username"]
    except TokenVerifyError as e:
        pass
    data = HomeActivities.run(cognito_user_id=cognito_user_id)
    return data, 200


@app.route("/api/activities/notifications", methods=["GET"])
def data_notifications():
    data = NotificationsActivities.run()
    return data, 200


@app.route("/api/activities/@<string:handle>", methods=["GET"])
@xray_recorder.capture("activities_users")
def data_handle(handle):
    cognito_user_id = None
    access_token = extract_access_token(request.headers)
    try:
        claims = cognito_jwt_token.verify(access_token)
        cognito_user_id = claims["username"]
    except TokenVerifyError as e:
        pass

    model = UserActivities.run(handle, cognito_user_id=cognito_user_id)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/activities/search", methods=["GET"])
def data_search():
    term = request.args.get("term")
    model = SearchActivities.run(term)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200
    return


@app.route("/api/activities", methods=["POST", "OPTIONS"])
@cross_origin()
def data_activities():
    cognito_user_id = None
    access_token = extract_access_token(request.headers)
    model = {}
    try:
        claims = cognito_jwt_token.verify(access_token)
        cognito_user_id = claims["username"]
        message = request.json["message"]
        ttl = request.json["ttl"]
        model = CreateActivity.run(message, cognito_user_id, ttl)
    except TokenVerifyError as e:
        app.logger.error(f"Request not authed: {access_token}, {e}")
        model["errors"] = ["Not Authenticated"]

    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200
    return


@app.route("/api/activities/<string:activity_uuid>", methods=["GET"])
@xray_recorder.capture("activities_show")
def data_show_activity(activity_uuid):
    data = ShowActivity.run(activity_uuid=activity_uuid)
    return data, 200


@app.route("/api/activities/<string:activity_uuid>/reply", methods=["POST", "OPTIONS"])
@cross_origin()
def data_activities_reply(activity_uuid):
    user_handle = "andrewbrown"
    message = request.json["message"]
    model = CreateReply.run(message, user_handle, activity_uuid)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200
    return


@app.route("/api/users/@<string:handle>/short", methods=["GET"])
def data_users_short(handle):
    data = UsersShort.run(handle)
    return data, 200


@app.route("/api/profile/update", methods=["POST", "OPTIONS"])
@cross_origin()
def data_update_profile():
    bio = request.json.get("bio", None)
    display_name = request.json.get("display_name", None)
    access_token = extract_access_token(request.headers)
    try:
        claims = cognito_jwt_token.verify(access_token)
        cognito_user_id = claims["sub"]
        model = UpdateProfile.run(
            cognito_user_id=cognito_user_id, bio=bio, display_name=display_name
        )
        if model["errors"] is not None:
            return model["errors"], 422
        else:
            return model["data"], 200
    except TokenVerifyError as e:
        # unauthenicatied request
        app.logger.debug(e)
        return {}, 401


if __name__ == "__main__":
    app.run(debug=True)
