import os
import json
import pytest
import requests
import xmltodict
import minio

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from minio import Minio

minio_host = os.environ.get("MINIO_HOSTNAME", "127.0.0.1")
minio_port = os.environ.get("MINIO_PORT", "9000")
auth_port = os.environ.get("port", 8000)
auth_server = "http://" + os.environ.get("server", "localhost")


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


def test_auth_to_minio(jwt):
    response = requests.post(
        url=f"http://{minio_host}:{minio_port}?Action=AssumeRoleWithCustomToken"
        f"&Token={jwt}"
        f"&Version=2011-06-15"
        f"&DurationSeconds=8600"
        f"&RoleArn=arn:minio:iam:::role/idmp-external-auth-provider"  # This is specified in the config.env of MinIO
    )
    assert response.status_code == 200, print(response.content)
    assert xmltodict.parse(response.content.decode())


def test_authZ_to_minio(jwt):
    response = requests.post(
        url=f"http://{minio_host}:{minio_port}?Action=AssumeRoleWithCustomToken"
        f"&Token={jwt}"
        f"&Version=2011-06-15"
        f"&DurationSeconds=8600"
        f"&RoleArn=arn:minio:iam:::role/idmp-external-auth-provider"  # This is specified in the config.env of MinIO
    )
    assert response.status_code == 200, print(response.content)
    login_info = xmltodict.parse(response.content.decode())
    assert login_info
    credentials = login_info["AssumeRoleWithCustomTokenResponse"][
        "AssumeRoleWithCustomTokenResult"
    ]["Credentials"]
    access_key = credentials["AccessKeyId"]
    secret_access_key = credentials["SecretAccessKey"]
    session_token = credentials["SessionToken"]
    client = Minio(
        endpoint=f"{minio_host}:{minio_port}",
        access_key=access_key,
        secret_key=secret_access_key,
        session_token=session_token,
        secure=False,
    )
    client.bucket_exists(bucket_name="test")
