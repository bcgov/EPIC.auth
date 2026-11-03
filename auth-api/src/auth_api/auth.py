# Copyright © 2024 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Bring in the common JWT Manager."""
import re
from functools import wraps
from http import HTTPStatus

from flask import current_app, g, request
from flask_jwt_oidc import JwtManager


jwt = (
    JwtManager()
)  # pylint: disable=invalid-name; lower case name as used by convention in most Flask apps

# IDIR usernames issued by the login proxy look like a 32 char hex guid suffixed
# with "@idir" (e.g. "b16917cd4cba4df6acb9ff5ca4e56b28@idir").
_IDIR_USERNAME_RE = re.compile(r"[0-9a-f]{32}@idir")


class Auth:
    """Extending JwtManager to include additional functionalities."""

    @staticmethod
    def is_idir(token_info):
        """Return True when the token represents an IDIR end user.

        Prefers the verified ``identity_provider`` claim when the realm emits
        it, and falls back to the protected IDIR ``preferred_username`` shape.
        """
        if token_info and "identity_provider" in token_info:
            return str(token_info["identity_provider"]).lower() == "idir"

        username = str((token_info or {}).get("preferred_username", "")).lower()
        return _IDIR_USERNAME_RE.fullmatch(username) is not None

    @staticmethod
    def is_service_account(token_info):
        """Return True when the token is a Keycloak client-credentials token.

        Name independent: a service account token carries a ``client_id`` claim
        and has no interactive browser session (no ``sid``/``session_state``).
        """
        if not token_info:
            return False
        has_client_id = bool(token_info.get("client_id") or token_info.get("clientId"))
        has_session = bool(token_info.get("sid") or token_info.get("session_state"))
        return has_client_id and not has_session

    @staticmethod
    def _allowed_client_ids():
        """Return the configured set of client ids permitted for IDIR callers."""
        raw = str(current_app.config.get("ALLOWED_CLIENT_IDS", "") or "")
        return {item.strip() for item in raw.split(",") if item.strip()}

    @classmethod
    def is_authorized_caller(cls, token_info):
        """Apply the layered caller policy on an already validated token.

        Layer 1 (audience) is enforced upstream by the JWT manager. This adds:
        - Layer 2: an IDIR end user must originate from an allowlisted client
          (matched against the token's ``azp``).
        - Layer 3: any non-IDIR caller must be a service account.
        """
        if cls.is_idir(token_info):
            return (token_info or {}).get("azp") in cls._allowed_client_ids()
        return cls.is_service_account(token_info)

    @classmethod
    def _deny(cls, token_info):
        """Decide whether to block the caller, honouring log-only mode.

        Returns a ``(response, status)`` tuple when the request must be
        rejected, otherwise ``None``. When ``CALLER_CHECK_LOG_ONLY`` is enabled
        an unauthorized caller is logged but allowed through, so the allowlist
        can be populated from real traffic before enforcement is turned on.
        """
        if cls.is_authorized_caller(token_info):
            return None

        info = token_info or {}
        detail = (
            f"azp={info.get('azp')} "
            f"client_id={info.get('client_id') or info.get('clientId')} "
            f"idir={cls.is_idir(info)} "
            f"service_account={cls.is_service_account(info)}"
        )

        log_only = str(
            current_app.config.get("CALLER_CHECK_LOG_ONLY", "false")
        ).lower() == "true"
        if log_only:
            current_app.logger.warning("Caller check (log-only) would block: %s", detail)
            return None

        current_app.logger.warning("Caller check blocked request: %s", detail)
        return (
            {"message": "Caller not permitted to access this API"},
            HTTPStatus.FORBIDDEN,
        )

    @classmethod
    def require(cls, f):
        """Validate the Bearer Token and enforce the layered caller policy."""

        @jwt.requires_auth
        @wraps(f)
        def decorated(*args, **kwargs):
            g.authorization_header = request.headers.get("Authorization", None)
            g.token_info = g.jwt_oidc_token_info

            denied = cls._deny(g.token_info)
            if denied is not None:
                return denied

            return f(*args, **kwargs)

        return decorated


auth = (
    Auth()
)
