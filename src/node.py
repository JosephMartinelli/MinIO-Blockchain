from abc import ABC
from blockchain.blockchain import BlockChain
from typing import Callable

"""
Much of the theory behind the implementation and design choices has been taken by the following paper: https://nvlpubs.nist.gov/nistpubs/ir/2022/NIST.IR.8403.pdf
"""


class ACNode(ABC):
    contracts: list[Callable[..., bool]]
    peers: set[str]

    def get_chain(self):
        pass


class LightNode(ACNode):
    def pass_transactions(self):
        pass


class FullNode(ACNode):
    blockchain: BlockChain

    def are_transactions_valid(self):
        pass

    def consensus(self):
        pass


class PublishingNode(FullNode):
    def publish_block(self):
        pass
