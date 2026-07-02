from uuid import UUID

from app.database.valkey import generate_valkey_session_string


class TestGenerateValkeySessionString:
    def test_generate_valkey_session_string_standard_case_a(self):
        """Case A: Validates correct format structure with standard string inputs."""
        user_id = "user-12345"
        jti = "abc-jti-xyz"
        
        expected_key = "user_id:user-12345:refresh_token_jti:abc-jti-xyz"
        result = generate_valkey_session_string(user_id, jti)
        
        assert result == expected_key

    def test_generate_valkey_session_string_casts_primitives_case_b(self):
        """Case B: Ensures function handles non-string primitives gracefully via f-string auto-casting."""
        user_id = 99999  # Integer input
        jti = "jti-format-777"
        
        expected_key = "user_id:99999:refresh_token_jti:jti-format-777"
        result = generate_valkey_session_string(user_id, jti)  # type: ignore
        
        assert result == expected_key

    def test_generate_valkey_session_string_with_uuids_case_c(self):
        """Case C: Validates formatting with standard raw UUIDv4 inputs."""
        user_uuid = UUID("e8b2b733-4fde-4e3a-bc4b-bfb026bebc71")
        jti_uuid = UUID("11a51139-4d6d-4952-b883-8a39c4a85fa4")
        
        expected_key = f"user_id:{user_uuid}:refresh_token_jti:{jti_uuid}"
        result = generate_valkey_session_string(user_uuid, jti_uuid)
        
        assert result == expected_key