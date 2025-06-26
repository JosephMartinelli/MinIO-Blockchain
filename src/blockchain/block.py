from datetime import datetime
from abc import ABC, abstractmethod
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

    def compute_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True).encode()
        ).hexdigest()

    def __str__(self):
        return str(self.__dict__)

    @abstractmethod
    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "proof": self.proof,
        }
