from __future__ import annotations

import json
from typing import Callable
from .block import Block
import time
import pandas as pd
import hashlib

from .errors import ContractNotFound
from .smart_contract import SmartContract
from .ac_transaction import ACResourcePolicy, ACIdentityPolicy


class ACBlockBody:
    def __init__(
        self,
        resource_policies: list[ACResourcePolicy] | dict[str, ACResourcePolicy],
        contract_header: pd.DataFrame | dict,
        events: pd.DataFrame | dict,
        identity_policies: dict[str, dict[str, ACIdentityPolicy]],
    ):
        if isinstance(resource_policies, list) and not resource_policies:
            self.resource_policies = {}
        elif isinstance(resource_policies, dict):
            self.resource_policies = resource_policies
        else:
            self.resource_policies = {policy.id: policy for policy in resource_policies}

        self.contract_header: pd.DataFrame = (
            contract_header
            if isinstance(contract_header, pd.DataFrame)
            else pd.DataFrame(contract_header)
        )
        self.events: pd.DataFrame = (
            events if isinstance(events, pd.DataFrame) else pd.DataFrame(events)
        )

        self.identity_policies = identity_policies

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
                other.resource_policies == self.resource_policies
                and other.contract_header.equals(self.contract_header)
                and other.identity_policies == self.identity_policies
                and other.events.equals(self.events)
            )
        return NotImplemented

    def to_dict(self) -> dict:
        identities = {}
        for user_id, policies in self.identity_policies.items():
            identities[user_id] = {
                policy_key: policy_val.model_dump()
                for policy_key, policy_val in policies.items()
            }
        return {
            "resource_policies": {
                policy_key: policy_val.model_dump()
                for policy_key, policy_val in self.resource_policies.items()
            },
            "contract_header": self.contract_header.to_dict(),
            "events": self.events.to_dict(),
            "identity_policies": identities,
        }


class ACBlock(Block):
    def __init__(
        self,
        index: int,
        timestamp: time | str,
        previous_hash: str,
        proof: int = 0,
        resource_policies: list[ACResourcePolicy] | None = None,
        identity_policies: dict[str, dict[str, ACIdentityPolicy]] | None = None,
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
        body: dict | ACBlockBody = None,
    ):
        super().__init__(index, timestamp, previous_hash, proof)
        if resource_policies is None:
            resource_policies = []
        if identity_policies is None:
            identity_policies = {}
        if not body:
            self.body: ACBlockBody = ACBlockBody(
                resource_policies, contract_header, events, identity_policies
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
            self.body.identity_policies,
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
