from datetime import datetime

from fastapi import APIRouter, Depends
from ..dependency import get_peers, get_blockchain
from blockchain.ac_blockchain import ACBlockchain
from blockchain.transaction import ACTransaction
from blockchain.ac_block import ACBlock
from validation import ChallengeRequest, ChallengeResponse
from typing import Annotated

router = APIRouter(dependencies=[Depends(get_peers), Depends(get_blockchain)])
peers_dependency = Annotated[set, Depends(get_peers)]
blockchain_dependency = Annotated[ACBlockchain, Depends(get_blockchain)]


@router.post(path="/challenge", response_model=ChallengeResponse, status_code=200)
def challenge(
    request: ChallengeRequest, blockchain: blockchain_dependency
) -> ChallengeResponse:
    request: dict = request.model_dump()
    # Get MAC address by searching it in the genesis block
    genesis: ACBlock = blockchain.chain[0]
    # Make a transaction logging the authentication and call the nonce-generating contract
    tr_payload = {
        "timestamp": datetime.now(),
        "type": "AUTHORIZATION",
        "requester_pk": request["public_key"],
        "requester_name": request["client_name"],
        "requester_id": request["client_id"],
        "requester_group": None,
    }
    transaction = ACTransaction(data=tr_payload, is_contract=False, contract_address="")
