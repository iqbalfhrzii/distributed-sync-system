from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio

from .nodes.lock_manager import LockManager


class LockRequest(BaseModel):
    resource: str
    lock_type: str = "exclusive"
    client: str


class ReleaseRequest(BaseModel):
    resource: str
    client: str


app = FastAPI()
_LM = LockManager()


@app.post("/lock/acquire")
async def acquire_lock(req: LockRequest):
    ok = await _LM.acquire(req.resource, req.client, lock_type=req.lock_type, timeout=3.0)
    if not ok:
        raise HTTPException(status_code=409, detail=f"Resource {req.resource} is locked")
    return {"status": "acquired", "resource": req.resource, "owner": req.client}


@app.post("/lock/release")
async def release_lock(req: ReleaseRequest):
    ok = await _LM.release(req.resource, req.client)
    if not ok:
        raise HTTPException(status_code=400, detail="release failed or not owner")
    return {"status": "released", "resource": req.resource}


@app.get("/lock/status")
def lock_status(resource: str):
    info = _LM.status(resource)
    if not info:
        return {"resource": resource, "locked": False}
    return {"resource": resource, "locked": True, "owner": info.owner, "type": info.lock_type}


@app.get("/")
def root():
    return {"message": "Node HTTP server running"}
