"""
This module contain functions that are called by admin nodes on during startup. It will insert into their genesis block
a series of smart contracts that the blockchain will use to determine if an user can have access to a given bucket
"""

import datetime
from app.config import settings
from blockchain.ac_block import ACBlock
from blockchain.ac_blockchain import ACBlockchain
import pandas as pd
import importlib.util
import sys
import os
from blockchain.smart_contract import SmartContract


def create_genesis_block_contracts():
    """
    This function creates a genesis block filled with all the smart contracts that are defined in this module.
    :return:
    """
    from inspect import getmembers, isfunction
    from app.dependency import set_global_chain

    # Fetching all the functions in this module
    spec = importlib.util.spec_from_file_location(
        os.path.dirname(os.path.abspath(__file__)), "app/startup.py"
    )
    foo = importlib.util.module_from_spec(spec)
    sys.modules["startup"] = foo
    spec.loader.exec_module(foo)
    cll_list = getmembers(foo, isfunction)
    contract_data = {
        "timestamp": [],
        "contract_name": [],
        "contract_address": [],
        "contract_description": [],
        "contract_bytecode": [],
    }
    for contract_name, contract_func in cll_list:
        if contract_name == "create_genesis_block_contracts":
            continue
        contract_data["timestamp"].append(datetime.datetime.now())
        contract_data["contract_name"].append(contract_name)
        contract_data["contract_description"].append(contract_func.__doc__)
        contract_data["contract_bytecode"].append(SmartContract.encode(contract_func))
        contract_data["contract_address"].append(
            SmartContract.create_address(SmartContract.encode(contract_func))
        )
    genesis = ACBlock(
        index=0,
        timestamp=datetime.datetime.now(),
        previous_hash="0",
        # TODO: Fix this
        contract_header=pd.DataFrame(contract_data),
    )
    set_global_chain(
        ACBlockchain(difficulty=settings.chain_difficulty, genesis_block=genesis)
    )


# Here is a list of function that will be embedded in the blockchain
def MAC(data: dict, block: ACBlock):
    pass


def PPC_log(user_auth: str, permissions: str) -> bool:
    pass


def PPC_generate_nonce() -> str:
    pass
