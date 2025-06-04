"""This module defines the structure of the transactional data in the BC"""

from pydantic import BaseModel, ConfigDict
from abc import ABC


# This is an abstract class that it is used by the blockchain abstract class definition
class Transaction(ABC):
    pass


class SimpleTransaction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: str | list[str] | list[int] | list[dict] | dict
    is_contract: bool = False
    contract_address: str = ""


class ACTransaction(BaseModel):
    pass
