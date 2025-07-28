from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse
from starlette.requests import Request

from ..ac_validation import ACResourcePolicy, ACIdentityPolicy
from ..dependency import get_peers, get_policies_cache, get_identity_policies_cache
from typing import Annotated

router = APIRouter(
    dependencies=[
        Depends(get_peers),
        Depends(get_policies_cache),
        Depends(get_identity_policies_cache),
    ]
)

peers_dependency = Annotated[set, Depends(get_peers)]
resource_policy_dependency = Annotated[dict, Depends(get_policies_cache)]
identity_dependency = Annotated[dict, Depends(get_identity_policies_cache)]


def extract_user_data(auth_request: dict) -> dict:
    return {
        "account": auth_request["input"]["account"],
        "groups": auth_request["input"]["groups"],
        "action": auth_request["input"]["action"],
        "bucket": auth_request["input"]["bucket"],
        "policies": auth_request["input"]["conditions"]["policy"],
        "owner": auth_request["input"]["owner"],
        "claims": auth_request["input"]["claims"],
    }


def evaluate_identity_policies(
    user_identity_policies: dict[str, ACIdentityPolicy],
    user_data: dict[str, str | list],
) -> tuple[str, bool]:
    for policy in user_identity_policies.values():
        for statement in policy.statements.values():
            action_match = set(user_data["action"]).issubset(statement.action)
            resource_match = set(user_data["resources"]).issubset(statement.resource)
            if action_match and resource_match:
                if statement.effect == "Deny":
                    return "Explicit Deny", False  # Explicit deny, immediate rejection
            else:
                return "Implicit Deny", False  # Implicit deny on first mismatch
    return "Allow", True


def evaluate_resource_policies(
    resource_policies: dict[str, ACResourcePolicy], user_data: dict[str, str | list]
) -> tuple[str, bool]:
    for policy in resource_policies.values():
        for statement in policy.statements.values():
            action_match = set(user_data["action"]).issubset(statement.action)
            resource_match = set(user_data["bucket"]).issubset(statement.resource)
            principal_match = set(user_data["claims"]["client_id"]).issubset(
                statement.principal
            )
            if action_match and resource_match and principal_match:
                if statement.effect == "Deny":
                    return "Explicit Deny", False  # Explicit deny, immediate rejection
            else:
                return "Implicit Deny", False  # Implicit deny on first mismatch

    return "Allow", True


def fetch_group_policies(user_data: dict):
    pass


@router.post(path="/authZ", status_code=200)
async def authorization(
    request: Request,
    peers: peers_dependency,
    resource_policies: resource_policy_dependency,
    identity_policies: identity_dependency,
):
    dict_body = await request.json()
    user_data = extract_user_data(dict_body)
    # 1. Fetch all the policies associated with that user identity
    user_identity_policies = identity_policies.get(
        user_data["claims"]["client_id"], None
    )

    # 2. Fetch all the policies associated with that user group
    # user_group_policies = fetch_group_policies[user_data["groups"]]

    # 3. Fetch all the policies associated with that resource
    r_policies = resource_policies.get(user_data["bucket"], None)

    # 4. Figure out what is trying to do, and if it is acting outside his identity
    if user_identity_policies is not None:
        result, allow = evaluate_identity_policies(user_identity_policies, user_data)
        if not allow:
            return JSONResponse(
                status_code=403,
                content={
                    "reason": f"Identity policies does not allow these actions!, {result}"
                },
            )
    else:
        return JSONResponse(
            status_code=403,
            content={
                "reason": "This user has no identity policies associated with it!"
            },
        )
    # 5. Check if the user is allowed given his group
    # This is yet to be implemented

    # 6. Find any resource policies associated with him that may prevent him from doing something
    if r_policies is not None:
        result, allow = evaluate_resource_policies(r_policies, user_data)
        if not allow:
            return JSONResponse(
                status_code=403,
                content={
                    "reason": f"Identity policies does not allow these actions!, {result}"
                },
            )
    else:
        return JSONResponse(
            status_code=403,
            content={"reason": "No resource policies have been found!"},
        )

    return {"result": {"allow": True}}
