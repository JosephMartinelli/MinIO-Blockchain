import datetime

import pytest

from ..blockchain import BlockChain, Block
from ..smart_contract import SmartContract
from ..errors import ContractNotFound, NoTransactionsFound
from datetime import datetime
from copy import deepcopy

blockchain = BlockChain(difficulty=3)
tr = [{"data": [], "is_contract": False, "contract_address": ""}]


def test_genesis_block_creation():
    assert len(blockchain.chain) > 0


def test_create_passed_genesis_block():
    genesis = Block(
        index=50,
        timestamp=datetime.now(),
        previous_hash="100",
        proof=100,
        transactions=[],
    )
    local_chain = BlockChain(difficulty=3, genesis_block=genesis)
    assert len(local_chain.chain) == 1
    assert local_chain.chain[-1] == genesis


def test_mine_no_committed_transactions():
    global blockchain
    with pytest.raises(NoTransactionsFound) as error:
        blockchain.mine()


def test_mine_check_contract_address_creation():
    global blockchain, tr

    def test_function(*args):
        pass

    test_tr = deepcopy(tr)
    test_tr[0]["data"] = SmartContract.encode(test_function)
    blockchain.add_new_transaction(
        [{"data": test_tr, "is_contract": True, "contract_address": ""}]
    )
    assert blockchain.mine()
    assert len(blockchain.chain) > 1
    assert blockchain.chain[-1].transactions[0]["contract_address"]

    # Cleanup
    del blockchain.chain[1:]


def test_smart_contract_exec():
    def hello(*args):
        for elem in args:
            pass

    encoded: str = SmartContract.encode(hello)
    blockchain.add_new_transaction(
        [{"data": [encoded], "is_contract": True, "contract_address": ""}]
    )
    assert blockchain.mine()
    assert len(blockchain.chain) > 1
    address = blockchain.chain[-1].transactions[0]["contract_address"]
    blockchain.add_new_transaction(
        [{"data": [], "is_contract": False, "contract_address": address}]
    )
    assert blockchain.mine()
    assert len(blockchain.chain) > 2
    # Cleanup
    del blockchain.chain[1:]


def test_smart_contract_exec_data_modified():
    global blockchain

    def function_that_modifies_transaction_data(data: list):
        for i in range(len(data)):
            data[i] += 2

    encoded: str = SmartContract.encode(function_that_modifies_transaction_data)
    blockchain.add_new_transaction(
        [{"data": [encoded], "is_contract": True, "contract_address": ""}]
    )
    assert blockchain.mine()
    assert len(blockchain.chain) > 1
    address = blockchain.chain[-1].transactions[0]["contract_address"]
    blockchain.add_new_transaction(
        [{"data": [0] * 5, "is_contract": False, "contract_address": address}]
    )
    assert blockchain.mine()
    assert blockchain.chain[-1].transactions[0]["data"] == [2] * 5
    assert len(blockchain.chain) > 1

    # Cleanup
    del blockchain.chain[1:]


def test_mine_contract_not_found():
    global blockchain
    blockchain.add_new_transaction(
        [
            {
                "data": [0] * 5,
                "is_contract": False,
                "contract_address": "not a valid address",
            }
        ]
    )
    with pytest.raises(ContractNotFound) as error:
        blockchain.mine()
    assert len(blockchain.chain) == 1


def test_check_is_chain_valid_good_chain():
    global blockchain
    blockchain.unconfirmed_transactions = []
    for i in range(5):
        blockchain.add_new_transaction(
            [
                {
                    "data": f"test{i}",
                    "is_contract": False,
                    "contract_address": "",
                }
            ]
        )
        blockchain.mine()
    assert blockchain.is_chain_valid()
