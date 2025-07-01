from pydantic import ConfigDict, BaseModel
from typing import Literal, Dict


class Condition(BaseModel):
    pass


class Statement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    sid: str
    effect: Literal["Allow", "Deny"]
    principal: str = ""
    action: list[str] | str = []
    resource: list[str] | str
    condition: Dict[str, Condition] = {}


class ACPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    action: Literal["add", "remove", "update"]
    statements: Dict[str, Statement] = {}
