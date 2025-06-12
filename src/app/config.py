"""
This file will contain all the settings of the application that will be validated by Pydantic.
"""

from enum import StrEnum
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import os


class NodeRole(StrEnum):
    PUBLISHER = "publisher"
    LIGHT = "light"


class Settings(BaseSettings):
    node_role: str
    port: int = Field(ge=8000, lt=9000)
    chain_difficulty: int = Field(lt=10)
    peers: list[str] | str = None

    @field_validator("node_role")
    def check_role_is_valid(cls, v):
        roles = set(role.value for role in NodeRole)
        if v in roles:
            return v
        raise ValueError(f"This role is not valid! Allowed roles are: {roles}")

    @field_validator("peers", mode="after")
    def make_peer_list(cls, v):
        if v:
            return v.replace('"', "").split(sep=",")
        else:
            return v


settings = Settings(
    node_role=os.environ.get("NODE_ROLE", "light"),
    port=os.environ.get("PORT", 8000),
    chain_difficulty=os.environ.get("CHAIN_DIFFICULTY", 3),
    peers=os.environ.get("PEERS", ""),
)
