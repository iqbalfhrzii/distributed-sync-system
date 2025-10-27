import asyncio
import logging
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from .nodes.cache_node import CacheNode
from .utils.config import Config
from .consensus.raft import RaftNode
from .nodes.queue_node import DistributedQueue


# ----- HTTP API (small wrapper around a local cache node) -----
app = FastAPI()
cache_node = CacheNode(node_id="node-1")


class CacheItem(BaseModel):
    key: str
    value: str


@app.post("/cache/set")
def api_set_cache(item: CacheItem):
    cache_node.set(item.key, item.value)
    return {"status": "ok", "key": item.key}


@app.get("/cache/get")
def api_get_cache(key: str):
    v = cache_node.get(key)
    if v is None:
        return {"detail": "Not Found"}
    return {"key": key, "value": v}


# ----- Node runtime -----
async def main_node():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("distributed.node")

    cfg = Config.get_node_config()
    logger.info("node config: %s", cfg)

    raft = RaftNode(cfg["node_id"], cfg["host"], cfg["port"])
    queue = DistributedQueue(cfg["node_id"])

    # register peers
    for p in cfg.get("peers", []):
        await raft.connect_to_peer(p["node_id"], p["host"], p["port"])

    peer_ids = [p["node_id"] for p in cfg.get("peers", [])]
    await queue.initialize([cfg["node_id"]] + peer_ids)

    try:
        await raft.start()
        logger.info("node started")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("shutting down")
        await raft.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    cfg = Config.get_node_config()
    http_port = cfg.get("http_port", 5001)

    # Run FastAPI server in the background and then run node logic.
    # uvicorn.run blocks by default, so we run it in a separate thread via
    # create_task wrapper which internally starts the server.
    loop.create_task(uvicorn.run(app, host="0.0.0.0", port=http_port, log_level="info"))
    loop.run_until_complete(main_node())
