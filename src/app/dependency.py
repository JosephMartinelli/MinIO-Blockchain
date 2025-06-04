"""
This file contains global dependencies that are shared across all endpoints and  will be
 injected with FastAPI injection system.
"""

from blockchain.ac_blockchain import ACBlockchain
from .config import settings

blockchain = ACBlockchain(difficulty=settings.chain_difficulty)

if not settings.peers:
    peers = set(settings.peers)
else:
    peers = set()


def get_peers():
    return peers


def get_blockchain() -> ACBlockchain:
    return blockchain


def create_blockchain():
    return ACBlockchain(difficulty=settings.chain_difficulty)
