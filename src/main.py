from fastapi import FastAPI
import endpoints

app = FastAPI()
app.include_router(endpoints.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(8000))
