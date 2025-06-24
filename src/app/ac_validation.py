from pydantic import ConfigDict, BaseModel


class Action(BaseModel):
    pass


class Condition(BaseModel):
    pass


class Statement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    sid: str
    effect: str
    principal: str = None
    action: list[Action] = []
    resource: list[str] | str
    condition: list[Condition] = []


class ACPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    statements: list[Statement] = []
