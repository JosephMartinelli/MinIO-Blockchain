import json
from typing import Annotated

import requests
from fastapi import APIRouter, Depends
from starlette.requests import Request
from starlette.responses import JSONResponse

from blockchain.ac_blockchain import ACBlockchain
from blockchain.errors import NoTransactionsFound, InvalidChain
from blockchain.ac_block import ACBlock
from validation import (
    InputBlock,
    RegisterNode,
)
from ..ac_validation import ACPolicy

from ..dependency import (
    get_peers,
    get_blockchain,
    create_blockchain,
    get_logger,
    get_policies_cache,
)

from logging import Logger
from anyio import move_on_after

router = APIRouter(
    dependencies=[
        Depends(get_peers),
        Depends(get_blockchain),
        Depends(get_policies_cache),
        Depends(get_logger),
    ]
)

peers_dependency = Annotated[set, Depends(get_peers)]
logger_dep = Annotated[Logger, Depends(get_logger)]
policies_dep = Annotated[dict, Depends(get_policies_cache)]
blockchain_dependency = Annotated[ACBlockchain, Depends(get_blockchain)]
create_blockchain_dependency = Annotated[ACBlockchain, Depends(create_blockchain)]


@router.get(path="/")
async def get_chain(blockchain: blockchain_dependency) -> dict:
    return {
        "chain": [x.__dict__ for x in blockchain.chain],
        "difficulty": blockchain.difficulty,
    }


@router.post("/add-policy", status_code=201)
async def add_new_policy(
    policy: ACPolicy,
    blockchain: blockchain_dependency,
    peers: peers_dependency,
    request: Request,
    logger: logger_dep,
):
    """
    This method adds a new policy to the mem pool so that a miner can later mine and add them
    to the blockchain. When a new policy is added, it is broadcasted to the node's peers
    following the gossip protocol
    :param policy:
    :param blockchain:
    :return:
    """
    # The policy is validated by FastAPI
    policy = policy.model_dump()
    if policy not in blockchain.unconfirmed_transactions:
        blockchain.add_new_transaction(policy)
        # Propagate the policy to the node's peers
        logger.info("Gossip protocol initiated by %s", request.client.host)
        await gossip(policy, peers, logger)
    return JSONResponse(status_code=200, content="Transactions added successfully")


async def gossip(policy: dict, peers: set, logger: Logger):
    for peer in peers:
        response = requests.post(
            url=f"http://{peer}/add-policy", data=json.dumps(policy)
        )
        if response.status_code != 201:
            logger.warning(
                f"Peer {peer} returned the following error: {response.status_code}/{response.content}"
            )


@router.get("/update-cache")
async def update_local_cache(
    mem_policies: policies_dep, blockchain: blockchain_dependency
):
    """
    This method instructs the node to update their local cache of the current valid access policies
    :return:
    """
    for block in blockchain.chain:
        blockchain.apply_policy_delta(block.body.policies, mem_policies)


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


@router.get("/consensus", status_code=200)
async def consensus(
    peers: peers_dependency, blockchain: blockchain_dependency, logger: logger_dep
):
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
            logger.warning("Node could not get peer chain")
        peer_chain = response.json()
        if len(peer_chain) > len(max_chain):
            max_chain = peer_chain
            replaced = True

    # Found the longest chain, we get it and we validate it
    if replaced:
        blockchain.create_blockchain_from_request(max_chain)

    return {"replaced": replaced}


async def announce_new_block(blockchain: ACBlockchain, peers: set):
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


@router.post(path="/add-block", status_code=201)
async def add_block(
    in_block: InputBlock, blockchain: blockchain_dependency, mem_pool: policies_dep
):
    block = ACBlock(**in_block.model_dump())
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
    # If the block is added successfully and the blockchain is valid then we remove
    # the transactions added to the block from our transactions pool
    new_unconfirmed_transactions = []
    for policy in blockchain.unconfirmed_transactions:
        if block.body.policies.get(policy.id, None) is not None:
            new_unconfirmed_transactions.append(policy)
    blockchain.unconfirmed_transactions = new_unconfirmed_transactions
    return JSONResponse(status_code=201, content="Block added successfully")


@router.get("/register-peer", status_code=200)
async def register_peer(
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
    mem_policies: policies_dep,
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
            url=f"http://{node_info['node_address']}:{node_info['node_port']}/register-peer"
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
    # Then I refresh my view of the access policies
    await update_local_cache(mem_policies, blockchain)
    return JSONResponse(
        status_code=200,
        content=f"Successfully registered to node {node_info['node_address']}, and now I can see the following"
        f" peers: {peers}",
    )
