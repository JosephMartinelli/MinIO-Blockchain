import json
import secrets

import jwt
import requests

from app.nodes.authorization import (
    extract_user_data,
    evaluate_identity_policies,
    evaluate_resource_policies,
)
from app.ac_validation import (
    ACResourcePolicy,
    ACIdentityPolicy,
    ACResourceStatement,
    ACIdentityStatement,
)
import pytest
from copy import deepcopy
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
import os

port = os.environ.get("port", 8000)
server = "http://" + os.environ.get("server", "localhost")
auth_port = os.environ.get("port", 8000)
auth_server = "http://" + os.environ.get("server", "localhost")

mock_resource_statements = {
    f"{i}": ACResourceStatement(
        version="A version",
        sid=f"{i}",
        effect="Allow",
        resource="A resource",
        principal=f"principal{i}",
    )
    for i in range(10)
}
mock_identity_statements = {
    f"{i}": ACIdentityStatement(
        version="A version", sid=f"{i}", effect="Allow", resource="A resource"
    )
    for i in range(10)
}


@pytest.fixture
def resource_statements():
    return deepcopy(mock_resource_statements)


@pytest.fixture
def identity_statements():
    return deepcopy(mock_identity_statements)


@pytest.fixture
def private_key():
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )


@pytest.fixture
def public_key(private_key):
    return private_key.public_key()


@pytest.fixture
def pk_hex(public_key) -> str:
    return public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).hex()


def sign_message(message: bytes, private_key: RSAPrivateKey) -> bytes:
    return private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )


@pytest.fixture
def jwt(private_key, public_key):
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
        url=f"{auth_server}:{auth_port}/auth", data=json.dumps(challenge_request)
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
    }
    response = requests.post(
        url=f"{auth_server}:{auth_port}/auth", data=json.dumps(payload)
    )
    assert response.status_code == 201
    assert response.json()
    return response.json()


def test_extract_user_data():
    mock_decoded_jwt = {
        "iss": "an issuer",
        "sub": "a sub",
        "principal": ["a principal"],
        "action": "an action",
        "resources": ["a resource"],
        "resource_data": ["a resource_data"],
    }
    principal, action, resource, resource_data = extract_user_data(mock_decoded_jwt)
    assert principal
    assert action
    assert resource
    assert resource_data
    assert mock_decoded_jwt.get("principal") is None
    assert mock_decoded_jwt.get("action") is None
    assert mock_decoded_jwt.get("resource") is None
    assert mock_decoded_jwt.get("resource_data") is None


def test_evaluate_identity_policies_explicit_deny():
    statements = {
        "A sid": ACIdentityStatement(
            sid="A sid",
            effect="Deny",
            action="s3:CreateBucket",
            resource="new-bucket",
            version="A version",
        )
    }
    identity_policies = {
        "policy_id": ACIdentityPolicy(
            id="policy_id", action="add", statements=statements
        )
    }

    result, allow = evaluate_identity_policies(
        identity_policies, {"action": "s3:CreateBucket", "resources": "new-bucket"}
    )
    assert not allow
    assert result == "Explicit Deny"


# TODO: Finish these tests
