from pydantic import BaseModel


class Transaction(BaseModel):
    data: list[str | bytes] = []
    is_contract: bool = False
    contract_address: str = ""


class UnconfirmedTransaction(BaseModel):
    transactions: list[Transaction] = []


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
