"""
Handles request signing for the Kalshi API.
"""
import base64
import time
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def load_private_key(key_path: str) -> rsa.RSAPrivateKey:
    """
    Load an RSA private key from a PEM file on disk.
    Returns the parsed private key object that we can sign with.
    """
    key_in_bytes = Path(key_path).read_bytes()
    return serialization.load_pem_private_key(key_in_bytes,password=None)
    


def current_timestamp_ms() -> str:
    """
    Return the current Unix timestamp in ms as a string as Kalshi requires.
    """
    return str(int(time.time() * 1000))




def sign_request(
    private_key: rsa.RSAPrivateKey,
    method: str,
    path: str,
    timestamp_ms: str,
) -> str:
    """
    Sign a Kalshi API request.

    Constructs the string-to-sign as: timestamp_ms + method + path
    Signs it using RSA-PSS with SHA-256.
    Returns the base64-encoded signature as a string.

    Args:
        private_key: The loaded RSA private key
        method: HTTP method, uppercase (e.g. "GET", "POST")
        path: The request path including /trade-api/v2 prefix
              (e.g. "/trade-api/v2/portfolio/orders")
        timestamp_ms: The timestamp string to include (must match what
                      gets sent in the KALSHI-ACCESS-TIMESTAMP header)

    Returns:
        Base64-encoded signature, ready to be put in the
        KALSHI-ACCESS-SIGNATURE header.
    """
    message = f"{timestamp_ms}{method}{path}".encode('utf-8')
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')
                    


def build_auth_headers(
    private_key: rsa.RSAPrivateKey,
    api_key_id: str,
    method: str,
    path: str,
) -> dict[str, str]:
    """
    Build the complete set of auth headers for a Kalshi request.
    Returns a dict ready to merge into requests headers
    """
    timestamp_ms = current_timestamp_ms()
    signature = sign_request(private_key,method,path,timestamp_ms)
    return {
        'KALSHI-ACCESS-KEY': api_key_id,
        'KALSHI-ACCESS-TIMESTAMP': timestamp_ms,
        'KALSHI-ACCESS-SIGNATURE': signature,
    }
