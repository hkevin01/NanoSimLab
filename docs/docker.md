# 🐳 Docker Setup and Usage

NanoSimLab provides a comprehensive Docker orchestration system that includes both a REST API backend and a responsive web GUI frontend. This setup allows you to run the entire application stack with a single command.

## Quick Start

1. **Clone and navigate to the repository:**
   ```bash
   git clone https://github.com/hkevin01/NanoSimLab.git
   cd NanoSimLab
   ```

2. **Start the complete application stack:**
   ```bash
   ./run.sh up
   ```

3. **Access the applications:**
   - **Web GUI**: http://localhost:3000
   - **API Documentation**: http://localhost:8080/docs
   - **API Health Check**: http://localhost:8080/status

## Prerequisites

- Docker (v20.10+)
- Docker Compose (v2.0+) or docker-compose (v1.29+)
- Bash shell (macOS/Linux)

The orchestration script automatically detects your Docker setup and uses the appropriate commands.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Web GUI       │    │   REST API      │
│  (Port 3000)    │◄───┤  (Port 8080)    │
│   Static Files  │    │   FastAPI       │
│   + JavaScript  │    │   + NanoSimLab  │
└─────────────────┘    └─────────────────┘
        │                       │
        └───────────────────────┘
            Docker Network
```

### Components

- **REST API Backend**: FastAPI server exposing NanoSimLab functionality
- **Web GUI Frontend**: Responsive single-page application with real-time simulation monitoring
- **Docker Orchestration**: Comprehensive run.sh script managing the entire stack

## Run Script Commands

The `./run.sh` script provides a complete Docker orchestration interface:

### Basic Commands
```bash
./run.sh help                 # Show detailed usage information
./run.sh up                   # Start all services (auto-creates GUI if missing)
./run.sh down                 # Stop and remove all services
./run.sh restart              # Restart all services
./run.sh status               # Show service status and health
```

### Development Commands
```bash
./run.sh build                # Build Docker images
./run.sh logs [service]       # Show logs (default: api)
./run.sh shell [service]      # Open shell in container
./run.sh exec "command"       # Execute command in API container
```

### GUI Management
```bash
./run.sh gui:create           # Create GUI scaffold if missing
./run.sh gui:create --force   # Recreate GUI (overwrites existing)
./run.sh gui:open             # Open GUI in default browser
```

### Maintenance Commands
```bash
./run.sh ps                   # Show running containers
./run.sh clean                # Remove containers and volumes
./run.sh prune                # Clean entire Docker system (WARNING)
```

## Configuration

### Environment Variables

Create a `.env` file to customize your setup:

```bash
# Copy the example configuration
cp .env.example .env

# Edit configuration
nano .env
```

**Key Configuration Options:**

| Variable         | Default                 | Description                 |
| ---------------- | ----------------------- | --------------------------- |
| `PORTS`          | `8080:8080`             | API port mapping            |
| `GUI_PORT`       | `3000`                  | GUI port                    |
| `API_URL`        | `http://localhost:8080` | API URL for GUI             |
| `DEV_MODE`       | `false`                 | Enable development features |
| `IMAGE_NAME`     | `nanosimlab-api:local`  | Backend Docker image name   |
| `GUI_IMAGE_NAME` | `nanosimlab-gui:local`  | Frontend Docker image name  |

### Development Mode

Enable development mode for hot reloading and debugging:

```bash
# Set in .env file
DEV_MODE=true

# Or set temporarily
DEV_MODE=true ./run.sh up
```

Development mode features:
- Source code hot reloading
- Additional development tools in containers
- Verbose logging
- Development server with auto-restart

## Web GUI Features

The automatically generated GUI provides:

### 🚀 Quick Start
- Predefined simulation presets (small test, nanoparticles, charged particles)
- One-click simulation launching

### ⚙️ Simulation Configuration
- Interactive parameter adjustment
- Real-time form validation
- Support for Lennard-Jones and Yukawa potentials

### 📊 Live Monitoring
- Real-time progress tracking
- Job status updates
- Background simulation execution

### 📈 Results Visualization
- Trajectory summaries
- Mean-squared displacement (MSD) analysis
- Radial distribution function (RDF) plots
- Downloadable results

### 📱 Responsive Design
- Mobile-friendly interface
- Modern, accessible UI components
- Real-time status indicators

## API Endpoints

The REST API provides programmatic access to NanoSimLab:

### Core Endpoints

| Method   | Endpoint                    | Description                 |
| -------- | --------------------------- | --------------------------- |
| `GET`    | `/`                         | Health check                |
| `GET`    | `/status`                   | Service status              |
| `POST`   | `/simulate`                 | Start simulation            |
| `GET`    | `/simulate/{job_id}`        | Get job status              |
| `GET`    | `/simulate/{job_id}/result` | Get results                 |
| `GET`    | `/jobs`                     | List all jobs               |
| `DELETE` | `/jobs/{job_id}`            | Delete job                  |
| `POST`   | `/analyze`                  | Analyze uploaded trajectory |
| `GET`    | `/presets`                  | Get simulation presets      |

### Interactive Documentation

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

## Example Usage

### Start a Simulation via API

```bash
# Start simulation
curl -X POST "http://localhost:8080/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "n_particles": 100,
    "box_size": 15.0,
    "steps": 5000,
    "potential": {
      "type": "lj",
      "epsilon": 1.0,
      "sigma": 1.0
    }
  }'

# Response: {"job_id": "uuid", "status": "queued", ...}
```

### Check Job Status

```bash
curl "http://localhost:8080/simulate/{job_id}"
```

### Using the Python Client

```python
import requests

# Start simulation
response = requests.post("http://localhost:8080/simulate", json={
    "n_particles": 200,
    "box_size": 20.0,
    "steps": 10000,
    "potential": {"type": "lj", "epsilon": 1.0, "sigma": 1.0}
})

job_id = response.json()["job_id"]

# Poll for completion
import time
while True:
    status = requests.get(f"http://localhost:8080/simulate/{job_id}").json()
    if status["status"] == "completed":
        break
    time.sleep(2)

# Get results
results = requests.get(f"http://localhost:8080/simulate/{job_id}/result").json()
```

## Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Check what's using the port
lsof -i :8080
# Or change the port
PORTS=8081:8080 ./run.sh up
```

**2. Docker Permission Issues**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Then logout and login again
```

**3. GUI Not Loading**
```bash
# Check API connectivity
curl http://localhost:8080/status

# Recreate GUI
./run.sh gui:create --force
./run.sh restart
```

**4. Memory Issues**
```bash
# Monitor container resources
docker stats

# Adjust container limits in docker-compose.yml
```

### Debug Mode

Enable verbose logging:

```bash
# Show detailed logs
./run.sh logs api

# Follow logs in real-time
./run.sh logs api | tail -f

# Check container health
docker inspect nanosimlab-api | grep Health -A 10
```

### Resetting Everything

```bash
# Complete reset
./run.sh clean
./run.sh prune  # WARNING: removes all Docker data
./run.sh up
```

## Performance Optimization

### Resource Limits

Adjust container resources in `docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 4G      # Increase for large simulations
          cpus: '2.0'     # Use multiple cores
```

### Scaling

Run multiple API instances:

```bash
# Scale API service
docker-compose up --scale api=3
```

### GPU Support

For GPU-accelerated simulations (future feature):

```yaml
services:
  api:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## Production Deployment

For production use:

1. **Use environment-specific configuration:**
   ```bash
   cp .env.example .env.production
   # Edit production settings
   ```

2. **Enable HTTPS:**
   - Use a reverse proxy (nginx, traefik)
   - Configure SSL certificates
   - Update CORS settings

3. **Use external databases:**
   - Redis for job queue
   - PostgreSQL for persistent data

4. **Monitor and log:**
   - Set up log aggregation
   - Configure health monitoring
   - Set resource alerts

## Contributing

When contributing Docker-related changes:

1. Test with both `docker compose` and `docker-compose`
2. Ensure compatibility with both development and production modes
3. Update documentation for any new environment variables
4. Test the complete workflow with `./run.sh up`

For more information, see the main [README.md](../README.md) and [CONTRIBUTING.md](../CONTRIBUTING.md).
