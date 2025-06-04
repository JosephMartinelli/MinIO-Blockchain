from .block import Block
from datetime import datetime
from .transaction import SimpleTransaction


class SimpleBlock(Block):
    def __init__(
        self,
        index: int,
        timestamp: datetime | str,
        previous_hash: str,
        proof: int = 0,
        transactions: list[SimpleTransaction] = None,
    ):
        super().__init__(index, timestamp, previous_hash, proof)
        # Transactional data is validated against a Transaction Model defined in transaction.py
        if transactions:
            self.transactions = [
                item.model_dump() for item in transactions
            ]  # This is done so that we have validated dicts
        else:
            self.transactions: list[dict] = []

    def __eq__(self, other) -> bool:
        if isinstance(other, SimpleBlock):
            return other.__dict__ == self.__dict__
        return NotImplemented
