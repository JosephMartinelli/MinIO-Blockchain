import pytest

from ..simple_blockchain import SimpleBlockchain
from ..transaction import SimpleTransaction
from ..simple_block import SimpleBlock
from ..smart_contract import SmartContract
from ..errors import ContractNotFound, NoTransactionsFound, InvalidChain

from copy import deepcopy


blockchain = SimpleBlockchain(difficulty=3)


## Cleanup function
@pytest.fixture(autouse=True)
def cleanup():
    global blockchain
    yield
    blockchain.unconfirmed_transactions = []
    del blockchain.chain[1:]


def test_genesis_block_creation():
    assert len(blockchain.chain) > 0


def test_create_passed_genesis_block():
    genesis = SimpleBlock(
        index=50,
        timestamp="10",
        previous_hash="100",
        proof=100,
        transactions=[],
    )
    local_chain = SimpleBlockchain(difficulty=3, genesis_block=genesis)
    assert len(local_chain.chain) == 1
    assert local_chain.chain[-1] == genesis


def test_mine_no_committed_transactions():
    global blockchain
    with pytest.raises(NoTransactionsFound):
        blockchain.mine()


def test_mine_check_contract_address_creation():
    global blockchain

    def test_function(*args):
        pass

    blockchain.add_new_transaction(
        [
            {
                "data": SmartContract.encode(test_function),
                "is_contract": True,
                "contract_address": "",
            }
        ]
    )
    assert blockchain.mine()
    assert len(blockchain.chain) > 1
    assert blockchain.chain[-1].transactions[0]["contract_address"]


def test_smart_contract_exec():
    def hello(*args):
        for elem in args:
            pass

    encoded: str = SmartContract.encode(hello)
    blockchain.add_new_transaction(
        [{"data": encoded, "is_contract": True, "contract_address": ""}]
    )
    assert blockchain.mine()
    assert len(blockchain.chain) > 1
    address = blockchain.chain[-1].transactions[0]["contract_address"]
    blockchain.add_new_transaction(
        [{"data": "", "is_contract": False, "contract_address": address}]
    )
    assert blockchain.mine()
    assert len(blockchain.chain) > 2


def test_smart_contract_exec_data_modified():
    global blockchain

    def function_that_modifies_transaction_data(data: list):
        for i in range(len(data)):
            data[i] += 2

    encoded: str = SmartContract.encode(function_that_modifies_transaction_data)
    blockchain.add_new_transaction(
        [{"data": encoded, "is_contract": True, "contract_address": ""}]
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
    with pytest.raises(ContractNotFound):
        blockchain.mine()
    assert len(blockchain.chain) == 1


def test_get_contract_from_multiple_contract_in_transaction():
    global blockchain

    def hello_1():
        pass

    def hello_2():
        pass

    def hello_3():
        pass

    def hello_4():
        pass

    encoded = [
        SmartContract.encode(hello_1),
        SmartContract.encode(hello_2),
        SmartContract.encode(hello_3),
        SmartContract.encode(hello_4),
    ]
    for data in encoded:
        blockchain.add_new_transaction(
            [
                {
                    "data": data,
                    "is_contract": True,
                    "contract_address": "",
                }
            ]
        )
    assert blockchain.mine()
    print(blockchain.chain[1].transactions)
    assert len(blockchain.chain) > 1
    third_address = blockchain.chain[1].transactions[2]["contract_address"]
    assert third_address
    assert blockchain.find_contract(third_address) == encoded[2]


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


def test_check_is_chain_valid_bad_chain():
    global blockchain
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
    # Last test didn't clean up so that we can modify the data and test the method is_chain_valid()
    assert len(blockchain.chain) > 1
    last_bloc = blockchain.chain[-1]
    last_bloc.transactions[0]["data"] = "Not the original data"
    with pytest.raises(InvalidChain):
        blockchain.is_chain_valid()


def test_add_block_bad_index():
    global blockchain
    block = SimpleBlock(index=100, timestamp="10.20.02", previous_hash="0", proof=100)
    with pytest.raises(IndexError):
        blockchain.add_block(block)


def test_add_block_bad_previous_hash():
    global blockchain
    block = SimpleBlock(index=1, timestamp="10.20.02", previous_hash="10000", proof=100)
    with pytest.raises(InvalidChain):
        blockchain.add_block(block)


def test_add_block_inconsistent_hash():
    global blockchain
    block = SimpleBlock(index=1, timestamp="10.20.02", previous_hash="0", proof=0)
    with pytest.raises(InvalidChain):
        blockchain.add_block(block)


def test_add_block_all_good():
    global blockchain
    # Get last block hash (which is the genesis block)
    genesis = blockchain.get_last_bloc
    block = SimpleBlock(
        index=1, timestamp="10.20.02", previous_hash=genesis.compute_hash(), proof=0
    )
    blockchain.proof_of_work(block)
    assert blockchain.add_block(block)


def test_create_blockchain_from_request_no_transactions():
    global blockchain
    for i in range(1, 6):
        block = SimpleBlock(
            index=i,
            timestamp="0",
            previous_hash=blockchain.get_last_bloc.compute_hash(),
            proof=0,
        )
        blockchain.proof_of_work(block)
        assert blockchain.add_block(block)
    # Convert it to list of dict
    blockchain_str = [x.__dict__ for x in blockchain.chain]
    # Now we pass it to the function so that we can test it
    blockchain.create_blockchain_from_request(blockchain_str)


def test_create_blockchain_from_request_with_transactions():
    global blockchain
    for i in range(1, 6):
        tr_list = []
        for j in range(10):
            tr_list.append(
                SimpleTransaction(
                    is_contract=False, contract_address="0", data=f"{i}{j}"
                )
            )
        block = SimpleBlock(
            index=i,
            timestamp="0",
            previous_hash=blockchain.get_last_bloc.compute_hash(),
            proof=0,
            transactions=tr_list,
        )
        blockchain.proof_of_work(block)
        assert blockchain.add_block(block)
    # Convert it to list of dict
    blockchain_str = [x.__dict__ for x in blockchain.chain]
    # Now we pass it to the function so that we can test it
    blockchain.create_blockchain_from_request(blockchain_str)


def test_create_blockchain_from_request_has_chain_changed():
    local_chain = SimpleBlockchain(difficulty=3)
    for i in range(1, 6):
        tr_list = []
        for j in range(10):
            tr_list.append(
                SimpleTransaction(
                    is_contract=False, contract_address="0", data=f"{i}{j}"
                )
            )
        block = SimpleBlock(
            index=i,
            timestamp="0",
            previous_hash=local_chain.get_last_bloc.compute_hash(),
            proof=0,
            transactions=tr_list,
        )
        local_chain.proof_of_work(block)
        assert local_chain.add_block(block)

    global blockchain
    for i in range(1, 6):
        tr_list = []
        for j in range(10):
            tr_list.append(
                SimpleTransaction(
                    is_contract=False, contract_address="0", data=f"{i}{j}"
                )
            )
        block = SimpleBlock(
            index=i,
            timestamp="0",
            previous_hash=blockchain.get_last_bloc.compute_hash(),
            proof=0,
            transactions=tr_list,
        )
        blockchain.proof_of_work(block)
        assert blockchain.add_block(block)

    # Convert it to list of dict
    blockchain_str = deepcopy([x.__dict__ for x in blockchain.chain])
    # Now we pass it to the function so that we can test it
    assert local_chain.create_blockchain_from_request(blockchain_str)
    for x, y in zip(local_chain.chain, blockchain.chain):
        assert x == y
