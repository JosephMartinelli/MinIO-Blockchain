from abc import ABC
from blockchain.blockchain import BlockChain
from typing import Callable

"""
Much of the theory behind the implementation and design choices has been taken by the following paper: https://nvlpubs.nist.gov/nistpubs/ir/2022/NIST.IR.8403.pdf
"""


class ACNode(ABC):
    peers: set[str]


class LightNode(ACNode):
    """a node that does not store or maintain a copy of the
    blockchain. Lightweight nodes must pass their transactions to full nodes."""

    def pass_transactions(self):
        pass


class PublishingNode(ACNode):
    """a node that stores the entire blockchain and ensures that
    transactions are valid, it also publishes new blocks"""

    contracts: list[Callable[..., bool]]
    blockchain: BlockChain

    def are_transactions_valid(self):
        pass

    def consensus(self):
        pass

    def publish_block(self):
        pass
