from fastapi import FastAPI


app = FastAPI(
    title="Zania Document QA API",
    description="Answer questions using information from uploaded documents.",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
