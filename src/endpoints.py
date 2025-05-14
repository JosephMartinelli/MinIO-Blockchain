import json
import os

import requests
from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import JSONResponse

from blockchain.blockchain import BlockChain
from blockchain.block import Block
from validation import (
    UnconfirmedTransaction,
    RegisterNode,
    InputBlock,
)

router = APIRouter()
difficulty: int = os.environ.get("difficulty", 7)
blockchain: BlockChain = BlockChain(difficulty=difficulty)
peers = set()
port = os.environ.get("port", 8000)


@router.get(path="/")
async def get_chain() -> list:
    return [x.__dict__ for x in blockchain.chain]


@router.post("/register-transactions", status_code=200)
async def add_new_transactions(transactions: UnconfirmedTransaction):
    transactions = transactions.model_dump()
    blockchain.add_new_transaction(transactions)
    return JSONResponse(status_code=200, content="Transactions added successfully")


@router.post("/register-node", status_code=201)
async def register_node(request: Request):
    """
    This function adds a new peer to the current node by inserting it into the set of his peers
    :return:
    """
    global peers
    to_return_peers = peers.copy()
    if not peers.intersection(f"{request.client.host}:{request.client.port}"):
        peers.add(f"{request.client.host}:{request.client.port}")
    else:
        return JSONResponse(
            status_code=400, content="Client already present into peers!"
        )
    chain = await get_chain()
    return {"chain": chain, "peers": list(to_return_peers)}


@router.post(path="/register-with-node", status_code=200)
async def register_with_node(node_to_register: RegisterNode):
    """
    This function register with an existing node, and it syncs with the blockchain that the node has
    :return:
    """
    global blockchain, peers
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
    blockchain = create_blockchain_from_request(data["chain"])
    return JSONResponse(
        status_code=200,
        content=f"Successfully registered to node {node_info['node_address']}, and now I can see the following"
        f" peers: {peers}",
    )


@router.post(path="/add-block", status_code=201)
async def add_block(in_block: InputBlock):
    global blockchain
    block = Block(**in_block.model_dump())
    try:
        blockchain.add_block(block)
    except (ValueError, IndexError) as e:
        return JSONResponse(
            status_code=400,
            content=f"Block discarded by the node due to the following error: {e}",
        )
    if not blockchain.is_chain_valid():
        blockchain.chain.pop(-1)
        return JSONResponse(
            status_code=400,
            content="Last block invalidated the chain, reverting back...",
        )


def create_blockchain_from_request(data: list[dict]) -> BlockChain:
    if len(data) == 1:
        blockchain = BlockChain(difficulty, genesis_block=Block(**data[0]))
    else:
        blockchain = BlockChain(difficulty)
        for block in data[1:]:
            blockchain.chain.append(Block(**block))
    if not blockchain.is_chain_valid():
        raise RuntimeError("Blockchain has been tampered!")
    return blockchain


@router.get("/consensus", status_code=200)
async def consensus():
    """
    This function will check all the peers of a given node and will try to figure out who has the longest valid chain.
    When found, all the nodes will swap their chain with the longest valid chain found since it is considered the most updated
    one.
    :return:
    """
    max_chain = []
    # First, find the longest oldest chain
    for indx, peer in enumerate(peers):
        # Get peer chain
        response = requests.get(url=f"http://{peer}/")
        if response.status_code != 200:
            raise RuntimeError("Could not get peer chain")
        peer_chain = response.json()
        if len(peer_chain) > len(max_chain):
            max_chain = peer_chain

    # Found the maximum chain we get that chain
    create_blockchain_from_request(max_chain.json())

    for peer in peers:
        response = requests.get(url=f"http://{peer}/consensus")
        if response.status_code != 200:
            raise RuntimeError(
                f"An error occurred during consensus, the following peer caused the error"
                f" {response.status_code} {response.content}"
            )


@router.get("/mine", status_code=200)
async def mine() -> str:
    result = blockchain.mine()
    if isinstance(result, bool) and not result:
        return "No uncommitted transactions are present!"
    else:
        # If we have the longest valid chain, than we need to announce the new block we have mined so that the
        # others node can add it
        current_chain_length: int = len(blockchain.chain)
        await consensus()
        if current_chain_length == len(blockchain.chain):
            await announce_new_block()
        return result


async def announce_new_block():
    """
    This function announces the new mined block to all the peers
    :return:
    """
    block_to_announce = blockchain.get_last_bloc
    for peer_url in peers:
        response = requests.post(
            url=f"http://{peer_url}/add-block",
            data=json.dumps(block_to_announce.__dict__),
        )
        if response.status_code != 201:
            raise RuntimeError(
                f"Error in announcing the new block to the other peers\n {response.content}"
            )
