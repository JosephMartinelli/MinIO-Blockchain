import datetime
from copy import deepcopy

from ..ac_block import ACBlock
from ..ac_transaction import ACPolicy, Statement


def test_compute_hash_no_data():
    block = ACBlock(index=0, timestamp=datetime.datetime.now(), previous_hash="0")
    assert block.compute_hash()


def test_compute_hash_policies():
    statements = {
        f"{i}": Statement(
            version="A version", sid=f"{i}", effect="Allow", resource="A resource"
        )
        for i in range(10)
    }
    policy = ACPolicy(statements=statements, id="0", action="add")
    block = ACBlock(
        index=0, timestamp=datetime.datetime.now(), previous_hash="0", policies=[policy]
    )
    assert block.compute_hash()


def test_eq_blocks():
    statements = {
        f"{i}": Statement(
            version="A version", sid=f"{i}", effect="Allow", resource="A resource"
        )
        for i in range(10)
    }
    timestamp = datetime.datetime.now()
    policy = ACPolicy(statements=statements, id="0", action="add")
    block = ACBlock(index=0, timestamp=timestamp, previous_hash="0", policies=[policy])
    block2 = deepcopy(block)
    assert block2 == block
    statements = {
        f"{i}": Statement(
            version="A version", sid=f"{i}", effect="Deny", resource="A resource"
        )
        for i in range(10)
    }
    policy = ACPolicy(statements=statements, id="0", action="add")
    assert block != ACBlock(
        index=0, timestamp=timestamp, previous_hash="0", policies=[policy]
    )
