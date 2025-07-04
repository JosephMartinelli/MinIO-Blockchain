import json
from time import sleep

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization


import requests
import os
import pytest
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

port = os.environ.get("port", 8000)
server = "http://" + os.environ.get("server", "localhost")


def sign_message(message: bytes, private_key: RSAPrivateKey) -> bytes:
    return private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )


@pytest.fixture
def private_key():
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )


@pytest.fixture
def public_key(private_key):
    return private_key.public_key()


def test_challenge_request(private_key, public_key):
    challenge_request = {
        "client_pk": public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        ).hex(),
        "client_id": "An id",
        "client_name": "A name",
    }
    response = requests.post(
        url=f"{server}:{port}/authentication", data=json.dumps(challenge_request)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nonce"]
    assert data["domain"]
    assert data["expire"]


def test_no_challenge_issued(private_key, public_key):
    challenge_request = {
        "message": {
            "nonce": "not a valid nonce",
            "domain": "A domain",
            "expire": 120391203129038,
        },
        "client_pk": public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        ).hex(),
        "signature": "An invalid signature",
    }
    response = requests.post(
        url=f"{server}:{port}/authentication", data=json.dumps(challenge_request)
    )
    assert response.status_code == 403, print(response.content)
    assert response.json() == "No challenge has been issued for this client!"


# For this test to work we need to set a very low nonce expiration (like 10 seconds)
def test_expired_nonce(private_key, public_key):
    encoded_pk = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).hex()
    challenge_request = {
        "client_pk": encoded_pk,
        "client_id": "An id",
        "client_name": "A name",
    }
    response = requests.post(
        url=f"{server}:{port}/authentication", data=json.dumps(challenge_request)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nonce"]
    assert data["domain"]
    assert data["expire"]
    sleep(7)
    signature = sign_message(response.content, private_key)
    payload = {
        "message": data,
        "signature": signature.hex(),
        "client_pk": encoded_pk,
    }
    response = requests.post(
        url=f"{server}:{port}/authentication", data=json.dumps(payload)
    )
    assert response.status_code == 403, print(response.content)
    assert response.json() == "Invalid or expired nonce!"


def test_invalid_signature(private_key, public_key):
    encoded_pk = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).hex()
    challenge_request = {
        "client_pk": encoded_pk,
        "client_id": "An id",
        "client_name": "A name",
    }
    response = requests.post(
        url=f"{server}:{port}/authentication", data=json.dumps(challenge_request)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nonce"]
    assert data["domain"]
    assert data["expire"]
    payload = {
        "message": data,
        "signature": "Not a valid signature",
        "client_pk": encoded_pk,
    }
    response = requests.post(
        url=f"{server}:{port}/authentication", data=json.dumps(payload)
    )
    assert response.status_code == 400, print(response.content)
    assert response.json() == "Signature must be passed as a valid hex string"


def test_obtain_jwt_all_good(private_key, public_key):
    encoded_pk = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).hex()
    challenge_request = {
        "client_pk": encoded_pk,
        "client_id": "An id",
        "client_name": "A name",
    }
    response = requests.post(
        url=f"{server}:{port}/authentication", data=json.dumps(challenge_request)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nonce"]
    assert data["domain"]
    assert data["expire"]
    signature = sign_message(response.content, private_key)
    payload = {
        "message": data,
        "signature": signature.hex(),
        "client_pk": encoded_pk,
        "client_id": "an id",
        "principal": "A principal",
        "action": ["an action"],
        "resources": ["a resource"],
        "resource_data": ["a resource data"],
    }
    response = requests.post(
        url=f"{server}:{port}/authentication", data=json.dumps(payload)
    )
    assert response.status_code == 201, print(response.content)
    assert response.json()
    print("\n", response.json())


def test_check_auth(public_key, private_key):
    encoded_pk = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).hex()
    challenge_request = {
        "client_pk": encoded_pk,
        "client_id": "An id",
        "client_name": "A name",
    }
    response = requests.post(
        url=f"{server}:{port}/authentication", data=json.dumps(challenge_request)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nonce"]
    assert data["domain"]
    assert data["expire"]
    signature = sign_message(response.content, private_key)
    payload = {
        "message": data,
        "signature": signature.hex(),
        "client_id": "an id",
        "client_pk": encoded_pk,
        "principal": "A principal",
        "action": ["an action"],
        "resources": ["a resource"],
        "resource_data": ["a resource data"],
    }
    response = requests.post(
        url=f"{server}:{port}/authentication", data=json.dumps(payload)
    )
    assert response.status_code == 201, print(response.content)
    assert response.json()
    print("\n", response.json())
    response = requests.post(
        url=f"{server}:{port}/check-auth", data=json.dumps({"jwt": response.json()})
    )
    assert response.status_code == 200
    assert response.json()
    print("\n", response.json())
