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
        ac_headers: dict[str, pd.DataFrame] = None,
    ):
        super().__init__(index, timestamp, previous_hash, proof)
        # Here comes the block structure declaration
        self.ac_headers = {
            "policy_header": pd.DataFrame(
                columns=[
                    "requester_id",
                    "requester_group",
                    "action",
                    "resource",
                    "allowed",
                ]
            ),  # This list will log the policy decisions carried by the PDC
            "contract_header": pd.DataFrame(
                columns=[
                    "timestamp",
                    "contract_name",
                    "contract_address",
                    "contract_description",
                    "contract_bytecode",
                ]
            ),  # This list will log all the contract addresses used by the MAC
            "events": pd.DataFrame(
                columns=[
                    "timestamp",
                    "requester_id",
                    "requester_pk",
                    "transaction_type",
                ]
            ),  # This list will log all the transactions that are committed to the bc
            "identity": pd.DataFrame(
                columns=["timestamp", "ip", "pk", "role", "nonce"]
            ),
        }

        if ac_headers:
            self.check_ac_header(ac_headers)

    def check_ac_header(self, in_header: dict[str, pd.DataFrame]):
        """
        This function is responsible in assuring that the passed ac_headers are consistent with the schema
        defined in the __init()__ function
        :param in_header:
        :return:
        """
        for header, values in in_header.items():
            data = self.ac_headers.get(header, None)
            if data is None:
                raise KeyError(
                    f"This header is not allowed, allowed headers are: {self.ac_headers.keys()}"
                )
            if list(self.ac_headers[header]) == list(values):
                self.ac_headers[header] = values
            else:
                raise KeyError(
                    f"{header} must have the following schema {list(self.ac_headers[header])}"
                )

    def compute_hash(self) -> str:
        obj_dict = deepcopy(self.__dict__)
        str_header = ""
        for header in obj_dict["ac_headers"].values():
            str_header += header.to_json()
        # So that json_dumps then works
        del obj_dict["ac_headers"]
        return hashlib.sha256((json.dumps(obj_dict) + str_header).encode()).hexdigest()

    @property
    def get_headers(self) -> dict[str, pd.DataFrame]:
        return self.ac_headers

    @property
    def get_headers_keys(self) -> list:
        to_return = []
        for header in self.ac_headers.values():
            to_return += list(header)
        return to_return

    def __eq__(self, other) -> bool:
        if isinstance(other, ACBlock):
            return other.__dict__ == self.__dict__
        return NotImplemented
