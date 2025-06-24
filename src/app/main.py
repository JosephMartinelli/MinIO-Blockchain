from fastapi import FastAPI
from app.nodes import light_node, full_node
from app.config import NodeRole, settings
from contextlib import asynccontextmanager

# from dependency import set_global_chain
import pandas as pd

# import datetime
from app.onstartup_contracts import load_contracts

# from blockchain.ac_blockchain import ACBlock, ACBlockchain
from onstartup_policies import load_policies


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This function defines the logic of the FastAPIcls application life-cycle. The code before the yield is run
    BEFORE the application is launched while the code after the yield is run AFTER the app execution. The code
    is run only once.
    """
    # We fetch from other admin
    if settings.node_role == NodeRole.PUBLISHER and settings.peers == "":
        contract_header: pd.DataFrame = load_contracts()
        policy_header: dict = load_policies()
        # We set the blockchain that will be used by the node
        # TODO: Define this process
        # set_global_chain(
        #     ACBlockchain(difficulty=settings.chain_difficulty, genesis_block=genesis)
        # )
    yield


app = FastAPI(lifespan=lifespan)

if settings.node_role == NodeRole.PUBLISHER:
    app.include_router(full_node.router)
    app.include_router(light_node.router)
else:
    app.include_router(light_node.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.port)
