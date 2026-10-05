from fraud.ops import router as ops_router
from fastapi import FastAPI, HTTPException
from fraud.score import InputError, score

app = FastAPI()
app.include_router(ops_router, prefix="/v1")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/score")
def post_score(body: dict):
    try:
        return score(body)
    except InputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
