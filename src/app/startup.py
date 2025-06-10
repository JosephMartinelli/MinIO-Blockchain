"""
This module contain functions that are called by admin nodes on during startup. It will insert into their genesis block
a series of smart contracts that the blockchain will use to determine if an user can have access to a given bucket
"""

import hashlib

import pandas as pd


def MAC(data: dict, context: list[pd.DataFrame]):
    print(data, context)


# Here is a list of function that will be embedded in the blockchain
def generate_nonce_and_log(user_auth: str, permissions: str) -> bool:
    pass


def fetch_permissions(user_data) -> str:
    pass


def populate_local_blockchain():
    pass


def create_contract_address(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
