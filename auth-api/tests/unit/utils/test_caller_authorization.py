# Copyright © 2024 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for the layered caller authorization policy in auth.Auth.

Covers the three-layer policy:
- Layer 2: IDIR end users must originate from an allowlisted client (`azp`).
- Layer 3: non-IDIR callers must be service accounts.
Audience (Layer 1) is enforced upstream and is not exercised here.
"""
from http import HTTPStatus

import pytest
from flask import Flask

from auth_api.auth import Auth


# Representative, sanitized claim sets derived from real tokens.
SERVICE_ACCOUNT_TOKEN = {
    "azp": "submit-api-condition-client",
    "client_id": "submit-api-condition-client",
    "preferred_username": "service-account-submit-api-condition-client",
    "realm_access": {"roles": ["default-roles-eao-epic"]},
}

IDIR_USER_TOKEN = {
    "azp": "epic-centre",
    "sid": "8U0jMP2ouji7rg-5JPD-hih2",
    "preferred_username": "b16917cd4cba4df6acb9ff5ca4e56b28@idir",
    "email": "someone@gov.bc.ca",
}


def _app(allowed="", log_only="false"):
    """Build a minimal Flask app carrying only the caller-check config."""
    app = Flask(__name__)
    app.config["ALLOWED_CLIENT_IDS"] = allowed
    app.config["CALLER_CHECK_LOG_ONLY"] = log_only
    return app


class TestIsIdir:
    """Classify IDIR end users."""

    def test_identity_provider_claim_wins(self):
        """An explicit identity_provider=idir claim is honoured."""
        assert Auth.is_idir({"identity_provider": "IDIR"}) is True
        assert Auth.is_idir({"identity_provider": "bceid"}) is False

    def test_username_fallback_matches_guid_at_idir(self):
        """Falls back to the 32-hex-guid@idir username shape."""
        assert Auth.is_idir(IDIR_USER_TOKEN) is True

    def test_non_idir_username_is_false(self):
        """A non-matching username is not treated as IDIR."""
        assert Auth.is_idir({"preferred_username": "service-account-foo"}) is False
        assert Auth.is_idir({"preferred_username": "someone@bceid"}) is False

    def test_empty_token(self):
        """Missing/empty token info is not IDIR and does not raise."""
        assert Auth.is_idir({}) is False
        assert Auth.is_idir(None) is False


class TestIsServiceAccount:
    """Classify client-credentials (service account) tokens."""

    def test_service_account_token(self):
        """client_id present and no session => service account."""
        assert Auth.is_service_account(SERVICE_ACCOUNT_TOKEN) is True

    def test_idir_user_is_not_service_account(self):
        """A token with a session is never a service account."""
        assert Auth.is_service_account(IDIR_USER_TOKEN) is False

    def test_client_id_with_session_is_not_service_account(self):
        """A session present disqualifies even if client_id exists."""
        token = {"client_id": "x", "sid": "abc"}
        assert Auth.is_service_account(token) is False

    def test_no_client_id_is_not_service_account(self):
        """Without client_id it is not a service account."""
        assert Auth.is_service_account({"azp": "x"}) is False

    def test_empty_token(self):
        """Missing/empty token info is not a service account."""
        assert Auth.is_service_account({}) is False
        assert Auth.is_service_account(None) is False


class TestIsAuthorizedCaller:
    """Full layered policy decision."""

    def test_service_account_allowed(self):
        """A service account is allowed regardless of the allowlist."""
        with _app(allowed="").app_context():
            assert Auth.is_authorized_caller(SERVICE_ACCOUNT_TOKEN) is True

    def test_idir_in_allowlist_allowed(self):
        """An IDIR user from an allowlisted client is permitted."""
        with _app(allowed="epic-centre,epic-submit").app_context():
            assert Auth.is_authorized_caller(IDIR_USER_TOKEN) is True

    def test_idir_not_in_allowlist_blocked(self):
        """An IDIR user from a non-allowlisted client is rejected."""
        with _app(allowed="epic-submit").app_context():
            assert Auth.is_authorized_caller(IDIR_USER_TOKEN) is False

    def test_idir_empty_allowlist_blocked(self):
        """With an empty allowlist every IDIR user is rejected (fail-closed)."""
        with _app(allowed="").app_context():
            assert Auth.is_authorized_caller(IDIR_USER_TOKEN) is False

    def test_non_idir_non_service_blocked(self):
        """A human from another IdP (session, no client_id) is rejected."""
        token = {"azp": "epic-centre", "sid": "abc", "preferred_username": "x@bceid"}
        with _app(allowed="epic-centre").app_context():
            assert Auth.is_authorized_caller(token) is False


class TestDeny:
    """Enforcement vs. log-only behaviour of the gate."""

    def test_authorized_caller_not_denied(self):
        """An authorized caller yields no denial."""
        with _app(allowed="epic-centre").app_context():
            assert Auth._deny(IDIR_USER_TOKEN) is None  # pylint: disable=protected-access

    def test_unauthorized_caller_denied_with_403(self):
        """An unauthorized caller is denied with a 403 when enforcing."""
        with _app(allowed="epic-submit").app_context():
            denied = Auth._deny(IDIR_USER_TOKEN)  # pylint: disable=protected-access
        assert denied is not None
        _body, status = denied
        assert status == HTTPStatus.FORBIDDEN

    def test_log_only_mode_allows_unauthorized(self):
        """Log-only mode logs but does not block an unauthorized caller."""
        with _app(allowed="epic-submit", log_only="true").app_context():
            assert Auth._deny(IDIR_USER_TOKEN) is None  # pylint: disable=protected-access
