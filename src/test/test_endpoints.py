import os
import json
import requests
from copy import deepcopy

port = os.environ.get("port", 8000)
server = "http://" + os.environ.get("server", "localhost")

test_transaction = {"transactions": [], "is_contract": "", "contract_address": ""}


def test_get_chain():
    response = requests.get(url=f"{server}:{port}/")
    assert response.status_code == 200, print(response.status_code, response.content)
    data = response.json()
    assert len(data) != 0, print(data)


def test_register_transactions_bad_tr_field():
    transactions = deepcopy(test_transaction)
    transactions["transactions"] = "bed_elem"
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
    transactions["transactions"] = [["Hello, this is test data!"]]
    del transactions["is_contract"]
    del transactions["contract_address"]
    response = requests.post(
        url=f"{server}:{port}/register-transactions", data=json.dumps(transactions)
    )
    assert response.status_code == 200, print(response.status_code, response.content)


def test_mine_transaction():
    pass
