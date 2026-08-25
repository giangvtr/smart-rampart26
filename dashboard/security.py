"""
Basic POC authentication for the dashboard override/disarm controls.

Scope (agreed for the hackathon MVP): a single shared agent credential, stored
here as a salted PBKDF2-SHA256 hash -- the plaintext password is NEVER in the
source. Read-only monitoring needs no login; only the alarm-clearing / disarm
actions are gated.

    Demo credentials  ->  username: guard   password: MuseumGuard!2026
    (documented in README.md; change SALT_HEX/HASH_HEX to rotate it, see below)

------------------------------------------------------------------------------
Deferred upgrade -- "real security" for the Arduino <-> laptop link
------------------------------------------------------------------------------
The login here only protects the *dashboard UI*. It does NOT authenticate the
radio/serial link. When you move off USB to Bluetooth/WiFi, the honest fix is to
treat the link as untrusted and authenticate every frame:

    frame = payload || counter || HMAC-SHA256(shared_key, payload || counter)

  * HMAC gives integrity + authenticity so a "DISARM"/"RESET" command cannot be
    forged; the monotonic `counter` blocks replay of a captured command.
  * Sensor telemetry isn't confidential, so authenticity beats encryption; add
    an AEAD (ChaCha20-Poly1305 / ASCON) later only if confidentiality is needed.

`core.LineCodec` is the drop-in point: verify the HMAC in `decode_reading`
(reject on mismatch) and append it in `encode_command`. Not wired in this POC.
"""
from __future__ import annotations

import hashlib
import hmac

# Regenerate with:
#   python -c "import hashlib,os;s=os.urandom(16);\
#   print(s.hex(), hashlib.pbkdf2_hmac('sha256', b'NEWPASS', s, 200_000).hex())"
_SALT_HEX = "9f2c1a77b4e83d5061c8a4f2e7d90b13"
_HASH_HEX = "cf47e7b1cb8c914514202f14549661004e03d4544e6246394d6877757c2814fb"
_ITERATIONS = 200_000
_USERNAME = "guard"


def verify_password(username: str, password: str) -> bool:
    """Constant-time check of a username/password against the stored hash."""
    salt = bytes.fromhex(_SALT_HEX)
    expected = bytes.fromhex(_HASH_HEX)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    user_ok = hmac.compare_digest(username.strip().lower(), _USERNAME)
    pass_ok = hmac.compare_digest(candidate, expected)
    return user_ok and pass_ok


class Session:
    """Tiny in-memory login state; there is no persistence/token for the POC."""

    def __init__(self) -> None:
        self._user: str | None = None

    @property
    def authenticated(self) -> bool:
        return self._user is not None

    @property
    def user(self) -> str | None:
        return self._user

    def login(self, username: str, password: str) -> bool:
        if verify_password(username, password):
            self._user = username.strip().lower()
            return True
        return False

    def logout(self) -> None:
        self._user = None
