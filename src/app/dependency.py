"""
This file contains global dependencies that are shared across all endpoints and  will be
 injected with FastAPI injection system.
"""

from blockchain.ac_blockchain import ACBlockchain
from .config import settings
import logging


blockchain = ACBlockchain(difficulty=settings.chain_difficulty)

if not settings.peers:
    peers = set(settings.peers)
else:
    peers = set()

# assuming loglevel is bound to the string value obtained from the
# command line argument. Convert to upper case to allow the user to
# specify --log=DEBUG or --log=debug
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="app/log/node.log",
    filemode="w",
    level=logging.DEBUG,
    format="%%(asctime)s (levelname)s:%(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

# Local cache of the policies
policies_cache = {}


def get_policies_cache():
    return policies_cache


def get_logger():
    return logger


def get_peers():
    return peers


def get_blockchain() -> ACBlockchain:
    return blockchain


def set_global_chain(new_chain: ACBlockchain) -> None:
    global blockchain
    blockchain = new_chain


def create_blockchain():
    return ACBlockchain(difficulty=settings.chain_difficulty)
