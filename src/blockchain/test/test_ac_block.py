import time
from copy import deepcopy
import pytest

from ..ac_block import ACBlock
from ..ac_transaction import (
    ACResourcePolicy,
    ACResourceStatement,
    ACIdentityStatement,
    ACIdentityPolicy,
)


@pytest.fixture
def resource_statements():
    return {
        f"{i}": ACResourceStatement(
            version="A version",
            sid=f"{i}",
            effect="Allow",
            resource="A resource",
            principal="A principal",
        )
        for i in range(10)
    }


@pytest.fixture
def identity_statements():
    return {
        f"{i}": ACIdentityStatement(
            version="A version", sid=f"{i}", effect="Allow", resource="A resource"
        )
        for i in range(10)
    }


def test_compute_hash_no_data():
    block = ACBlock(index=0, timestamp=time.time(), previous_hash="0")
    assert block.compute_hash()


def test_compute_hash_policies(resource_statements):
    policy = ACResourcePolicy(statements=resource_statements, id="0", action="add")
    block = ACBlock(
        index=0,
        timestamp=time.time(),
        previous_hash="0",
        resource_policies=[policy],
    )
    assert block.compute_hash()


def test_compute_hash_identities(identity_statements):
    policy = {
        "principal_id": {
            "policy_id": ACIdentityPolicy(
                statements=identity_statements, id="0", action="add"
            )
        }
    }
    block = ACBlock(
        index=0,
        timestamp=time.time(),
        previous_hash="0",
        identity_policies=policy,
    )
    assert block.compute_hash()


def test_compute_hash_both(identity_statements, resource_statements):
    policy = {
        "principal_id": {
            "policy_id": ACIdentityPolicy(
                statements=identity_statements, id="0", action="add"
            )
        }
    }
    resource = ACResourcePolicy(statements=resource_statements, id="0", action="add")
    block = ACBlock(
        index=0,
        timestamp=time.time(),
        previous_hash="0",
        identity_policies=policy,
        resource_policies=[resource],
    )
    assert block.compute_hash()


def test_eq_blocks(resource_statements, identity_statements):
    policy = {
        "principal_id": {
            "policy_id": ACIdentityPolicy(
                statements=identity_statements, id="0", action="add"
            )
        }
    }
    resource = ACResourcePolicy(statements=resource_statements, id="0", action="add")
    timestamp = time.time()
    block = ACBlock(
        index=0,
        timestamp=timestamp,
        previous_hash="0",
        resource_policies=[resource],
        identity_policies=policy,
    )
    block2 = deepcopy(block)
    assert block2 == block
    resource = {
        f"{i}": ACResourceStatement(
            version="A version",
            sid=f"{i}",
            effect="Deny",
            resource="A resource",
            principal="A different principal",
        )
        for i in range(10)
    }
    identity = {
        f"{i}": ACIdentityStatement(
            version="A version", sid=f"{i}", effect="Deny", resource="A resource"
        )
        for i in range(10)
    }

    policy = ACResourcePolicy(statements=resource, id="0", action="add")
    identity_pol = {
        "principal_id": {
            "a different principal id": ACIdentityPolicy(
                statements=identity, id="0", action="add"
            )
        }
    }
    assert block != ACBlock(
        index=0,
        timestamp=timestamp,
        previous_hash="0",
        resource_policies=[policy],
        identity_policies=identity_pol,
    )
