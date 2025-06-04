from datetime import datetime
from abc import ABC
import hashlib
import json


class Block(ABC):
    def __init__(
        self,
        index: int,
        timestamp: datetime | str,
        previous_hash: str,
        proof: int = 0,
    ):
        self.index = index
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
