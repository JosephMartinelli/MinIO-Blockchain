import datetime
from copy import deepcopy

from ..ac_block import ACBlock
from ..ac_transaction import ACPolicy, Statement


def test_compute_hash_no_data():
    block = ACBlock(index=0, timestamp=datetime.datetime.now(), previous_hash="0")
    assert block.compute_hash()


def test_compute_hash_policies():
    statements = []
    for i in range(2):
        statements.append(
            Statement(
                version=f"{i}",
                sid=f"A sid{i}",
                effect="Allow",
                resource=f"A resource{i}",
            )
        )
    policy = ACPolicy(statements=statements, id="0", action="add")
    block = ACBlock(
        index=0, timestamp=datetime.datetime.now(), previous_hash="0", policies=[policy]
    )
    assert block.compute_hash()


def test_eq_blocks():
    statements = []
    for i in range(2):
        statements.append(
            Statement(
                version=f"{i}",
                sid=f"A sid{i}",
                effect="Allow",
                resource=f"A resource{i}",
            )
        )
    timestamp = datetime.datetime.now()
    policy = ACPolicy(statements=statements, id="0", action="add")
    block = ACBlock(index=0, timestamp=timestamp, previous_hash="0", policies=[policy])
    block2 = deepcopy(block)
    assert block2 == block
    statements = []
    for i in range(2):
        statements.append(
            Statement(
                version="Not equal",
                sid=f"A sid{i}",
                effect="Allow",
                resource=f"A resource{i}",
            )
        )
    policy = ACPolicy(statements=statements, id="0")
    assert block != ACBlock(
        index=0, timestamp=timestamp, previous_hash="0", policies=[policy]
    )
