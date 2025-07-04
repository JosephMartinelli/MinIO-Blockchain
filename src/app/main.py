from fastapi import FastAPI
from app.nodes import light_node, full_node, authentication
from app.config import NodeRole, settings
from contextlib import asynccontextmanager

from onstartup_contracts import load_contracts
from policy_util import load_policies
from dependency import set_global_chain, get_blockchain, get_logger

from blockchain.ac_blockchain import ACBlock, ACBlockchain
from blockchain.ac_transaction import ACPolicy
import pandas as pd
import time
from anyio import fail_after

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This function defines the logic of the FastAPIcls application life-cycle. The code before the yield is run
    BEFORE the application is launched while the code after the yield is run AFTER the app execution. The code
    is run only once.
    """
    failure = False
    # We fetch from other admin
    if (
        not isinstance(settings.peers, list)
        and settings.node_role == NodeRole.PUBLISHER
    ):
        try:
            with fail_after(5):
                await full_node.consensus(settings.peers, get_blockchain(), logger)
        except TimeoutError:
            logger.warning(
                "Consensus during startup failed, node will init with a local chain"
            )
            failure = True
    elif failure or settings.node_role == NodeRole.PUBLISHER:
        logger.debug("Node starting with a local chain")
        contract_header: pd.DataFrame = load_contracts()
        policies: list[ACPolicy] = load_policies()
        # We set the blockchain that will be used by the node
        genesis = ACBlock(
            index=0,
            contract_header=contract_header,
            policies=policies,
            timestamp=time.time(),
            previous_hash="0",
        )
        set_global_chain(
            ACBlockchain(difficulty=settings.chain_difficulty, genesis_block=genesis)
        )
    # If there are peers we trigger consensus so that we get the longest valid chain
    yield


app = FastAPI(lifespan=lifespan)

if settings.node_role == NodeRole.PUBLISHER:
    app.include_router(full_node.router)
    app.include_router(light_node.router)
    app.include_router(authentication.router)
else:
    app.include_router(light_node.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.port)
