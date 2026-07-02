from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from pwdlib.exceptions import UnknownHashError

from app.core.exceptions import (
    DataIntegrityError,
    InvalidTokenSignatureError,
    TokenDecodingError,
    TokenExpiredError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_jwt,
    hash_password,
    verify_password,
)
from app.core.settings import settings


############################################################################### create_access_token
class TestCreateAccessToken:
    # --- 1. Success Cases ---
    def test_create_access_token_success_default_expire(self):
        """Verifies standard generation with default expiration settings when 'sub' is provided."""
        payload = {"sub": "user-123-uuid", "role": "admin"}

        token = create_access_token(data=payload)

        assert isinstance(token, str)
        decoded = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        assert decoded["sub"] == "user-123-uuid"
        assert decoded["role"] == "admin"
        assert "exp" in decoded

        # Verify expiration timing limits
        expected_expiry = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        decoded_expiry = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        assert abs((expected_expiry - decoded_expiry).total_seconds()) < 5

    def test_create_access_token_custom_expire(self):
        """Verifies that passing custom minutes overrides the default setting."""
        payload = {"sub": "user-123-uuid"}
        custom_minutes = 10

        token = create_access_token(
            data=payload, ACCESS_TOKEN_EXPIRE_MINUTES=custom_minutes
        )
        decoded = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        expected_expiry = datetime.now(timezone.utc) + timedelta(minutes=custom_minutes)
        decoded_expiry = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        assert abs((expected_expiry - decoded_expiry).total_seconds()) < 5

    # --- 2. Validation / Exception Cases ---
    @pytest.mark.parametrize(
        "invalid_payload",
        [
            {},  # Completely empty dict
            {"role": "admin"},  # Data exists, but missing 'sub'
            {"subject": "user-123"},  # Wrong key name entirely
        ],
    )
    def test_create_access_token_raises_on_missing_sub(self, invalid_payload):
        """Verifies that any payload lacking a 'sub' key triggers a DataIntegrityError."""
        with pytest.raises(DataIntegrityError) as exc_info:
            create_access_token(data=invalid_payload)

        assert str(exc_info.value) == "Token payload has to contain 'sub' field."

    def test_create_access_token_does_not_mutate_input(self):
        """Verifies function leaves the original input dictionary completely intact."""
        payload = {"sub": "user-456-uuid"}

        create_access_token(data=payload)

        assert "exp" not in payload
        assert list(payload.keys()) == ["sub"]


################################################################################# create_refresh_token
class TestCreateRefreshToken:
    @pytest.mark.asyncio
    @patch("app.core.security.set_valkey_session", new_callable=AsyncMock)
    async def test_create_refresh_token_success_default_expire(self, mock_set_session):
        """Case A & C: Standard generation with default expiration, unique JTIs, and cache logging."""
        payload = {"sub": "user-789-uuid", "org": "my-company"}
        mock_valkey = AsyncMock()

        # Run token generation twice to guarantee JTI uniqueness
        token_1 = await create_refresh_token(data=payload, valkey=mock_valkey)
        token_2 = await create_refresh_token(data=payload, valkey=mock_valkey)

        assert isinstance(token_1, str)
        assert isinstance(token_2, str)
        assert token_1 != token_2  # Dynamic uuid4 ensures tokens aren't identical

        # Decode and inspect properties
        decoded1 = jwt.decode(
            token_1, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert decoded1["sub"] == "user-789-uuid"
        assert decoded1["org"] == "my-company"
        assert "jti" in decoded1
        assert "exp" in decoded1

        decoded2 = jwt.decode(
            token_2, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert decoded2["sub"] == "user-789-uuid"
        assert decoded2["org"] == "my-company"
        assert "jti" in decoded2
        assert "exp" in decoded2

        # Verify time calculation limits (default days config)
        expected_expiry1 = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        decoded_expiry1 = datetime.fromtimestamp(decoded1["exp"], tz=timezone.utc)
        assert abs((expected_expiry1 - decoded_expiry1).total_seconds()) < 5

        expected_expiry2 = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        decoded_expiry2 = datetime.fromtimestamp(decoded1["exp"], tz=timezone.utc)
        assert abs((expected_expiry2 - decoded_expiry2).total_seconds()) < 5

        # Verify set_valkey_session utility was invoked properly
        assert mock_set_session.call_count == 2
        # Verify the target arguments passed to the cache layer match payload variables
        called_args1 = mock_set_session.call_args_list[0][0]
        assert called_args1[0] == "user-789-uuid"  # str_user_id
        assert called_args1[1] == decoded1["jti"]  # str_jti
        assert called_args1[2] == timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )  # td_exp
        assert called_args1[3] == mock_valkey  # valkey client instance

        called_args2 = mock_set_session.call_args_list[1][0]
        assert called_args2[0] == "user-789-uuid"  # str_user_id
        assert called_args2[1] == decoded2["jti"]  # str_jti
        assert called_args2[2] == timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )  # td_exp
        assert called_args2[3] == mock_valkey  # valkey client instance

    @pytest.mark.asyncio
    @patch("app.core.security.set_valkey_session", new_callable=AsyncMock)
    async def test_create_refresh_token_custom_expire(self, mock_set_session):
        """Case B: Custom expiration override limits are mapped accurately to JWT and Valkey."""
        payload = {"sub": "user-789-uuid"}
        mock_valkey = AsyncMock()
        custom_days = 14

        token = await create_refresh_token(
            data=payload, valkey=mock_valkey, REFRESH_TOKEN_EXPIRE_DAYS=custom_days
        )
        decoded = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        # Validate JWT expiration
        expected_expiry = datetime.now(timezone.utc) + timedelta(days=custom_days)
        decoded_expiry = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        assert abs((expected_expiry - decoded_expiry).total_seconds()) < 5

        # Validate Valkey time-to-live delta configuration mismatch check
        called_args = mock_set_session.call_args[0]
        assert called_args[2] == timedelta(days=custom_days)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "invalid_payload",
        [
            {},
            {"role": "user"},
        ],
    )
    async def test_create_refresh_token_raises_on_missing_sub(self, invalid_payload):
        """Case E: Guardrail prevents creating a refresh token without a 'sub' field."""
        mock_valkey = AsyncMock()

        with pytest.raises(DataIntegrityError) as exc_info:
            await create_refresh_token(data=invalid_payload, valkey=mock_valkey)

        assert str(exc_info.value) == "Token payload has to contain 'sub' field."

    @pytest.mark.asyncio
    @patch("app.core.security.set_valkey_session", new_callable=AsyncMock)
    async def test_create_refresh_token_does_not_mutate_input(self, mock_set_session):
        """Case D: The caller's source dict remains completely immutable."""
        payload = {"sub": "user-789-uuid"}
        mock_valkey = AsyncMock()

        await create_refresh_token(data=payload, valkey=mock_valkey)

        assert "jti" not in payload
        assert "exp" not in payload
        assert list(payload.keys()) == ["sub"]


################################################################################# decode_jwt
class TestDecodeJWT:
    def test_decode_jwt_success_case_a(self):
        """Case A: Successfully decodes a structurally sound, signed, and unexpired token."""
        payload = {"sub": "user-123-uuid", "role": "user"}
        token = create_access_token(data=payload)

        result = decode_jwt(token)

        assert result["sub"] == "user-123-uuid"
        assert result["role"] == "user"
        assert "exp" in result

    def test_decode_jwt_expired_case_b(self):
        """Case B: Catches an expired token and raises a custom TokenExpiredError."""
        # Create a payload explicitly timestamped 10 minutes in the past
        expired_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        payload = {"sub": "user-123-uuid", "exp": expired_time}

        # Manually encode using the standard library to bypass our function's safety rules
        expired_token = jwt.encode(
            payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        with pytest.raises(TokenExpiredError):
            decode_jwt(expired_token)

    def test_decode_jwt_invalid_signature_case_c(self):
        """Case C: Catches a tampered signature or bad key and raises InvalidTokenSignatureError."""
        payload = {"sub": "user-123-uuid"}
        # Sign the token using an invalid secret key
        bad_signed_token = jwt.encode(
            payload,
            "WRONG_SECRET_KEY_skibidisgima67gyatmaxxing2137billgates",
            algorithm=settings.ALGORITHM,
        )

        with pytest.raises(InvalidTokenSignatureError):
            decode_jwt(bad_signed_token)

    def test_decode_jwt_malformed_string_case_d(self):
        """Case D: Catches structurally invalid garbage strings and raises TokenDecodingError."""
        malformed_token = "not.a.valid.jwt.string"

        with pytest.raises(TokenDecodingError) as exc_info:
            decode_jwt(malformed_token)

        assert exc_info.value.message == "Malformed or invalid token."


###################################################### hash_password && verify_password
class TestPasswordSecurity:
    @pytest.mark.asyncio
    async def test_hash_password_success_cases_a_and_b(self):
        """Cases A & B: Successfully hashes a password and ensures salt uniqueness."""
        password = "SuperSecretPassword123!"

        hash_1 = await hash_password(password)
        hash_2 = await hash_password(password)

        # Case A: Ensure they are valid strings and not empty
        assert isinstance(hash_1, str)
        assert len(hash_1) > 0

        # Case B: Ensure distinct salts mean hashes are never identical
        assert hash_1 != hash_2

    @pytest.mark.asyncio
    async def test_verify_password_correct_case_c(self):
        """Case C: Returns True when verifying the correct password against its hash."""
        password = "MySecurePassword#2026"
        hashed = await hash_password(password)

        is_valid = await verify_password(password, hashed)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_verify_password_incorrect_case_d(self):
        """Case D: Returns False when attempting to verify an incorrect password."""
        password = "CorrectPassword123"
        wrong_password = "IncorrectPassword123"

        hashed = await hash_password(password)

        is_valid = await verify_password(wrong_password, hashed)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_verify_password_malformed_hash_case_e(self):
        """Case E: Verifies that structurally invalid hash strings trigger an UnknownHashError."""
        password = "AnyPassword123"
        malformed_hash = "not-a-valid-cryptographic-hash-string"

        with pytest.raises(UnknownHashError) as exc_info:
            await verify_password(password, malformed_hash)

        assert "This hash can't be identified" in str(exc_info.value)
