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

## Project Structure

```
distributed-sync-system/
├── src/
│   ├── nodes/
│   │   ├── base_node.py
│   │   ├── lock_manager.py
│   │   ├── queue_node.py
│   │   └── cache_node.py
│   ├── consensus/
│   │   └── raft.py
│   ├── communication/
│   │   └── message_passing.py
│   └── utils/
│       ├── config.py
│       └── metrics.py
├── docker/
│   ├── Dockerfile.node
│   └── docker-compose.yml
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd distributed-sync-system
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the System

### Using Docker Compose

1. Build and start the containers:
```bash
docker-compose -f docker/docker-compose.yml up --build
```

2. Monitor the nodes:
- Access Prometheus: http://localhost:9090
- Access Grafana: http://localhost:3000 (admin/admin)

### Manual Setup

1. Start individual nodes:
```bash
# Terminal 1
export NODE_ID=node1 PORT=5001 PEERS=node2:5002,node3:5003
python -m src.main

# Terminal 2
export NODE_ID=node2 PORT=5002 PEERS=node1:5001,node3:5003
python -m src.main

# Terminal 3
export NODE_ID=node3 PORT=5003 PEERS=node1:5001,node2:5002
python -m src.main
```

## Testing

Run the test suite:
```bash
pytest tests/
```

## Performance Testing

Run load tests:
```bash
locust -f benchmarks/load_test_scenarios.py
```

## Documentation

- Full technical documentation is available in the `docs/` directory
- API documentation available at `docs/api_spec.yaml`
- Performance analysis report at `docs/performance_report.md`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.