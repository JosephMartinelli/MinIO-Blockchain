import json

from .block import Block
from copy import deepcopy
from datetime import datetime
import pandas as pd
import hashlib


class ACBlock(Block):
    def __init__(
        self,
        index: int,
        timestamp: datetime | str,
        previous_hash: str,
        proof: int = 0,
        policy_heder: pd.DataFrame = None,
        contract_header: pd.DataFrame = None,
        events: pd.DataFrame = None,
    ):
        super().__init__(index, timestamp, previous_hash, proof)
        # Here comes the block structure declaration
        self.policy_header: pd.DataFrame = pd.DataFrame(
            columns=["requester_id", "requester_group", "action", "resource", "allowed"]
        )  # This list will log the policy decisions carried by the PDC
        if policy_heder is not None:
            if list(policy_heder) == list(self.policy_header):
                self.policy_header = policy_heder
            else:
                raise KeyError(
                    f"Policy header must have the following schema {self.policy_header.schema}"
                )
        self.contract_header: pd.DataFrame = pd.DataFrame(
            columns=[
                "timestamp",
                "contract_name",
                "contract_address",
                "contract_description",
                "contract_bytecode",
            ]
        )  # This list will log all the contract addresses used by the MAC
        if contract_header is not None:
            if list(contract_header) == list(self.contract_header):
                self.contract_header = contract_header
            else:
                raise KeyError(
                    f"Contract header must have the following schema {self.contract_header.schema}"
                )
        self.events: pd.DataFrame = pd.DataFrame(
            columns=["timestamp", "requester_id", "requester_pk", "transaction_type"]
        )  # This list will log all the transactions that are committed to the bc
        if events is not None:
            if list(events) == list(self.events):
                self.events = events
            else:
                raise KeyError(
                    f"Events header must have the following schema {self.events.schema}"
                )

    def compute_hash(self) -> str:
        obj_dict = deepcopy(self.__dict__)
        del obj_dict["policy_header"]
        del obj_dict["contract_header"]
        del obj_dict["events"]
        return hashlib.sha256(
            (
                json.dumps(obj_dict)
                + self.policy_header.to_json()
                + self.contract_header.to_json()
                + self.events.to_json()
            ).encode()
        ).hexdigest()

    @property
    def get_headers(self) -> list[pd.DataFrame]:
        return [self.policy_header, self.contract_header, self.events]

    @property
    def get_headers_keys(self) -> tuple[list, list, list]:
        return (
            list(self.policy_header),
            list(self.contract_header),
            list(self.events),
        )

    def __eq__(self, other) -> bool:
        if isinstance(other, ACBlock):
            return other.__dict__ == self.__dict__
        return NotImplemented
