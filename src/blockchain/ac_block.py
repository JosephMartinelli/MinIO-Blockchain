from __future__ import annotations

import json
from typing import Callable
from .block import Block
from datetime import datetime
import pandas as pd
import hashlib

from .errors import ContractNotFound
from .smart_contract import SmartContract
from .ac_transaction import ACPolicy


class ACBlockBody:
    def __init__(
        self,
        policies: list[ACPolicy],
        contract_header: pd.DataFrame,
        events: pd.DataFrame,
        identity: pd.DataFrame,
    ):
        if policies:
            self.policies: dict[str, ACPolicy] = {
                policy.id: policy for policy in policies
            }
        else:
            self.policies = {}
        self.contract_header: pd.DataFrame = contract_header
        self.events: pd.DataFrame = events
        self.identity: pd.DataFrame = identity

    def __repr__(self) -> str:
        to_return = {}
        for key, val in self.__dict__.items():
            if isinstance(val, pd.DataFrame):
                to_return.update({key: val.to_dict()})
            else:
                to_return.update({key: val})
        return str(to_return)

    @property
    def get_headers(self):
        return self.__dict__

    def __eq__(self, other) -> bool:
        if isinstance(other, ACBlockBody):
            return (
                other.policies == self.policies
                and other.contract_header.equals(self.contract_header)
                and other.identity.equals(self.identity)
                and other.events.equals(self.events)
            )
        return NotImplemented


class ACBlock(Block):
    def __init__(
        self,
        index: int,
        timestamp: datetime | str,
        previous_hash: str,
        policies: list[ACPolicy] | None = None,
        contract_header: pd.DataFrame = pd.DataFrame(
            columns=[
                "timestamp",
                "contract_name",
                "contract_address",
                "contract_description",
                "contract_bytecode",
            ]
        ),
        events: pd.DataFrame = pd.DataFrame(
            columns=[
                "timestamp",
                "requester_id",
                "requester_pk",
                "transaction_type",
            ]
        ),
        identity: pd.DataFrame = pd.DataFrame(
            columns=["timestamp", "ip", "pk", "role", "nonce"]
        ),
        proof: int = 0,
    ):
        super().__init__(index, timestamp, previous_hash, proof)
        self.body: ACBlockBody = ACBlockBody(
            policies, contract_header, events, identity
        )

    def compute_hash(self) -> str:
        return hashlib.sha256(json.dumps(str(self)).encode()).hexdigest()

    def find_contract(
        self, contract_name: str
    ) -> Callable[[dict, ACBlock], bool | str | tuple]:
        df: pd.DataFrame = self.body.contract_header
        to_return: pd.DataFrame = df.loc[df["contract_name"] == contract_name]
        if to_return.empty:
            raise ContractNotFound(
                f"No contract with name {contract_name} has been found"
            )
        else:
            return SmartContract.decode(to_return["contract_bytecode"].values[0])

    @property
    def get_headers(self) -> dict:
        return self.body.get_headers

    @property
    def get_headers_keys(self) -> list:
        return [
            list(self.body.contract_header),
            list(self.body.identity),
            list(self.body.events),
        ]

    def __eq__(self, other) -> bool:
        if isinstance(other, ACBlock):
            return other.__dict__ == self.__dict__
        return NotImplemented
