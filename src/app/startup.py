"""
This module contain functions that are called by admin nodes on during startup. It will insert into their genesis block
a series of smart contracts that the blockchain will use to determine if an user can have access to a given bucket
"""


# Here is a list of function that will be embedded in the blockchain
def grant_access(user_data: str, permissions: str) -> bool:
    pass


def fetch_permissions(user_data) -> str:
    pass


def populate_local_blockchain():
    pass
