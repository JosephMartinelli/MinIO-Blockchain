import json
import time

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from ..dependency import get_peers, get_blockchain
from ..ac_validation import (
    ChallengeRequest,
    ChallengeResponse,
    UserSignedRequestAccess,
)
from typing import Annotated
from ..security import get_mem_nonce, get_security_settings, SecuritySettings
from ..security import (
    verify_user_message,
    create_access_token,
    decode_access_token,
    decode_and_verify_jwt_signature,
)
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


@router.head(path="/auth", status_code=200)
async def is_alive():
    return {}


@router.post(path="/auth", response_model=ChallengeResponse | dict, status_code=200)
async def challenge(
    mem_nonces: nonce_dependency,
    settings: security_settings_dep,
    client: (
        ChallengeRequest | UserSignedRequestAccess | None
    ) = None,  # This means that an empty body might be sent ( it is the case of MinIO POST)
    token: str | None = None,
):
    if isinstance(client, ChallengeRequest) and token is None:
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
    elif isinstance(client, UserSignedRequestAccess) and token is None:
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
        }
        return JSONResponse(status_code=201, content=create_access_token(payload))
    elif token:
        # TODO: A check should be done here to see if the iss is a known and authorized node in the network
        try:
            decoded_token = decode_and_verify_jwt_signature(token)
        except InvalidSignature:
            return JSONResponse(
                status_code=403, content={"reason": "Invalid signature"}
            )
        return {
            "user": decoded_token["client_id"],
            # TODO: This should be dealt better and it must be between 900 and 31536000
            "maxValiditySeconds": 86000,
            "claims": {
                "policy": "read_and_write",
                "client_id": decoded_token["client_id"],
                "sub": decoded_token["sub"],
            },
        }
    else:
        return JSONResponse(status_code=200, content="")


# TODO: Define automatic scheduling procedure that when a JWT expiration triggers a mining operation
