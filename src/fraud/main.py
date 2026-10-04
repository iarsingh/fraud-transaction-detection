from fastapi import FastAPI, HTTPException
from fraud.score import InputError, score

app = FastAPI()


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/score")
def post_score(body: dict):
    try:
        return score(body)
    except InputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
