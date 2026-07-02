from unittest.mock import MagicMock, patch
from uuid import uuid4

import jwt
import pytest
from starlette.requests import Request

from app.api.dependencies.auth import (
    CREDENTIALS_EXCEPTION,
    decode_user_id_from_cookie,
    has_token,
    verify_is_anonymous,
    verify_is_not_anonymous,
)
from app.core.exceptions import AuthenticationError, AuthorizationError

has_token
verify_is_anonymous
verify_is_not_anonymous
decode_user_id_from_cookie

class TestHasToken:
    @pytest.mark.parametrize(
        "cookies, expected_result",
        [
            # Scenario 1: Clean Happy Path (Both present)
            # Scenario 2: Access Token Only
            # Scenario 3: Refresh Token Only
            # Scenario 4: Completely Logged Out (No cookies)
            # Scenario 5: Empty Token Strings (Falsy strings)
            # Scenario 6: Explicit Falsy or None Values
            ({"access_token": "valid_access", "refresh_token": "valid_refresh"}, True),
            ({"access_token": "valid_access"}, True),
            ({"refresh_token": "valid_refresh"}, True),
            ({}, False),
            ({"access_token": "", "refresh_token": ""}, False),
            ({"access_token": False, "refresh_token": None}, False),
        ]
    )
    def test_has_token_scenarios(self, cookies, expected_result):
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = cookies

        result = has_token(mock_request)

        assert result is expected_result


class TestVerifyIsAnonymous:
    @patch("app.api.dependencies.auth.has_token")
    def test_verify_is_anonymous_passes(self, mock_has_token):
        mock_has_token.return_value = False
        mock_request = MagicMock(spec=Request)

        result = verify_is_anonymous(mock_request)
        assert result is None

    @patch("app.api.dependencies.auth.has_token")
    def test_verify_is_anonymous_raises_error(self, mock_has_token):
        mock_has_token.return_value = True
        mock_request = MagicMock(spec=Request)

        with pytest.raises(AuthorizationError, match="Route inaccessible for logged in users"):
            verify_is_anonymous(mock_request)


class TestVerifyIsNotAnonymous:
    @patch("app.api.dependencies.auth.has_token")
    def test_verify_is_not_anonymous_passes(self, mock_has_token):
        mock_has_token.return_value = True
        mock_request = MagicMock(spec=Request)

        result = verify_is_not_anonymous(mock_request)
        assert result is None

    @patch("app.api.dependencies.auth.has_token")
    def test_verify_is_not_anonymous_raises_error(self, mock_has_token):
        mock_has_token.return_value = False
        mock_request = MagicMock(spec=Request)

        with pytest.raises(AuthenticationError, match="Route inaccessible for logged out users."):
            verify_is_not_anonymous(mock_request)



def build_mock_request(cookies: dict) -> Request:
    request = MagicMock(spec=Request)
    request.cookies = cookies
    return request
class TestDecodeUserIdFromCookie:
    @patch("app.api.dependencies.auth.decode_jwt")
    def test_decode_success(self, mock_decode_jwt):
        expected_uuid = uuid4()
        mock_decode_jwt.return_value = {"sub": str(expected_uuid)}
        req = build_mock_request({"access_token": "valid_token"})

        result = decode_user_id_from_cookie(req)

        assert result == expected_uuid
        mock_decode_jwt.assert_called_once_with("valid_token")

    def test_missing_cookie_raises(self):
        req = build_mock_request({})

        with pytest.raises(type(CREDENTIALS_EXCEPTION)) as exc_info:
            decode_user_id_from_cookie(req)
        assert exc_info.value == CREDENTIALS_EXCEPTION

    @patch("app.api.dependencies.auth.decode_jwt")
    def test_invalid_jwt_raises(self, mock_decode_jwt):
        mock_decode_jwt.side_effect = jwt.InvalidTokenError()
        req = build_mock_request({"access_token": "forged_token"})

        with pytest.raises(type(CREDENTIALS_EXCEPTION)) as exc_info:
            decode_user_id_from_cookie(req)
        assert exc_info.value == CREDENTIALS_EXCEPTION

    @patch("app.api.dependencies.auth.decode_jwt")
    def test_missing_sub_claim_raises(self, mock_decode_jwt):
        mock_decode_jwt.return_value = {"exp": 123456789}
        req = build_mock_request({"access_token": "valid_token"})

        with pytest.raises(type(CREDENTIALS_EXCEPTION)) as exc_info:
            decode_user_id_from_cookie(req)
        assert exc_info.value == CREDENTIALS_EXCEPTION