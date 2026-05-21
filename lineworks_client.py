import time
from urllib.parse import quote

import jwt
import requests

TOKEN_URL = "https://auth.worksmobile.com/oauth2/v2.0/token"
# ユーザーIDへの直接送信（Channel ID不要）
MESSAGE_URL = "https://www.worksapis.com/v1.0/bots/{bot_id}/users/{user_id}/messages"


def _get_access_token(client_id: str, client_secret: str, service_account: str, private_key_path: str) -> str:
    with open(private_key_path, "r") as f:
        private_key = f.read()

    now = int(time.time())
    payload = {
        "iss": client_id,
        "sub": service_account,
        "iat": now,
        "exp": now + 3600,
    }
    jwt_token = jwt.encode(payload, private_key, algorithm="RS256")

    resp = requests.post(
        TOKEN_URL,
        data={
            "assertion": jwt_token,
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "bot",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def send_message(
    text: str,
    bot_id: str,
    user_id: str,
    client_id: str,
    client_secret: str,
    service_account: str,
    private_key_path: str,
) -> None:
    access_token = _get_access_token(client_id, client_secret, service_account, private_key_path)
    encoded_user_id = quote(user_id, safe="")
    url = MESSAGE_URL.format(bot_id=bot_id, user_id=encoded_user_id)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    body = {"content": {"type": "text", "text": text}}
    resp = requests.post(url, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
