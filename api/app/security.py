import base64
import binascii
import logging
import time

from fastapi import Header, HTTPException

LEGACY_SECRET = "WORKSHOP_SECRET_2026"
BEARER_PREFIX = "Bearer "
INVALID_TOKEN_DETAIL = "Invalid token"
logger = logging.getLogger(__name__)


def legacy_identity(authorization: str = Header(default="")) -> dict[str, str]:
    try:
        token = authorization.replace(BEARER_PREFIX, "")
        decoded = base64.b64decode(token).decode("utf-8")
        parts = decoded.split("|")
        if len(parts) != 4 or parts[3] != LEGACY_SECRET or int(parts[2]) < int(time.time()):
            raise ValueError("invalid legacy token")
        return {"username": parts[0], "role": parts[1]}
    except (binascii.Error, UnicodeDecodeError, ValueError) as error:
        logger.info("Rejected legacy token (%s)", type(error).__name__)
        raise HTTPException(status_code=401, detail=INVALID_TOKEN_DETAIL) from error
