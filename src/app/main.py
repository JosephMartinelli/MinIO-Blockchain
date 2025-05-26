from fastapi import FastAPI
from app.nodes import light_node, full_node
from app.config import settings, NodeRole
from contextlib import asynccontextmanager
from app.startup import populate_local_blockchain


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This function defines the logic of the FastAPIcls application life-cycle. The code before the yield is run
    BEFORE the application is launched while the code after the yield is run AFTER the app execution. The code
    is run only once.
    """
    # We fetch from other admin
    if settings.node_role == NodeRole.PUBLISHER:
        populate_local_blockchain()
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
