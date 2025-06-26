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
        policies: list[ACPolicy] | dict[str, ACPolicy],
        contract_header: pd.DataFrame | dict,
        events: pd.DataFrame | dict,
        identity: pd.DataFrame | dict,
    ):
        if isinstance(policies, list) and not policies:
            self.policies = {}
        elif isinstance(policies, dict):
            self.policies = policies
        else:
            self.policies = {policy.id: policy for policy in policies}

        self.contract_header: pd.DataFrame = (
            contract_header
            if isinstance(contract_header, pd.DataFrame)
            else pd.DataFrame(contract_header)
        )
        self.events: pd.DataFrame = (
            events if isinstance(events, pd.DataFrame) else pd.DataFrame(events)
        )
        self.identity: pd.DataFrame = (
            identity if isinstance(identity, pd.DataFrame) else pd.DataFrame(identity)
        )

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

    def to_dict(self) -> dict:
        return {
            "policies": {
                policy_key: policy_val.model_dump()
                for policy_key, policy_val in self.policies.items()
            },
            "contract_header": self.contract_header.to_dict(),
            "events": self.events.to_dict(),
            "identity": self.identity.to_dict(),
        }


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
        body: dict | ACBlockBody = None,
    ):
        super().__init__(index, timestamp, previous_hash, proof)
        if policies is None:
            policies = []
        if not body:
            self.body: ACBlockBody = ACBlockBody(
                policies, contract_header, events, identity
            )
        else:
            self.body = body if isinstance(body, ACBlockBody) else ACBlockBody(**body)

    def compute_hash(self) -> str:
        return hashlib.sha256(json.dumps(self.to_dict()).encode()).hexdigest()

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
            return other.to_dict() == self.to_dict()
        return NotImplemented

    def to_dict(self) -> dict:
        super_dict = super().to_dict()
        super_dict.update({"body": self.body.to_dict()})
        return super_dict
