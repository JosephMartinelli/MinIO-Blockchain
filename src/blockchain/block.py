import hashlib
import json
from datetime import datetime
from .transaction import Transaction


class Block:
    def __init__(
        self,
        index: int,
        timestamp: datetime | str,
        previous_hash: str,
        proof: int = 0,
        transactions: list[Transaction] = None,
    ):
        self.index = index
        if transactions:
            self.transactions = [
                item.model_dump() for item in transactions
            ]  # This is done so that we have validated dicts
        else:
            self.transactions: list[dict] = []
        if isinstance(timestamp, datetime):
            self.timestamp = timestamp.strftime("%d/%m/%y %H:%M:%S.%f")
        else:
            self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.proof = proof

    def compute_hash(self):
        return hashlib.sha256(
            json.dumps(self.__dict__, sort_keys=True).encode()
        ).hexdigest()

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other) -> bool:
        if isinstance(other, Block):
            return other.__dict__ == self.__dict__
        return False
