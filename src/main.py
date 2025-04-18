import json

from fastapi import FastAPI, Request
from pydantic import BaseModel
from starlette.responses import JSONResponse
import requests
from blockchain import BlockChain, Block
import os


app = FastAPI()
blockchain: BlockChain = BlockChain(difficulty=5)
peers = set()
port = os.environ.get("port", 8000)


@app.get(path="/")
async def get_chain() -> list:
    return [x.__dict__ for x in blockchain.chain]


class UnconfirmedTransactions(BaseModel):
    transactions: list[list] | list[dict]


@app.post("/register-transactions", status_code=200)
async def add_new_transactions(transactions: UnconfirmedTransactions):
    transactions = transactions.model_dump()
    blockchain.add_new_transaction(transactions["transactions"])
    return JSONResponse(status_code=200, content="Transactions added successfully")


class RegisterNode(BaseModel):
    node_address: str
    node_port: str


class Client(BaseModel):
    ip_address: str
    port: str


@app.post("/register-node", status_code=201)
async def register_node(client: Client):
    """
    This function adds a new peer to the current node by inserting it into the set of his peers
    :return:
    """
    client = client.model_dump()
    if not client:
        return JSONResponse(
            status_code=404, content="Node address cannot be an empty field!"
        )
    if not peers.intersection(f"{client['ip_address']}:{client['port']}"):
        peers.add(f"{client['ip_address']}:{client['port']}")
    else:
        return JSONResponse(
            status_code=400, content="Client already present into peers!"
        )
    chain = await get_chain()
    return {"chain": chain, "peers": list(peers)}


@app.post(path="/register-with-node", status_code=200)
async def register_with_node(node_to_regiser: RegisterNode, request: Request):
    """
    This function register with an existing node, and it syncs with the blockchain that the node has
    :return:
    """
    node_info = node_to_regiser.model_dump()
    # Register with node
    try:
        response = requests.post(
            url=f"http://{node_info['node_address']}:{node_info['node_port']}/register-node",
            data=json.dumps({"ip_address": request.client.host, "port": port}),
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
    global blockchain, peers
    data = response.json()
    peers.update(data["peers"])
    return JSONResponse(
        status_code=200,
        content=f"Successfully registered to node {node_info['node_address']}, and now I can see the following"
        f"peers: {peers}",
    )


def create_blockchain_from_request(data: list[dict]) -> BlockChain:
    if len(data) == 1:
        blockchain = BlockChain(5, genesis_block=Block(**data[0]))
    else:
        blockchain = BlockChain(5)
        for block in data[1:]:
            blockchain.chain.append(Block(**block))
    if not blockchain.is_chain_valid():
        raise RuntimeError("Blockchain has been tampered!")
    return blockchain


def consesus():
    pass


class InputBlock(BaseModel):
    transactions: list[list]
    index: int
    timestamp: str
    previous_hash: str
    proof: int


@app.post(path="/add-block", status_code=201)
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


@app.get("/mine", status_code=200)
async def mine() -> str:
    result = blockchain.mine()
    if isinstance(result, bool) and not result:
        return "No uncommitted transactions are present!"
    else:
        announce_new_block()
        return result


def announce_new_block():
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(port))
