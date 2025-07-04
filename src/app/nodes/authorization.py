from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from validation import AccessRequest
from ..security import decode_access_token
from ..dependency import get_peers, get_policies_cache, get_identity_policies_cache
from authentication import check_authentication
from typing import Annotated

router = APIRouter(
    dependencies=[
        Depends(get_peers),
        Depends(get_policies_cache),
        Depends(get_identity_policies_cache),
    ]
)

peers_dependency = Annotated[set, Depends(get_peers)]
policy_dependency = Annotated[dict, Depends(get_policies_cache)]
identity_dependency = Annotated[dict, Depends(get_identity_policies_cache)]


@router.post(path="/authorize")
async def authorization(
    jwt: AccessRequest,
    peers: peers_dependency,
    mem_policies: policy_dependency,
    identity_policies: identity_dependency,
):
    decoded_token = decode_access_token(jwt.model_dump())
    # First step we verify the source, i.e was the node authenticated by a peer?
    if not await check_authentication(jwt, peers=peers):
        return JSONResponse(
            status_code=403,
            content={"reason": "User has not been authenticated by the chain!"},
        )
    # 1. Fetch all the policies associated with that user identity

    # 2. Figure out what is trying to do, and if it is acting outside of his groups
    # 3. Find any policies associated with him that may prevent him from doing something
