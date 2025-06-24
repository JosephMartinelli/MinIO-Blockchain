from pydantic import ConfigDict, BaseModel
from typing import Literal


class Condition(BaseModel):
    pass


class Statement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    sid: str
    effect: Literal["Allow", "Deny"]
    principal: str = None
    action: list[str] | str = []
    resource: list[str] | str
    condition: dict[str, Condition] = []


class ACPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    action: Literal["add", "remove", "update"]
    statements: dict[str, Statement] = {}
