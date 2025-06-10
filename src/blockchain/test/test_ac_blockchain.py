import pytest

from ..ac_blockchain import ACBlockchain
from ..ac_block import ACBlock
from ..errors import ContractNotFound
import pandas as pd
from copy import deepcopy
from pydantic import ValidationError
from datetime import date

blockchain = ACBlockchain(difficulty=3)
transaction = {
    "contract_address": "",
    "data": [""],
    "timestamp": "",
    "requester_id": "",
    "requester_pk": "",
    "transaction_type": "",
}


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
    genesis = ACBlock(
        index=50,
        timestamp="10",
        previous_hash="100",
    )
    local_chain = ACBlockchain(difficulty=3, genesis_block=genesis)
    assert len(local_chain.chain) == 1
    assert local_chain.chain[-1] == genesis
    assert local_chain.chain[-1].proof != 0


def test_digest_proof_and_no_dataframes():
    genesis = ACBlock(index=0, timestamp="10", previous_hash="100", proof=100)
    assert ACBlockchain.digest_proof_and_transactions(
        1, genesis.proof, genesis.index, genesis.get_headers
    )


def test_proof_of_work_no_dataframes():
    block = ACBlock(
        index=50,
        timestamp="10",
        previous_hash="100",
    )
    blockchain.proof_of_work(block)
    assert block.proof != 0


def test_digest_proof_with_dataframes():
    policy_header = pd.DataFrame(
        {
            "requester_id": ["1", "100", "1000"],
            "requester_group": ["user", "user", "user"],
            "action": ["s3:getBucket", "s3:getBucket", "s3:getBucket"],
            "resource": ["test", "test", "test"],
            "allowed": [False, False, False],
        }
    )
    block = ACBlock(
        index=50, timestamp="10", previous_hash="100", policy_heder=policy_header
    )
    assert ACBlockchain.digest_proof_and_transactions(
        1, block.proof, block.proof, block.get_headers
    )


def test_mine_invalid_transactions():
    global blockchain, transaction
    local_tr = deepcopy(transaction)
    local_tr["transaction_type"] = "10"
    with pytest.raises(ValidationError):
        blockchain.add_new_transaction([local_tr])


def test_mine_no_mac():
    global blockchain, transaction
    local_tr = deepcopy(transaction)
    local_tr["transaction_type"] = "ADD_CONTRACT"
    local_tr["timestamp"] = date.today()
    blockchain.add_new_transaction([local_tr])
    for block in blockchain.chain:
        print(block)
    with pytest.raises(ContractNotFound):
        blockchain.mine()


def test_mine_transaction():
    pass
