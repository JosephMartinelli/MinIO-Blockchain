from .block import Block
from datetime import datetime
from .transaction import ACTransaction


class ACBlock(Block):
    def __init__(
        self,
        index: int,
        timestamp: datetime | str,
        previous_hash: str,
        proof: int = 0,
        transactions: list[ACTransaction] = None,
    ):
        super().__init__(index, timestamp, previous_hash, proof)
        # Here comes the block structure declaration
        self.policy_header: list = (
            []
        )  # This list will log the policy decisions carried by the PDC
        self.contract_header: list = (
            []
        )  # This list will log all the contract addresses used by the MAC
        self.events: list = []  # This list will log all the blockchain activity

    def __eq__(self, other) -> bool:
        if isinstance(other, ACBlock):
            return other.__dict__ == self.__dict__
        return NotImplemented
