"""This module contains all methods and variables that are used for authentication by a node"""

import time

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from pydantic_settings import BaseSettings
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_ssh_public_key
import jwt
from pydantic import Field
import os


class SecuritySettings(BaseSettings):
    RSA_PUBLIC_EXP: int = Field(ge=65537)
    KEY_SIZE: int = Field(ge=2048)
    nonce_exp_min: int = 0
    nonce_exp_s: int = Field(lt=60)
    nonce_size: int


settings = SecuritySettings(
    RSA_PUBLIC_EXP=os.environ.get("RSA_PUBLIC_EXP", 65537),
    KEY_SIZE=os.environ.get("KEY_SIZE", 2048),
    nonce_exp_min=os.environ.get("NONCE_EXP_MIN", 1),
    nonce_exp_s=os.environ.get("NONCE_EXP_S", 0),
    nonce_size=os.environ.get("NONCE_SIZE", 10),
)


# These keys will be used to validate incoming transactions and to auth user requests
PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
PUBLIC_KEY = PRIVATE_KEY.public_key()
# This is a dictionary that will contain clients that have requested the nonce for auth
mem_nonce = {}


def serialize_pk_hex() -> str:
    return PUBLIC_KEY.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).hex()


def sign_message(message: bytes) -> bytes:
    return PRIVATE_KEY.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )


def verify_message(message: bytes, signature: bytes) -> bool:
    PUBLIC_KEY.verify(
        signature,
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )
    return True


def verify_user_message(message: bytes, signature: bytes, user_pk: bytes) -> bool:
    user_pk: RSAPublicKey = load_ssh_public_key(user_pk)
    user_pk.verify(
        signature,
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )
    return True


def encrypt(message: bytes) -> bytes:
    return PUBLIC_KEY.encrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def decrypt(ciphertext: bytes) -> bytes:
    return PRIVATE_KEY.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def create_access_token(data: dict) -> str:
    data.update({"exp": settings.nonce_exp_min * 60 + settings.nonce_exp_s})
    data.update({"iat": time.time()})
    data.update({"iss": serialize_pk_hex()})
    return jwt.encode(data, PRIVATE_KEY, algorithm="RS256")


def decode_access_token(encoded_jwt: str) -> dict:
    return jwt.decode(encoded_jwt, PUBLIC_KEY, algorithms=["RS256"])


def get_mem_nonce():
    return mem_nonce


def get_security_settings():
    return settings
