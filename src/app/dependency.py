"""
This file contains global dependencies that are shared across all endpoints and  will be
 injected with FastAPI injection system.
"""

from blockchain.blockchain import BlockChain
from config import settings

blockchain = BlockChain(difficulty=settings.chain_difficulty)
peers = set()


def get_peers():
    return peers


def get_blockchain():
    return blockchain


def create_blockchain():
    return BlockChain(difficulty=settings.chain_difficulty)
