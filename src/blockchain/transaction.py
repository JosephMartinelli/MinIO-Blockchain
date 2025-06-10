"""This module defines the structure of the transactional data in the BC"""

from pydantic import BaseModel, ConfigDict
from datetime import date
from abc import ABC
from typing import Literal


# This is an abstract class that it is used by the blockchain abstract class definition
class Transaction(ABC):
    contract_address: str = ""
    data: str | list[str] | list[int] | list[dict] | dict


class SimpleTransaction(BaseModel, Transaction):
    model_config = ConfigDict(extra="forbid")
    is_contract: bool = False


class ACTransaction(BaseModel, Transaction):
    timestamp: date
    requester_id: str
    requester_pk: str
    transaction_type: Literal["ADD_CONTRACT", "AUTHORIZATION", "AUTHENTICATION"]
