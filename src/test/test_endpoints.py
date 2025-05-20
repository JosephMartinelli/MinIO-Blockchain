import os
import json
import requests
from copy import deepcopy

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


def test_register_node():
    response = requests.get(url=f"{server}:{port}/register-node")
    assert response.status_code == 200, print(response.status_code, response.content)
    data = response.json()
    assert data["chain"]
    assert len(data["chain"]) > 0


# TODO: Implement this
def test_mine_all_good():
    pass
