import datetime

import pytest

from ..ac_block import ACBlock
import pandas as pd


def test_invalid_policy_header():
    policy_header = pd.DataFrame(
        {
            "requester_id": ["1", "100", "1000"],
            "requester_group": ["user", "user", "user"],
            "action": ["s3:getBucket", "s3:getBucket", "s3:getBucket"],
            "resource": ["test", "test", "test"],
            "not_a_key": [False, False, False],
        }
    )
    ac_header = {"policy_header": policy_header}
    with pytest.raises(KeyError, match=r"\bmust have the following schema\w*"):
        block = ACBlock(
            index=0,
            timestamp=datetime.datetime.now(),
            previous_hash="0",
            ac_headers=ac_header,
        )


def test_header_is_not_allowed():
    unallowed = pd.DataFrame({"somehting": ["something"]})
    ac_header = {"not_an_allowed_name": unallowed}
    with pytest.raises(KeyError, match=r"\bThis header is not allowed\w*"):
        block = ACBlock(
            index=0,
            timestamp=datetime.datetime.now(),
            previous_hash="0",
            ac_headers=ac_header,
        )


def test_header_are_added():
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
        index=0,
        timestamp=datetime.datetime.now(),
        previous_hash="0",
        ac_headers={"policy_header": policy_header},
    )
    assert block.ac_headers["policy_header"].equals(policy_header)


def test_compute_hash():
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
        index=0,
        timestamp=datetime.datetime.now(),
        previous_hash="0",
        ac_headers={"policy_header": policy_header},
    )
    assert block.compute_hash()
