import json
from typing import Annotated

import requests
from fastapi import APIRouter, Depends
from starlette.requests import Request
from starlette.responses import JSONResponse

from blockchain.blockchain import BlockChain
from blockchain.errors import NoTransactionsFound, InvalidChain
from blockchain.block import Block
from validation import (
    UnconfirmedTransaction,
    InputBlock,
    RegisterNode,
)

from ..dependency import get_peers, get_blockchain, create_blockchain

from anyio import move_on_after

router = APIRouter(dependencies=[Depends(get_peers)])

peers_dependency = Annotated[set, Depends(get_peers)]
blockchain_dependency = Annotated[BlockChain, Depends(get_blockchain)]
create_blockchain_dependency = Annotated[BlockChain, Depends(create_blockchain)]


@router.get(path="/")
async def get_chain(blockchain: blockchain_dependency) -> dict:
    return {
        "chain": [x.__dict__ for x in blockchain.chain],
        "difficulty": blockchain.difficulty,
    }


@router.post("/register-transactions", status_code=200)
async def add_new_transactions(
    transactions: UnconfirmedTransaction, blockchain: blockchain_dependency
):
    transactions = transactions.model_dump()
    blockchain.add_new_transaction(transactions["transactions"])
    return JSONResponse(status_code=200, content="Transactions added successfully")


@router.post(path="/add-block", status_code=201)
async def add_block(in_block: InputBlock, blockchain: blockchain_dependency):
    block = Block(**in_block.model_dump())
    try:
        result = blockchain.add_block(block)
    except (IndexError, InvalidChain) as e:
        return JSONResponse(
            status_code=400,
            content=f"Block discarded by the node due to the following error: {e}",
        )
    if not blockchain.is_chain_valid() or not result:
        blockchain.chain.pop(-1)
        return JSONResponse(
            status_code=400,
            content="Last block invalidated the chain, reverting back...",
        )
    else:
        return JSONResponse(status_code=201, content="Block added successfully")


@router.get("/consensus", status_code=200)
async def consensus(peers: peers_dependency, blockchain: blockchain_dependency):
    """
    This function will check all the peers of a given node and will try to figure out who has the longest valid chain.
    When found, all the nodes will swap their chain with the longest valid chain found since it is considered the most updated
    one.
    :return:
    """
    max_chain = blockchain.chain
    replaced = False
    # First, find the longest oldest chain
    for indx, peer in enumerate(peers):
        # Get peer chain
        with move_on_after(2.5):
            try:
                response = requests.get(url=f"http://{peer}/")
            except requests.exceptions.ConnectionError:
                continue
        if response.status_code != 200:
            raise RuntimeError("Could not get peer chain")
        peer_chain = response.json()
        if len(peer_chain) > len(max_chain):
            max_chain = peer_chain
            replaced = True

    # Found the longest chain, we get it and we validate it
    if replaced:
        blockchain.create_blockchain_from_request(max_chain)

    return {"replaced": replaced}


@router.get("/mine", status_code=200)
async def mine(blockchain: blockchain_dependency, peers: peers_dependency):
    try:
        result = blockchain.mine()
    except NoTransactionsFound:
        return JSONResponse(
            status_code=400, content="No transactions have been found on this node!"
        )
    # When a block has been mined, all the nodes by using consensus need to reach
    # a common view of the blockchain
    with move_on_after(2.5):
        response = await consensus(peers, blockchain)
    if not response["replaced"]:
        await announce_new_block(blockchain, peers)
    return result


async def announce_new_block(blockchain: BlockChain, peers: set):
    """
    This function announces the new mined block to all the peers
    :return:
    """
    block_to_announce = blockchain.get_last_bloc
    for peer_url in peers:
        try:
            response = requests.post(
                url=f"http://{peer_url}/add-block",
                data=json.dumps(block_to_announce.__dict__),
            )
        except requests.exceptions.ConnectionError:
            continue
        if response.status_code != 201:
            raise RuntimeError(
                f"Error in announcing the new block to the other peers\n {response.content}"
            )


@router.get("/register-node", status_code=200)
async def register_node(
    request: Request, peers: peers_dependency, blockchain: blockchain_dependency
):
    """
    This function adds a new peer to the current node by inserting it into the set of his peers
    :return:
    """
    to_return_peers = peers.copy()
    if not peers.intersection(f"{request.client.host}:{request.client.port}"):
        peers.add(f"{request.client.host}:{request.client.port}")
    else:
        return JSONResponse(
            status_code=400, content="Client already present into peers!"
        )
    chain_data: dict = await get_chain(blockchain)
    return {
        "chain": chain_data["chain"],
        "difficulty": chain_data["difficulty"],
        "peers": list(to_return_peers),
    }


@router.post(path="/register-with-node", status_code=200)
async def register_with_node(
    node_to_register: RegisterNode,
    peers: peers_dependency,
    blockchain: blockchain_dependency,
):
    """
    This function register with an existing node, and it syncs with the blockchain that the node has
    :return:
    """
    node_info = node_to_register.model_dump()
    if (
        len(peers.intersection(f"{node_info['node_address']}:{node_info['node_port']}"))
        == 1
    ):
        return JSONResponse(
            status_code=400,
            content=f"This node is already registered with {node_info['node_address']}",
        )
    # Register with node
    try:
        response = requests.post(
            url=f"http://{node_info['node_address']}:{node_info['node_port']}/register-node"
        )
    except requests.exceptions.ConnectionError:
        return JSONResponse(
            status_code=400,
            content=f"Could not connect with node at {node_info['node_address']}",
        )
    if response.status_code != 201:
        return JSONResponse(
            status_code=400,
            content=f"Could not register with node at {node_info['node_address']}\n, {response.content}",
        )
    # If I could register, then I update my local view of the blockchain
    data = response.json()
    peers.update(set(data["peers"]))
    # Then I add to my peers the node that I am registering to
    peers.add(f"{node_info['node_address']}:{node_info['node_port']}")
    # Updating local view of the blockchain
    blockchain.create_blockchain_from_request(data["chain"])
    return JSONResponse(
        status_code=200,
        content=f"Successfully registered to node {node_info['node_address']}, and now I can see the following"
        f" peers: {peers}",
    )
