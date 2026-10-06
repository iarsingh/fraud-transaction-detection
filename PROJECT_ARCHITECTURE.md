# fraud-transaction-detection — project architecture

[README](README.md) · [Interview questions and answers](INTERVIEW_QA.md)

## Purpose and scope

Score amount, foreign flag, and velocity. At or above 0 is review. No payment is captured.

This document describes files and symbols in this checkout. Deployment templates and statements in the original overview are distinguished from a verified running environment.

## Component diagram

```mermaid
flowchart LR
    M0["src/fraud/__init__.py"]
    M1["src/fraud/main.py"]
    M2["src/fraud/ops.py"]
    M3["src/fraud/score.py"]
    M1 -->|imports| M2
    M1 -->|imports| M3
```

For Python repositories, arrows show resolved local imports, not network calls or deployment order. Otherwise the diagram is a repository component map; containment arrows do not assert runtime integration.

## Components and responsibilities

| Component | Responsibility |
| --- | --- |
| [`src/fraud/main.py`](src/fraud/main.py) | HTTP handlers: `GET /healthz`, `POST /score` |
| [`src/fraud/ops.py`](src/fraud/ops.py) | HTTP handlers: `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}` |
| [`src/fraud/score.py`](src/fraud/score.py) | Functions: `score` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`src/fraud/__init__.py`](src/fraud/__init__.py) | Implementation or supporting configuration |
| [`Dockerfile`](Dockerfile) | Container build/service configuration |
| [`Makefile`](Makefile) | Implementation or supporting configuration |
| [`docker-compose.yml`](docker-compose.yml) | Container build/service configuration |
| [`tests/test_ops.py`](tests/test_ops.py) | Executable checks and regression examples |
| [`tests/test_score.py`](tests/test_score.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Project explanations or operating notes |

## Existing design and operating guides

These checked-in guides provide the project’s detailed design, operational context, or deployment view:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Request interface

| Method and path | Handler | Source |
| --- | --- | --- |
| `GET /healthz` | `healthz` | [`src/fraud/main.py`](src/fraud/main.py#L10) |
| `POST /score` | `post_score` | [`src/fraud/main.py`](src/fraud/main.py#L15) |
| `GET /readyz` | `readyz` | [`src/fraud/ops.py`](src/fraud/ops.py#L74) |
| `POST /workspaces` | `create_workspace` | [`src/fraud/ops.py`](src/fraud/ops.py#L80) |
| `GET /workspaces` | `list_workspaces` | [`src/fraud/ops.py`](src/fraud/ops.py#L98) |
| `POST /workspaces/{workspace_id}/jobs` | `create_job` | [`src/fraud/ops.py`](src/fraud/ops.py#L106) |
| `GET /jobs/{job_id}` | `get_job` | [`src/fraud/ops.py`](src/fraud/ops.py#L130) |
| `POST /jobs/{job_id}/approve` | `approve_job` | [`src/fraud/ops.py`](src/fraud/ops.py#L140) |
| `GET /audit` | `audit` | [`src/fraud/ops.py`](src/fraud/ops.py#L160) |
| `GET /metrics` | `metrics` | [`src/fraud/ops.py`](src/fraud/ops.py#L176) |

The table lists literal route decorators found in the inspected Python modules. Router prefixes and middleware can add behavior; check the linked handler and application setup before calling an endpoint.

## Implementation walkthrough

### `score(body)`

Source: [`src/fraud/score.py`](src/fraud/score.py#L11).

Calls visible in this function: `', '.join`, `InputError`, `WEIGHTS.items`, `isinstance`, `parts.append`, `round`.

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

## Validation and failure paths

| Explicit exception | Source |
| --- | --- |
| `HTTPException(status_code=422, detail=str(exc))` | [`src/fraud/main.py`](src/fraud/main.py#L19) |
| `HTTPException(status_code=404, detail='workspace not found')` | [`src/fraud/ops.py`](src/fraud/ops.py#L77) |
| `HTTPException(status_code=404, detail='job not found')` | [`src/fraud/ops.py`](src/fraud/ops.py#L100) |
| `HTTPException(status_code=404, detail='job not found')` | [`src/fraud/ops.py`](src/fraud/ops.py#L109) |
| `HTTPException(status_code=403, detail='production apply is disabled in this lab')` | [`src/fraud/ops.py`](src/fraud/ops.py#L113) |
| `InputError('missing ' + ', '.join(missing))` | [`src/fraud/score.py`](src/fraud/score.py#L14) |
| `InputError(f'{name} must be a number')` | [`src/fraud/score.py`](src/fraud/score.py#L20) |

These are explicit exceptions in the inspected source, rather than a claim that every failure is handled. Follow the calling handler to see whether the exception becomes an HTTP response or propagates.

## Data and state

- [`src/fraud/ops.py`](src/fraud/ops.py) defines module-level containers: `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`.
- [`src/fraud/score.py`](src/fraud/score.py) defines module-level containers: `WEIGHTS`.

Module-level dictionaries/lists live in a Python process. They can be fixtures or mutable state; inspect writes before treating them as persistent storage. A production extension would need to define persistence and concurrency behavior explicitly.

## Data flow and design decisions

### What is the input-to-output contract of `score`

In [`src/fraud/score.py`](src/fraud/score.py#L11), `score(body)` receives the inputs. The function computes these intermediate values:

- `missing = [name for name in REQUIRED if name not in body]`
- `total = INTERCEPT`
- `parts = []`
- `label = 'review' if total >= THRESHOLD else 'clear'`

Its result is defined by:

- `{'score': round(total, 4), 'label': label, 'threshold': THRESHOLD, 'parts': parts}`

### Which decision rules or boundary conditions should an interviewer challenge

The implementation in [`src/fraud/score.py`](src/fraud/score.py#L11) branches on:

- `missing`
- `not isinstance(value, (int, float)) or isinstance(value, bool)`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

### What does the operations plane add, and where is its limit

[`src/fraud/ops.py`](src/fraud/ops.py) declares `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}`, `POST /jobs/{job_id}/approve`, `GET /audit`, `GET /metrics`. Inspect the application’s `include_router` call for its URL prefix.

Its state containers are `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`. The job-approval handler defines whether a target is accepted or refused; check that branch and the associated tests instead of treating a recorded job as a successful infrastructure apply.

## Setup and verification

The following commands are derived from the checked-in dependency/test contracts. Execute them from the repository root; the block prepares a local environment, not a cloud deployment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Python dependencies: [`requirements.txt`](requirements.txt).

Test entry points: [`tests/test_ops.py`](tests/test_ops.py), [`tests/test_score.py`](tests/test_score.py).

Automation definitions: [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Read their triggers and job steps to determine what CI actually runs.

## Operating boundaries and design review

Before turning this checkout into a customer deployment, establish the input contract, data ownership, access controls, failure response, evaluation criteria, and rollback owner. Repository fixtures and unit tests demonstrate local behavior; they do not establish throughput, uptime, compliance, or business impact.

A useful architecture review starts with the linked implementation: identify where input enters, where a decision is made, which state can change, and which external dependency can fail. Add a deployment view only for infrastructure that is actually configured and exercised.
