import json
import time

import requests
from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from ..dependency import get_peers, get_blockchain
from validation import (
    ChallengeRequest,
    ChallengeResponse,
    UserSignedRequestAccess,
    CheckAuth,
)
from typing import Annotated
from ..security import get_mem_nonce, get_security_settings, SecuritySettings
from ..security import verify_user_message, create_access_token, decode_access_token
import secrets
from cryptography.exceptions import InvalidSignature

router = APIRouter(
    dependencies=[
        Depends(get_peers),
        Depends(get_blockchain),
        Depends(get_mem_nonce),
        Depends(get_security_settings),
    ]
)
peers_dependency = Annotated[set, Depends(get_peers)]
nonce_dependency = Annotated[dict, Depends(get_mem_nonce)]
security_settings_dep = Annotated[SecuritySettings, Depends(get_security_settings)]


@router.post(
    path="/authentication", response_model=ChallengeResponse | dict, status_code=200
)
async def challenge(
    client: ChallengeRequest | UserSignedRequestAccess,
    mem_nonces: nonce_dependency,
    settings: security_settings_dep,
):
    if isinstance(client, ChallengeRequest):
        client_challenge_info: dict = client.model_dump()
        expiration = time.time() + settings.nonce_exp_min * 60 + settings.nonce_exp_s
        nonce = secrets.token_hex(settings.nonce_size)
        mem_nonces.update({client_challenge_info["client_pk"]: (nonce, expiration)})
        return JSONResponse(
            status_code=200,
            content={
                "nonce": nonce,
                "domain": "Sign In to access MinIO resources",
                "expire": expiration,
            },
        )
    else:
        client_signed_message: dict = client.model_dump()
        mem_data = mem_nonces.get(client_signed_message["client_pk"], None)
        if mem_data is None:
            return JSONResponse(
                status_code=403, content="No challenge has been issued for this client!"
            )
        assigned_nonce, expiration = mem_data
        if (
            assigned_nonce != client_signed_message["message"]["nonce"]
            or time.time() > expiration
        ):
            return JSONResponse(status_code=403, content="Invalid or expired nonce!")

        # Signature Verification
        try:
            verify_user_message(
                json.dumps(client_signed_message["message"])
                .replace(": ", ":")
                .replace(', "', ',"')
                .encode(),
                bytes.fromhex(client_signed_message["signature"]),
                bytes.fromhex(client_signed_message["client_pk"]),
            )
        except ValueError:
            return JSONResponse(
                status_code=400,
                content="Signature/public key must be passed as a valid hex string",
            )
        except InvalidSignature:
            return JSONResponse(status_code=403, content="Invalid signature!")
        # Remove saved nonce for the client
        del mem_nonces[client_signed_message["client_pk"]]
        # Issue JWT
        payload = {
            "sub": client_signed_message["client_pk"],
            "client_id": client_signed_message["client_id"],
            "role": "user",
            "principal": client_signed_message["principal"],
            "action": client_signed_message["action"],
            "resources": client_signed_message["resources"],
            "resource_data": client_signed_message["resource_data"],
        }
        return JSONResponse(status_code=201, content=create_access_token(payload))


@router.post("/check-auth", status_code=200)
async def check_authentication(jwt: CheckAuth, peers: peers_dependency) -> dict:
    is_auth = True
    try:
        decoded_jwt = decode_access_token(jwt.model_dump()["jwt"])
    except InvalidSignature:
        for peer in peers:
            try:
                response = requests.post(
                    url=f"http://{peer}/check-auth", data=jwt.model_dump_json()
                )
            except requests.exceptions.ConnectionError:
                continue
            if response.status_code == 200 and response.json()["result"] == True:
                return {"result": True}
        is_auth = False
    return {"result": is_auth}
