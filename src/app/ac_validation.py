from pydantic import ConfigDict, BaseModel, field_validator
from typing import Literal, Dict
from app.security import decode_access_token


class Condition(BaseModel):
    pass


class ACPolicy(BaseModel):
    pass


# The principal here is absent bc it is implicit the user that the policy has been attached to
class ACIdentityStatement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    sid: str
    effect: Literal["Allow", "Deny"]
    action: list[str] | str = []
    resource: list[str] | str
    condition: Dict[str, Condition] = {}


class ACResourceStatement(ACIdentityStatement):
    principal: list[str] | str = []


class ACResourcePolicy(ACPolicy):
    model_config = ConfigDict(extra="forbid")
    id: str
    action: Literal[
        "add", "remove", "update"
    ]  # This is needed for the policy delta operation
    statements: Dict[str, ACResourceStatement] = {}


class ACIdentityPolicy(ACPolicy):
    model_config = ConfigDict(extra="forbid")
    id: str
    action: Literal["add", "remove", "update"]
    statements: Dict[str, ACIdentityStatement] = {}


class Transaction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: list[str | bytes | int] | str
    is_contract: bool = False
    contract_address: str = ""


class UnconfirmedTransaction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transactions: list[Transaction] = []


class RegisterNode(BaseModel):
    node_address: str
    node_port: str


class Client(BaseModel):
    ip_address: str
    port: str


class InputBlock(BaseModel):
    transactions: list[Transaction]
    index: int
    timestamp: str
    previous_hash: str
    proof: int


class ChallengeRequest(BaseModel):
    client_pk: str  # Hex format
    client_id: str
    client_name: str


class ChallengeResponse(BaseModel):
    nonce: str
    domain: str
    expire: float


class UserSignedRequestAccess(BaseModel):
    message: ChallengeResponse
    client_id: str
    client_pk: str  # Hex format
    signature: str  # Hex format


class MinioTokenRequest(BaseModel):
    pass


class AccessRequest(BaseModel):
    token: str

    # @field_validator("jwt", mode="after")
    def check_jwt_payload(cls, in_jwt: str) -> str:
        decoded = decode_access_token(in_jwt, verify_signature=False)
        if decoded.get("principal", None) is None or not isinstance(
            decoded.get("principal", None), list
        ):
            raise ValueError(
                "decoded jwt must have principal and it must be a list of strings, "
                f"jwt has the following keys: {decoded.keys()}"
            )
        elif not all(isinstance(elem, str) for elem in decoded.get("principal")):
            raise ValueError("jwt principal parameter must be a list of strings")

        if decoded.get("action", None) is None or not isinstance(
            decoded.get("action", None), list
        ):
            raise ValueError(
                "decoded jwt must have action and it must be a list of strings, "
                f"jwt has the following keys: {decoded.keys()}"
            )
        elif not all(isinstance(elem, str) for elem in decoded.get("action")):
            raise ValueError("jwt action parameter must be a list of strings")
        if decoded.get("resources", None) is None or not isinstance(
            decoded.get("resources", None), list
        ):
            raise ValueError(
                "decoded jwt must have resources parameter and it must be a list of strings,"
                f" jwt has the following keys: {decoded.keys()}"
            )
        elif not all(isinstance(elem, str) for elem in decoded.get("resources")):
            raise ValueError("jwt resources parameter must be a list of strings")
        if decoded.get("resource_data", None) is None or not isinstance(
            decoded.get("resource_data", None), list
        ):
            raise ValueError(
                "jwt must have resource_data parameter and it must be a list of strings"
            )
        elif not all(isinstance(elem, str) for elem in decoded.get("resource_data")):
            raise ValueError("jwt resource_data parameter must be a list of strings")
        if decoded.get("iss") is None:
            raise ValueError(
                "iss parameter must be present!"
                f" jwt has the following keys: {decoded.keys()}"
            )
        if decoded.get("sub") is None:
            raise ValueError(
                "sub parameter must be present!"
                f" jwt has the following keys: {decoded.keys()}"
            )
        return in_jwt


class CheckAuth(AccessRequest):
    pass


class AuthBody(BaseModel):
    pass
