from pydantic import ConfigDict, BaseModel
from typing import Literal, Dict
from abc import ABC


class Condition(BaseModel):
    pass


class ACPolicy(ABC):
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
    principal: str = ""


class ACResourcePolicy(BaseModel, ACPolicy):
    model_config = ConfigDict(extra="forbid")
    id: str
    action: Literal[
        "add", "remove", "update"
    ]  # This is needed for the policy delta operation
    statements: Dict[str, ACResourceStatement] = {}


class ACIdentityPolicy(BaseModel, ACPolicy):
    model_config = ConfigDict(extra="forbid")
    id: str
    action: Literal["add", "remove", "update"]
    statements: Dict[str, ACIdentityStatement] = {}
