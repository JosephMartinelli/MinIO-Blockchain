from pydantic import BaseModel


class UnconfirmedTransactions(BaseModel):
    transactions: list[list] | list[dict]


class RegisterNode(BaseModel):
    node_address: str
    node_port: str


class Client(BaseModel):
    ip_address: str
    port: str


class InputBlock(BaseModel):
    transactions: list[list]
    index: int
    timestamp: str
    previous_hash: str
    proof: int
