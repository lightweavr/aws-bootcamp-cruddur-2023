# Largely copied from https://github.com/cgauge/Flask-AWSCognito/blob/master/flask_awscognito/services/token_service.py
# Which in turn is copied from https://github.com/awslabs/aws-support-tools/blob/master/Cognito/decode-verify-jwt/decode-verify-jwt.py
# https://youtu.be/d079jccoG-M?t=676
import os
import time
from functools import partial, wraps
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

import requests
from flask import current_app as app
from flask import g, request
from jose import jwk, jwt
from jose.exceptions import JOSEError
from jose.utils import base64url_decode


class FlaskAWSCognitoError(Exception):
    pass


class TokenVerifyError(Exception):
    pass


def extract_access_token(request_headers: Mapping[str, str]) -> Optional[str]:
    access_token = None
    auth_header = request_headers.get("Authorization")
    if auth_header and " " in auth_header:
        _, access_token = auth_header.split()
    return access_token


class CognitoJwtToken:
    def __init__(
        self,
        user_pool_id: str,
        user_pool_client_id: str,
        region: str,
        request_client: Optional[Callable] = None,  # pyre-ignore: [31]
    ) -> None:
        self.region = region
        if not self.region:
            raise FlaskAWSCognitoError("No AWS region provided")
        self.user_pool_id = user_pool_id
        self.user_pool_client_id = user_pool_client_id
        self.claims: Mapping[str, str] = {}
        if not request_client:
            self.request_client: Callable = requests.get  # pyre-ignore: [31]
        else:
            self.request_client: Callable = request_client  # pyre-ignore: [31]
        self.jwk_keys: Sequence[Mapping[str, str]] = []
        self._load_jwk_keys()

    def _load_jwk_keys(self) -> None:
        keys_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
        try:
            response = self.request_client(keys_url)
            self.jwk_keys = response.json()["keys"]
        except requests.exceptions.RequestException as e:
            raise FlaskAWSCognitoError(str(e)) from e

    @staticmethod
    def _extract_headers(token: str) -> Mapping[str, str]:
        try:
            headers = jwt.get_unverified_headers(token)
            return headers
        except JOSEError as e:
            raise TokenVerifyError(str(e)) from e

    def _find_pkey(self, headers: Mapping[str, str]) -> Mapping[str, str]:
        kid = headers["kid"]
        # search for the kid in the downloaded public keys
        key_index = -1
        for i in range(len(self.jwk_keys)):
            if kid == self.jwk_keys[i]["kid"]:
                key_index = i
                break
        if key_index == -1:
            raise TokenVerifyError("Public key not found in jwks.json")
        return self.jwk_keys[key_index]

    @staticmethod
    def _verify_signature(token: str, pkey_data: Mapping[str, str]) -> None:
        try:
            # construct the public key
            public_key = jwk.construct(pkey_data)
        except JOSEError as e:
            raise TokenVerifyError(str(e)) from e
        # get the last two sections of the token,
        # message and signature (encoded in base64)
        message, encoded_signature = str(token).rsplit(".", 1)
        # decode the signature
        decoded_signature = base64url_decode(encoded_signature.encode("utf-8"))
        # verify the signature
        if not public_key.verify(message.encode("utf8"), decoded_signature):
            raise TokenVerifyError("Signature verification failed")

    @staticmethod
    def _extract_claims(token: str) -> Mapping[str, str]:
        try:
            claims = jwt.get_unverified_claims(token)
            return claims
        except JOSEError as e:
            raise TokenVerifyError(str(e)) from e

    @staticmethod
    def _check_expiration(
        claims: Mapping[str, str], current_time: Optional[float]
    ) -> None:
        if not current_time:
            current_time = time.time()
        if current_time > float(claims["exp"]):
            raise TokenVerifyError("Token is expired")  # probably another exception

    def _check_audience(self, claims: Mapping[str, str]) -> None:
        # and the Audience  (use claims['client_id'] if verifying an access token)
        audience = claims["aud"] if "aud" in claims else claims["client_id"]
        if audience != self.user_pool_client_id:
            raise TokenVerifyError("Token was not issued for this audience")

    def verify(
        self, token: str, current_time: Optional[float] = None
    ) -> Mapping[str, str]:
        """https://github.com/awslabs/aws-support-tools/blob/master/Cognito/decode-verify-jwt/decode-verify-jwt.py"""
        if not token:
            raise TokenVerifyError("No token provided")

        headers = self._extract_headers(token)
        pkey_data = self._find_pkey(headers)
        self._verify_signature(token, pkey_data)

        claims = self._extract_claims(token)
        self._check_expiration(claims, current_time)
        self._check_audience(claims)

        self.claims = claims
        return claims

def jwt_required(f=None, on_error=None):
    if f is None:
        return partial(jwt_required, on_error=on_error)

    @wraps(f)
    def decorated_function(*args, **kwargs):
        cognito_jwt_token = CognitoJwtToken(
            user_pool_id=os.getenv("AWS_COGNITO_USER_POOL_ID"),
            user_pool_client_id=os.getenv("AWS_COGNITO_USER_POOL_CLIENT_ID"),
            region=os.getenv("AWS_DEFAULT_REGION")
        )
        access_token = extract_access_token(request.headers)
        try:
            claims = cognito_jwt_token.verify(access_token)
            # is this a bad idea using a global?
            g.cognito_user_id = claims['sub']  # storing the user_id in the global g object
        except TokenVerifyError as e:
            # unauthenticated request
            app.logger.debug(e)
            if on_error:
                return on_error(e)
            return {}, 401
        return f(*args, **kwargs)
    return decorated_function
