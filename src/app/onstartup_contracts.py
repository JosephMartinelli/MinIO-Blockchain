"""
This module contain functions that are called by admin nodes on during startup. It will insert into their genesis block
a series of smart contracts that the blockchain will use to determine if an user can have access to a given bucket
"""

import datetime
from blockchain.ac_block import ACBlock
import pandas as pd
import importlib.util
import sys
import os
from blockchain.smart_contract import SmartContract


def load_contracts() -> pd.DataFrame:
    """
    This function loads all the contracts defined in this module and returns a contract header's dataframe
    :return:
    """
    from inspect import getmembers, isfunction

    # Fetching all the functions in this module
    spec = importlib.util.spec_from_file_location(
        os.path.dirname(os.path.abspath(__file__)), "app/onstartup_contracts.py"
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
    return pd.DataFrame(contract_data)


# Here is a list of function that will be embedded in the blockchain
def MAC(transactions: dict, block: ACBlock):
    ppc_log = block.find_contract("PPC_log")
    for tr in transactions:
        if tr["transaction_type"] == "REQUEST_CHALLENGE":
            gen_nonce = block.find_contract("PPC_challenge_message")
            nonce = gen_nonce(block)
        elif tr["transaction_type"] == "ADD_CONTRACT":
            pass
        elif tr["transaction_type"] == "AUTHORIZATION":
            pass
        ppc_log(tr, block)


def PPC_log(request: dict, block: ACBlock) -> None:
    """
    This smart contract records requests onto the events header, tracking who requested what
    :return:
    """
    import datetime
    import pandas as pd

    to_log = pd.Series(
        {
            "timestamp": datetime.datetime.now(),
            "requester_id": request["requester_id"],
            "requester_pk": request["requester_pk"],
            "transaction_type": request["transaction_type"],
        }
    )
    block.ac_headers["events"] = pd.concat(
        [block.ac_headers["events"], to_log.to_frame().T], ignore_index=True
    )


def PPC_challenge_message(block: ACBlock) -> str:
    """

    :param block:
    :return:
    """


def PPC_attach_policy():
    pass


def PPC_detach_policy():
    pass
