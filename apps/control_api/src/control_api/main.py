from fastapi import FastAPI

app = FastAPI(title="EU5 Optimizer Control API", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
