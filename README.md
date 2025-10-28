# Distributed Synchronization System

A distributed system implementation featuring Raft consensus, distributed queue with consistent hashing, and cache coherence using the MESI protocol.

## Features

- **Distributed Lock Manager**
  - Raft Consensus implementation
  - Support for shared and exclusive locks
  - Network partition handling
  - Deadlock detection

- **Distributed Queue System**
  - Consistent hashing for queue distribution
  - At-least-once delivery guarantee
  - Message persistence and recovery
  - Multiple producers/consumers support

- **Cache Coherence**
  - MESI protocol implementation
  - Multiple cache nodes support
  - Cache invalidation and update propagation
  - LRU cache replacement policy

## Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- Redis
- Prometheus & Grafana (for monitoring)

## How to Use
Run docker
```powershell
docker-compose up -d
```

```powershell
docker ps
```

Distributed Lock Manager
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/lock" `
  -Method POST `
  -Body '{"resource":"fileA","type":"exclusive","client":"client-1"}' `
  -ContentType "application/json" | ConvertFrom-Json
```

```powershell
Invoke-WebRequest -Uri "http://localhost:5002/lock" `
  -Method POST `
  -Body '{"resource":"fileA","type":"shared","client":"client-2"}' `
  -ContentType "application/json" | ConvertFrom-Json
```

Log Aktivitas Node
```powershell
docker logs docker-node1 --tail 30
```

Benchmarking Menggunakan Locust
```powershell
python -m locust -f load_test_scenarios.py --host http://localhost:5001
```

Uji Kegagalan (Node Failure Test)
```powershell
docker stop docker-node1
```

```powershell
docker ps
```

```powershell
docker start docker-node1
```
