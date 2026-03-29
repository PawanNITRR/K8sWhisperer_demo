from __future__ import annotations

from slack_sdk.signature import SignatureVerifier


def verify_slack_request(signing_secret: str, body: bytes, timestamp: str, signature: str) -> bool:
    if not signing_secret:
        return False
    verifier = SignatureVerifier(signing_secret)
    return verifier.is_valid(body=body, timestamp=timestamp, signature=signature)
