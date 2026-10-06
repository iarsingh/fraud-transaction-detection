# fraud-transaction-detection — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does fraud-transaction-detection address, and what can you demonstrate?

Score amount, foreign flag, and velocity. At or above 0 is review. No payment is captured.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/fraud/main.py`](src/fraud/main.py): Implementation or supporting configuration.
- [`src/fraud/ops.py`](src/fraud/ops.py): Implementation or supporting configuration.
- [`src/fraud/score.py`](src/fraud/score.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`src/fraud/__init__.py`](src/fraud/__init__.py): Implementation or supporting configuration.
- [`Dockerfile`](Dockerfile): Container build/service configuration.
- [`Makefile`](Makefile): Implementation or supporting configuration.
- [`docker-compose.yml`](docker-compose.yml): Container build/service configuration.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `score` and explain the decision it makes?

The main walkthrough here is `score(body)` in [`src/fraud/score.py`](src/fraud/score.py#L11).

```python
def score(body):
    missing = [name for name in REQUIRED if name not in body]
    if missing:
        raise InputError("missing " + ", ".join(missing))
    total = INTERCEPT
    parts = []
    for name, weight in WEIGHTS.items():
        value = body[name]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise InputError(f"{name} must be a number")
        contrib = weight * value
        total += contrib
        parts.append({"feature": name, "contribution": round(contrib, 4)})
    label = "review" if total >= THRESHOLD else "clear"
    return {"score": round(total, 4), "label": label, "threshold": THRESHOLD, "parts": parts}
```

The implementation calls `', '.join`, `InputError`, `WEIGHTS.items`, `isinstance`, `parts.append`, `round`. In an interview, trace those calls in execution order using a fixture input.

## 4. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `HTTPException(status_code=422, detail=str(exc))` in [`src/fraud/main.py`](src/fraud/main.py#L19).
- `HTTPException(status_code=404, detail='workspace not found')` in [`src/fraud/ops.py`](src/fraud/ops.py#L77).
- `HTTPException(status_code=404, detail='job not found')` in [`src/fraud/ops.py`](src/fraud/ops.py#L100).
- `HTTPException(status_code=404, detail='job not found')` in [`src/fraud/ops.py`](src/fraud/ops.py#L109).
- `HTTPException(status_code=403, detail='production apply is disabled in this lab')` in [`src/fraud/ops.py`](src/fraud/ops.py#L113).
- `InputError('missing ' + ', '.join(missing))` in [`src/fraud/score.py`](src/fraud/score.py#L14).
- `InputError(f'{name} must be a number')` in [`src/fraud/score.py`](src/fraud/score.py#L20).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 5. Which test would you use to demonstrate correctness?

[`tests/test_ops.py`](tests/test_ops.py#L8) contains `test_readyz`:

```python
def test_readyz():
    r = client.get("/v1/readyz")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 6. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/fraud/main.py`](src/fraud/main.py#L10).
- `POST /score` → `post_score` in [`src/fraud/main.py`](src/fraud/main.py#L15).
- `GET /readyz` → `readyz` in [`src/fraud/ops.py`](src/fraud/ops.py#L74).
- `POST /workspaces` → `create_workspace` in [`src/fraud/ops.py`](src/fraud/ops.py#L80).
- `GET /workspaces` → `list_workspaces` in [`src/fraud/ops.py`](src/fraud/ops.py#L98).
- `POST /workspaces/{workspace_id}/jobs` → `create_job` in [`src/fraud/ops.py`](src/fraud/ops.py#L106).
- `GET /jobs/{job_id}` → `get_job` in [`src/fraud/ops.py`](src/fraud/ops.py#L130).
- `POST /jobs/{job_id}/approve` → `approve_job` in [`src/fraud/ops.py`](src/fraud/ops.py#L140).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 7. Where does state live, and what happens with multiple workers?

Module-level containers include `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS` in [`src/fraud/ops.py`](src/fraud/ops.py); `WEIGHTS` in [`src/fraud/score.py`](src/fraud/score.py).

These containers belong to a Python process. Inspect which are constant fixtures and which are mutated. Mutable process state needs an explicit shared-storage or synchronization strategy before multiple workers can provide consistent behavior.

## 8. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 9. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 10. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 11. What is the input-to-output contract of `score`?

In [`src/fraud/score.py`](src/fraud/score.py#L11), `score(body)` receives the inputs. The function computes these intermediate values:

- `missing = [name for name in REQUIRED if name not in body]`
- `total = INTERCEPT`
- `parts = []`
- `label = 'review' if total >= THRESHOLD else 'clear'`

Its result is defined by:

- `{'score': round(total, 4), 'label': label, 'threshold': THRESHOLD, 'parts': parts}`

## 12. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/fraud/score.py`](src/fraud/score.py#L11) branches on:

- `missing`
- `not isinstance(value, (int, float)) or isinstance(value, bool)`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

## 13. What does the operations plane add, and where is its limit?

[`src/fraud/ops.py`](src/fraud/ops.py) declares `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}`, `POST /jobs/{job_id}/approve`, `GET /audit`, `GET /metrics`. Inspect the application’s `include_router` call for its URL prefix.

Its state containers are `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`. The job-approval handler defines whether a target is accepted or refused; check that branch and the associated tests instead of treating a recorded job as a successful infrastructure apply.
