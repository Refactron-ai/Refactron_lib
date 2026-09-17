"""Tests for device-code authentication helpers."""

import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from refactron.core.device_auth import (
    DeviceAuthorization,
    TokenResponse,
    _normalize_base_url,
    _post_json,
    poll_for_token,
    start_device_authorization,
)


def test_normalize_base_url():
    """Test URL normalization."""
    assert _normalize_base_url("https://api.test.com/") == "https://api.test.com"
    assert _normalize_base_url("https://api.test.com") == "https://api.test.com"
    assert _normalize_base_url("  https://api.test.com/  ") == "https://api.test.com"
    assert _normalize_base_url(None) == ""


@patch("refactron.core.device_auth.urlopen")
def test_post_json_success(mock_urlopen):
    """Test successful JSON POST."""
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"status": "ok"}'
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    result = _post_json("https://api.test.com", {"data": "test"})
    assert result == {"status": "ok"}


@patch("refactron.core.device_auth.urlopen")
def test_post_json_http_error(mock_urlopen):
    """Test HTTP error handling in _post_json."""
    error_response = MagicMock()
    error_response.read.return_value = b'{"error": "forbidden"}'
    mock_error = HTTPError("url", 403, "Forbidden", {}, error_response)
    mock_urlopen.side_effect = mock_error

    result = _post_json("https://api.test.com", {"data": "test"})
    assert result == {"error": "forbidden"}


@patch("refactron.core.device_auth._post_json")
def test_start_device_authorization(mock_post):
    """Test starting device authorization."""
    mock_post.return_value = {
        "device_code": "dev_123",
        "user_code": "USER-123",
        "verification_uri": "https://refactron.dev/verify",
        "expires_in": 900,
        "interval": 5,
    }

    auth = start_device_authorization()
    assert isinstance(auth, DeviceAuthorization)
    assert auth.device_code == "dev_123"
    assert auth.user_code == "USER-123"


@patch("refactron.core.device_auth._post_json")
def test_start_device_authorization_invalid_response(mock_post):
    """Test handling of invalid authorization response."""
    mock_post.return_value = {"error": "invalid_client"}
    with pytest.raises(RuntimeError, match="Invalid /oauth/device response"):
        start_device_authorization()


@patch("refactron.core.device_auth._post_json")
def test_poll_for_token_success(mock_post):
    """Test successful token polling."""
    # First response is pending, second is success
    mock_post.side_effect = [
        {"error": "authorization_pending"},
        {
            "access_token": "token_123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "user": {"email": "test@example.com", "plan": "pro"},
        },
    ]

    # Mock sleep to avoid waiting
    with patch("time.sleep"):
        token = poll_for_token("dev_123")
        assert isinstance(token, TokenResponse)
        assert token.access_token == "token_123"
        assert token.email == "test@example.com"
        assert token.plan == "pro"


@patch("refactron.core.device_auth._post_json")
def test_poll_for_token_timeout(mock_post):
    """Test token polling timeout."""
    mock_post.return_value = {"error": "authorization_pending"}

    with patch("time.monotonic") as mock_time:
        # Simulate time passing quickly
        mock_time.side_effect = [0, 1000]
        with pytest.raises(RuntimeError, match="Login timed out"):
            poll_for_token("dev_123", expires_in_seconds=10)


@patch("refactron.core.device_auth._post_json")
def test_poll_for_token_expired(mock_post):
    """Test token polling with expired code."""
    mock_post.return_value = {"error": "expired_token"}
    with pytest.raises(RuntimeError, match="Device code expired"):
        poll_for_token("dev_123")
