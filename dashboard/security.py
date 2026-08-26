"""
Basic POC authentication for the dashboard.

Two tiers (agreed for the hackathon MVP):

  * `viewer` -- gates the dashboard itself (charts, live data). Required just
    to load the page.
  * `guard`  -- gates the override/disarm controls. A guard login is a
    *separate, stronger* credential entered via the in-page "Agent login"
    modal; it does not replace the viewer session, it layers on top of it.

Both are single shared credentials, stored here as salted PBKDF2-SHA256
hashes -- the plaintext passwords are NEVER in the source. See README.md for
the current demo credentials (regenerate with the one-liner below to rotate
them).

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

------------------------------------------------------------------------------
Also deferred: TLS
------------------------------------------------------------------------------
Login still posts the password in the clear over plain HTTP (see server.py).
Putting TLS in front is the next step, held off until the Raspberry Pi
deployment shape (reverse proxy vs. wrapping the socket directly) is decided.
"""
from __future__ import annotations

import hashlib
import hmac
import threading
import time

# Regenerate a credential with:
#   python -c "import hashlib,os;s=os.urandom(16);\
#   print(s.hex(), hashlib.pbkdf2_hmac('sha256', b'NEWPASS', s, 200_000).hex())"
_ITERATIONS = 200_000

# username -> {salt, hash, role}. "guard" can view *and* override; "viewer"
# can only view. Passwords are the 15-char random-looking ones in README.md.
_ACCOUNTS: dict[str, dict[str, str]] = {
    "guard": {
        "salt": "eb47ee0ed884e794ff4959def7c3b2c2",
        "hash": "53ce657fc084450ce0adfb11058fba40fea80b01f9a402e243fcc72a908a4835",
        "role": "guard",
    },
    "viewer": {
        "salt": "ac76f2e934fe67ef8b9331be87769a14",
        "hash": "b7cf19ca77ab3165a7246233e6c64b258919b8636e06c709f18822d506016e84",
        "role": "viewer",
    },
}


def authenticate(username: str, password: str) -> str | None:
    """Constant-time check against the stored hash. Returns the role
    ("guard"/"viewer") on success, None on failure."""
    account = _ACCOUNTS.get(username.strip().lower())
    if account is None:
        # Still do a dummy PBKDF2 round so an unknown username doesn't return
        # measurably faster than a wrong password (basic timing-side-channel hygiene).
        hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), b"\x00" * 16, _ITERATIONS)
        return None
    salt = bytes.fromhex(account["salt"])
    expected = bytes.fromhex(account["hash"])
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    if hmac.compare_digest(candidate, expected):
        return account["role"]
    return None


# Role >= required: guard can do everything viewer can.
_ROLE_RANK = {"viewer": 1, "guard": 2}


def role_satisfies(role: str | None, required: str) -> bool:
    return role is not None and _ROLE_RANK.get(role, 0) >= _ROLE_RANK.get(required, 0)


class RateLimiter:
    """Per-key (typically client IP) login throttle.

    Not persisted -- a process restart clears it, same as the token store.
    Threshold trips after MAX_ATTEMPTS failures within WINDOW_S and locks the
    key out for LOCKOUT_S. This defends against *online* password guessing;
    it does nothing for offline cracking (that's what the PBKDF2 iteration
    count is for).
    """

    MAX_ATTEMPTS = 5
    WINDOW_S = 300.0
    LOCKOUT_S = 300.0

    def __init__(self) -> None:
        self._fails: dict[str, list[float]] = {}
        self._locked_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def seconds_locked(self, key: str) -> float:
        """0.0 if `key` may attempt a login now, else seconds remaining."""
        now = time.time()
        with self._lock:
            until = self._locked_until.get(key, 0.0)
            return max(0.0, until - now)

    def record_failure(self, key: str) -> None:
        now = time.time()
        with self._lock:
            fails = [t for t in self._fails.get(key, []) if now - t < self.WINDOW_S]
            fails.append(now)
            if len(fails) >= self.MAX_ATTEMPTS:
                self._locked_until[key] = now + self.LOCKOUT_S
                fails = []
            self._fails[key] = fails

    def record_success(self, key: str) -> None:
        with self._lock:
            self._fails.pop(key, None)
            self._locked_until.pop(key, None)


LOGIN_LIMITER = RateLimiter()
