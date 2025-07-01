from pydantic import BaseModel, ConfigDict


class Transaction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: list[str | bytes | int] | str
    is_contract: bool = False
    contract_address: str = ""


class UnconfirmedTransaction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transactions: list[Transaction] = []


class RegisterNode(BaseModel):
    node_address: str
    node_port: str


class Client(BaseModel):
    ip_address: str
    port: str


class InputBlock(BaseModel):
    transactions: list[Transaction]
    index: int
    timestamp: str
    previous_hash: str
    proof: int


class ChallengeRequest(BaseModel):
    client_pk: str  # Hex format
    client_id: str
    client_name: str


class ChallengeResponse(BaseModel):
    nonce: str
    domain: str
    expire: float


class UserSignedMessage(BaseModel):
    message: ChallengeResponse
    client_pk: str  # Hex format
    signature: str  # Hex format


class AccessRequest(BaseModel):
    action: list[str]
    resource: str
