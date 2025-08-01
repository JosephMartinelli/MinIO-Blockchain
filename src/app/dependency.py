"""
This file contains global dependencies that are shared across all endpoints and  will be
 injected with FastAPI injection system.
"""

from blockchain.ac_blockchain import ACBlockchain
from app.config import settings
import logging
from pathlib import Path

blockchain = ACBlockchain(difficulty=settings.chain_difficulty)

if not settings.peers:
    peers = set(settings.peers)
else:
    peers = set()

# assuming loglevel is bound to the string value obtained from the
# command line argument. Convert to upper case to allow the user to
# specify --log=DEBUG or --log=debug
logger = logging.getLogger("logger")
current_file = Path(__file__).resolve()
project_root = current_file.parent
log_file = project_root / "log" / "node.log"
# Clearing log file
open(log_file, "w+").close()
logging.basicConfig(
    filename=log_file,
    format="%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
)

# Local cache of the policies
policies_cache = {}

identity_policies_cache = {}


def get_identity_policies_cache():
    return identity_policies_cache


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
