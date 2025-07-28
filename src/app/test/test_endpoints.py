import os
import json
import requests
from copy import deepcopy
from blockchain.ac_blockchain import ACBlockchain, ACBlock
from blockchain.smart_contract import SmartContract
from blockchain.ac_transaction import ACPolicy, Statement
from app.dependency import get_policies_cache, log_file
import pandas as pd
import pytest
import random
import datetime
from typing import Callable
from pathlib import Path


port = os.environ.get("port", 8000)
server = "http://" + os.environ.get("server", "localhost")

mock_statements = {
    f"{i}": Statement(
        version="A version", sid=f"{i}", effect="Allow", resource="A resource"
    )
    for i in range(10)
}

# TODO: Finish these tests


#
# mock_contract_header: pd.DataFrame = pd.DataFrame(
#     {
#         "timestamp": ["a timestamp" for i in range(10)],
#         "contract_name": ["a contract_name" for i in range(10)],
#         "contract_address": ["an address" for i in range(10)],
#         "contract_description": ["a description" for i in range(10)],
#         "contract_bytecode": ["b a bytecode str" for i in range(10)],
#     }
# )
#
# mock_events: pd.DataFrame = pd.DataFrame(
#     {
#         "timestamp": ["a timestamp" for i in range(10)],
#         "requester_id": ["a requester id" for i in range(10)],
#         "requester_pk": ["a requester pk" for i in range(10)],
#         "transaction_type": ["a type" for i in range(10)],
#     }
# )
#
# mock_identity: pd.DataFrame = pd.DataFrame(
#     data={
#         "timestamp": ["a timestamp" for i in range(10)],
#         "ip": ["an ip" for i in range(10)],
#         "pk": ["a pk" for i in range(10)],
#         "role": ["a role" for i in range(10)],
#         "nonce": ["a nonce" for i in range(10)],
#     }
# )
#
#
# @pytest.fixture
# def statements():
#     return deepcopy(mock_statements)
#
#
@pytest.fixture
def policy(statements):
    return ACPolicy(id="An id", action="add", statements=statements)


#
#
# @pytest.fixture
# def headers():
#     return (
#         deepcopy(mock_contract_header),
#         deepcopy(mock_events),
#         deepcopy(mock_identity),
#     )
#
#
# def random_headers(headers):
#     contract, events, identity = headers
#     return (
#         contract.sample(frac=0.5),
#         events.sample(frac=0.5),
#         identity.sample(frac=0.5),
#     )
#
#
def random_statements():
    random_sts = random.sample(list(deepcopy(mock_statements).values()), 5)
    return {random_st.sid: random_st for random_st in random_sts}


def random_policies() -> list[ACPolicy]:
    return [
        ACPolicy(id=str(i), action="add", statements=random_statements())
        for i in range(random.randint(1, 3))
    ]


#
#
# def random_policies_serialized():
#     policies: list[ACPolicy] = random_policies()
#     return json.dumps([policy.model_dump() for policy in policies])
#
#
# @pytest.fixture
# def chain_with_blocks(headers, policy) -> ACBlockchain:
#     chain = ACBlockchain(difficulty=2)
#     for i in range(10):
#         contract, events, identity = random_headers(headers)
#         block = ACBlock(
#             index=chain.get_last_bloc.index + 1,
#             timestamp=datetime.datetime.now(),
#             previous_hash=chain.get_last_bloc.compute_hash(),
#             policies=random_policies(),
#             contract_header=contract,
#             events=events,
#             identity=identity,
#         )
#         chain.proof_of_work(block)
#         chain.add_block(block)
#     return chain
#
#
# def append_to_contract_header(df: pd.DataFrame, func: Callable) -> pd.DataFrame:
#     to_append = pd.Series(
#         [
#             "a timestamp",
#             func.__name__,
#             SmartContract.create_address(SmartContract.encode(func)),
#             "a description",
#             SmartContract.encode(func),
#         ],
#         index=list(df),
#     )
#     return pd.concat([df, to_append.to_frame().T], ignore_index=True)
#


def test_get_chain():
    response = requests.get(url=f"{server}:{port}/")
    assert response.status_code == 200, print(response.status_code, response.content)
    data = response.json()
    assert data
    assert data["chain"]
    assert data["difficulty"]


def test_register_peer():
    response = requests.get(url=f"{server}:{port}/register-peer")
    assert response.status_code == 200, print(response.content)
    data = response.json()
    assert data
    assert data["chain"]
    assert data["difficulty"]


def test_mine_no_policies():
    response = requests.get(url=f"{server}:{port}/mine")
    assert response.status_code == 400


def test_add_policy():
    for policy in random_policies():
        response = requests.post(
            url=f"{server}:{port}/add-policy", data=policy.model_dump_json()
        )
        assert response.status_code == 200, print(response.content)


def test_add_policy_logger_has_logged(policy):
    response = requests.post(
        url=f"{server}:{port}/add-policy", data=policy.model_dump_json()
    )
    assert response.status_code == 200, print(response.content)
    # This checks if the log file is not empty
    assert os.stat(log_file).st_size != 0


def test_add_policy_trigger_gossip_logging_warning(policy):
    # First we register to the node
    response = requests.get(url=f"{server}:{port}/register-peer")
    assert response.status_code == 200, print(response.content)
    # Then we trigger the gossip protocol by adding a transaction
    response = requests.post(
        url=f"{server}:{port}/add-policy", data=policy.model_dump_json()
    )
    assert response.status_code == 200
    with open(log_file) as f:
        for line in f:
            pass
    last_line = line
    assert "WARNING" in last_line


def test_update_local_cache_no_policies():
    response = requests.get(url=f"{server}:{port}/update-cache")
    assert response.status_code == 200
    # Since no policies are mined the cache of the node should be empty
    assert not get_policies_cache()
