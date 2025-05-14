"""This module defines the structure of the transactional data in the BC"""

from pydantic import BaseModel, ConfigDict


class Transaction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: str | list[str] | list[int]
    is_contract: bool = False
    contract_address: str = ""
