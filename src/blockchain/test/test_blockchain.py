import datetime

from ..blockchain import BlockChain, Block
from ..smart_contract import SmartContract
from datetime import datetime

blockchain = BlockChain(difficulty=3)


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
    local_chain = BlockChain(difficulty=3)


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
