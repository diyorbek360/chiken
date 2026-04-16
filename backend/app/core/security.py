import hmac
import hashlib
import json
from urllib.parse import unquote
from fastapi import HTTPException, Header, Depends
from app.core.config import settings


def verify_telegram_webapp(init_data: str) -> dict:
    """Verify Telegram WebApp initData and return parsed user data."""
    try:
        parsed = {}
        for part in init_data.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                parsed[unquote(k)] = unquote(v)

        hash_value = parsed.pop("hash", None)
        if not hash_value:
            raise ValueError("No hash in initData")

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )

        secret_key = hmac.new(
            b"WebAppData", settings.TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256
        ).digest()

        computed_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, hash_value):
            raise ValueError("Invalid hash")

        user_data = json.loads(parsed.get("user", "{}"))
        return user_data

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Telegram data: {e}")


async def get_current_user_id(x_init_data: str = Header(None)) -> int:
    """FastAPI dependency - extract and verify Telegram user ID."""
    if not x_init_data:
        raise HTTPException(status_code=401, detail="Missing X-Init-Data header")

    if settings.DEBUG and x_init_data.startswith("debug:"):
        # For local development: "debug:123456789"
        return int(x_init_data.split(":")[1])

    user_data = verify_telegram_webapp(x_init_data)
    user_id = user_data.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="No user ID in Telegram data")
    return int(user_id)


async def get_admin_user(user_id: int = Depends(get_current_user_id)) -> int:
    """Ensure user is admin."""
    if user_id not in settings.admin_id_list:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id
