from fastapi import FastAPI
from app.nodes import light_node, full_node
from .config import settings, NodeRole


app = FastAPI()

if settings.node_role == NodeRole.PUBLISHER:
    app.include_router(full_node.router)
    app.include_router(light_node.router)
else:
    app.include_router(light_node.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.port)
