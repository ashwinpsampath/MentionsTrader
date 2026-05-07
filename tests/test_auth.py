"""
Network-free tests for the auth module by generating a throwaway key
pair and verifying with matching public key.
"""
import base64
import time

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from src.auth import (
    build_auth_headers,
    current_timestamp_ms,
    sign_request,
)


@pytest.fixture
def test_private_key():
    """
    Generate a fresh RSA key pair for use in tests.
    
    A pytest fixture is a function that produces a value tests can use.
    Any test that has `test_private_key` as a parameter will get a freshly
    generated key. This is more isolated than sharing one key across tests.
    """
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


# ============================================================
# Tests for current_timestamp_ms
# ============================================================

def test_current_timestamp_ms_returns_string():
    """The function must return a string, not an int — Kalshi headers are text."""
    result = current_timestamp_ms()
    assert isinstance(result, str)


def test_current_timestamp_ms_is_in_milliseconds():
    """
    The result should be in milliseconds, not seconds.
    A millisecond timestamp for any time after 2001 has 13 digits.
    A second timestamp has only 10. This catches the bug we fixed earlier.
    """
    result = current_timestamp_ms()
    assert len(result) == 13, f"Expected 13-digit ms timestamp, got: {result}"


def test_current_timestamp_ms_is_close_to_now():
    """The timestamp should be roughly 'now' — within 1 second."""
    # YOUR CODE HERE
    # Hint: get current_timestamp_ms(), convert to int,
    # compare against int(time.time() * 1000)
    # Allow a small difference (say, 1000ms) to account for execution time
    test_time = int(current_timestamp_ms())
    curr_time = int(time.time() * 1000)
    assert abs(curr_time - test_time) <= 1000


# ============================================================
# Tests for sign_request
# ============================================================

def test_sign_request_returns_non_empty_string(test_private_key):
    """Basic sanity: signing produces a non-empty string."""
    # YOUR CODE HERE
    # Call sign_request with the fixture key, any method/path/timestamp
    # Assert the result is a string and has length > 0
    signed_req = sign_request(test_private_key,"GET","/trade-api/v2/portfolio/orders",current_timestamp_ms())
    assert isinstance(signed_req,str) and len(signed_req) > 0


def test_sign_request_output_is_valid_base64(test_private_key):
    """
    The output should decode cleanly as base64.
    base64.b64decode() raises an exception on invalid input.
    """
    signature_str = sign_request(
        test_private_key, "GET", "/trade-api/v2/markets", "1714521600000"
    )
    # If this doesn't raise, the output is valid base64
    decoded = base64.b64decode(signature_str)
    # And the decoded length should be 256 bytes for a 2048-bit RSA key
    assert len(decoded) == 256


def test_sign_request_signature_actually_verifies(test_private_key):
    """
    The gold-standard test: a signature we produce must verify
    against the matching public key. If this passes, our signing
    logic is cryptographically correct.
    """
    method = "POST"
    path = "/trade-api/v2/portfolio/orders"
    timestamp = "1714521600000"
    
    # Sign the message
    signature_b64 = sign_request(test_private_key, method, path, timestamp)
    signature_bytes = base64.b64decode(signature_b64)
    
    # Reconstruct the message that should have been signed
    expected_message = f"{timestamp}{method}{path}".encode("utf-8")
    
    # Verify with the public key — this raises InvalidSignature if wrong
    public_key = test_private_key.public_key()
    public_key.verify(
        signature_bytes,
        expected_message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )
    # If verify() didn't raise, the test passes


def test_sign_request_different_calls_produce_different_signatures(test_private_key):
    """
    Because PSS uses a random salt, signing the same message twice
    should produce different signatures. This confirms PSS randomness
    is actually working.
    """
    # Sign the same message twice, assert the two signatures differ
    method = "POST"
    path = "/trade-api/v2/portfolio/orders"
    timestamp = "1714521600000"
    
    # Sign the message
    signature_b64_a = sign_request(test_private_key, method, path, timestamp)
    signature_b64_b = sign_request(test_private_key, method, path, timestamp)
    assert signature_b64_a != signature_b64_b
    


# ============================================================
# Tests for build_auth_headers
# ============================================================

def test_build_auth_headers_contains_all_three_kalshi_headers(test_private_key):
    """The returned dict must have all three KALSHI-ACCESS-* headers."""
    headers = build_auth_headers(
        test_private_key, "test-key-id", "GET", "/trade-api/v2/markets"
    )
    assert "KALSHI-ACCESS-KEY" in headers
    assert "KALSHI-ACCESS-TIMESTAMP" in headers
    assert "KALSHI-ACCESS-SIGNATURE" in headers


def test_build_auth_headers_uses_provided_api_key_id(test_private_key):
    """The KALSHI-ACCESS-KEY header should match what we passed in."""
    headers = build_auth_headers(
        test_private_key, "test-key-id", "GET", "/trade-api/v2/markets"
    )
    assert headers["KALSHI-ACCESS-KEY"] == "test-key-id"