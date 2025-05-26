import os
import json
import requests
from copy import deepcopy
from blockchain.blockchain import BlockChain, Block

port = os.environ.get("port", 8000)
server = "http://" + os.environ.get("server", "localhost")

test_transaction = {"data": [], "is_contract": "", "contract_address": ""}


def test_get_chain():
    response = requests.get(url=f"{server}:{port}/")
    assert response.status_code == 200, print(response.status_code, response.content)
    data = response.json()
    assert len(data) != 0, print(data)


def test_mine_no_transactions():
    response = requests.get(url=f"{server}:{port}/mine")
    assert response.status_code == 400


def test_register_transactions_bad_tr_field():
    transactions = deepcopy(test_transaction)
    transactions["data"] = 0.321
    response = requests.post(
        url=f"{server}:{port}/register-transactions", data=transactions
    )
    assert response.status_code == 422, print(response.status_code, response.content)


def test_register_transactions_bad_contract_field():
    transactions = deepcopy(test_transaction)
    transactions["is_contract"] = "bed_elem"
    response = requests.post(
        url=f"{server}:{port}/register-transactions", data=transactions
    )
    assert response.status_code == 422, print(response.status_code, response.content)


def test_register_transactions_bad_contract_address_field():
    transactions = deepcopy(test_transaction)
    transactions["contract_address"] = 0
    response = requests.post(
        url=f"{server}:{port}/register-transactions", data=transactions
    )
    assert response.status_code == 422, print(response.status_code, response.content)


def test_register_transaction_all_good():
    transactions = deepcopy(test_transaction)
    transactions["data"] = ["Hello, this is test data!"]
    payload = {"transactions": [transactions]}
    del transactions["is_contract"]
    del transactions["contract_address"]
    response = requests.post(
        url=f"{server}:{port}/register-transactions", data=json.dumps(payload)
    )
    assert response.status_code == 200, print(response.status_code, response.content)


def test_add_block_good_block():
    # First we fetch the blockchain
    response = requests.get(url=f"{server}:{port}/register-node")
    assert response.status_code == 200, print(response.status_code, response.content)
    chain_data: dict = response.json()
    assert chain_data
    local_chain = BlockChain(difficulty=chain_data["difficulty"])
    assert local_chain.create_blockchain_from_request(data=chain_data["chain"])
    # This is a block that should not be rejected
    block = Block(
        index=local_chain.get_last_bloc.index + 1,
        timestamp="0",  # Timestamp is irrelevant
        previous_hash=local_chain.get_last_bloc.compute_hash(),
    )
    local_chain.proof_of_work(block)
    response = requests.post(
        url=f"{server}:{port}/add-block", data=json.dumps(block.__dict__)
    )
    assert response.status_code == 201, print(response.status_code, response.content)


def test_add_block_invalid_index():
    # First we fetch the blockchain
    response = requests.get(url=f"{server}:{port}/register-node")
    assert response.status_code == 200, print(response.status_code, response.content)
    chain_data: dict = response.json()
    assert chain_data
    local_chain = BlockChain(difficulty=chain_data["difficulty"])
    assert local_chain.create_blockchain_from_request(data=chain_data["chain"])
    # This is a block that should not be rejected
    block = Block(
        index=10,
        timestamp="0",  # Timestamp is irrelevant
        previous_hash=local_chain.get_last_bloc.compute_hash(),
    )
    local_chain.proof_of_work(block)
    response = requests.post(
        url=f"{server}:{port}/add-block", data=json.dumps(block.__dict__)
    )
    assert response.status_code == 400, print(response.status_code, response.content)


def test_add_block_invalid_last_block_hash():
    # First we fetch the blockchain
    response = requests.get(url=f"{server}:{port}/register-node")
    assert response.status_code == 200, print(response.status_code, response.content)
    chain_data: dict = response.json()
    assert chain_data
    local_chain = BlockChain(difficulty=chain_data["difficulty"])
    assert local_chain.create_blockchain_from_request(data=chain_data["chain"])
    # This is a block that should not be rejected
    block = Block(
        index=local_chain.get_last_bloc.index + 1,
        timestamp="0",  # Timestamp is irrelevant
        previous_hash="10203019",
    )
    local_chain.proof_of_work(block)
    response = requests.post(
        url=f"{server}:{port}/add-block", data=json.dumps(block.__dict__)
    )
    assert response.status_code == 400, print(response.status_code, response.content)


def test_consensus():
    # First we register we the node so that it adds us to his peers
    response = requests.get(url=f"{server}:{port}/register-node")
    assert response.status_code == 200, print(response.status_code, response.content)
    data = response.json()
    assert data
    assert data["chain"]
    assert data["difficulty"]
    response = requests.get(url=f"{server}:{port}/consensus")
    assert response.status_code == 200
    data = response.json()
    assert not data["replaced"]


def test_mine_all_good():
    transactions = deepcopy(test_transaction)
    transactions["data"] = ["Hello, this is test data!"]
    payload = {"transactions": [transactions]}
    del transactions["is_contract"]
    del transactions["contract_address"]
    response = requests.post(
        url=f"{server}:{port}/register-transactions", data=json.dumps(payload)
    )
    assert response.status_code == 200, print(response.status_code, response.content)
    response = requests.get(url=f"{server}:{port}/mine")
    assert response.status_code == 200, print(response.status_code, response.content)
    assert response.json()


def test_register_node():
    response = requests.get(url=f"{server}:{port}/register-node")
    assert response.status_code == 200, print(response.status_code, response.content)
    data = response.json()
    assert data["chain"]
    assert len(data["chain"]) > 0
