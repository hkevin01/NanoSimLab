#!/bin/bash

set -Eeuo pipefail

# Trap errors and provide helpful messages
trap 'echo "ERROR: Script failed at line $LINENO" >&2' ERR

# Project configuration with defaults
IMAGE_NAME="${IMAGE_NAME:-nanosimlab-api:local}"
GUI_IMAGE_NAME="${GUI_IMAGE_NAME:-nanosimlab-gui:local}"
SERVICE_NAME="${SERVICE_NAME:-api}"
GUI_SERVICE_NAME="${GUI_SERVICE_NAME:-gui}"
ENV_FILE="${ENV_FILE:-.env}"
PORTS="${PORTS:-8080:8080}"
GUI_PORT="${GUI_PORT:-3000}"
API_URL="${API_URL:-http://localhost:8080}"
GUI_PATH="${GUI_PATH:-./gui}"
DEV_MODE="${DEV_MODE:-false}"
DOCKER_PLATFORM="${DOCKER_PLATFORM:-}"
MOUNTS="${MOUNTS:-}"
BUILD_ARGS="${BUILD_ARGS:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Detect project root (directory containing this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Change to project root
cd "$PROJECT_ROOT"

# Preflight checks
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running or not accessible"
        exit 1
    fi

    log_success "Docker is available"
}

# Detect docker compose command
detect_compose() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    elif command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    else
        log_error "Neither 'docker compose' nor 'docker-compose' is available"
        exit 1
    fi
}

# Check if compose file exists
has_compose_file() {
    [[ -f "docker-compose.yml" ]] || [[ -f "compose.yaml" ]] || [[ -f "docker-compose.yaml" ]]
}

# Check if GUI exists
has_gui() {
    [[ -d "$GUI_PATH" ]] && [[ -f "$GUI_PATH/index.html" ]]
}

# Platform flag for Docker
get_platform_flag() {
    if [[ -n "$DOCKER_PLATFORM" ]]; then
        echo "--platform $DOCKER_PLATFORM"
    fi
}

# Parse port mappings
parse_ports() {
    local ports_str="$1"
    echo "${ports_str//,/ -p }"
}

# Parse build args
parse_build_args() {
    local args_str="$1"
    if [[ -n "$args_str" ]]; then
        # Convert "KEY=VAL KEY2=VAL2" to "--build-arg KEY=VAL --build-arg KEY2=VAL2"
        echo "$args_str" | sed 's/\([^ =]*=[^ ]*\)/--build-arg \1/g'
    fi
}

# Parse mount specifications
parse_mounts() {
    local mounts_str="$1"
    if [[ -n "$mounts_str" ]]; then
        # Convert "src:dest,src2:dest2" to "-v src:dest -v src2:dest2"
        echo "$mounts_str" | sed 's/,/ -v /g' | sed 's/^/-v /'
    fi
}

# Create GUI scaffold
create_gui() {
    local force_create=false
    if [[ "${1:-}" == "--force" ]]; then
        force_create=true
    fi

    if has_gui && [[ "$force_create" != true ]]; then
        log_warning "GUI already exists at $GUI_PATH. Use --force to overwrite."
        return 0
    fi

    log_info "Creating GUI scaffold at $GUI_PATH"

    # Create GUI directory
    mkdir -p "$GUI_PATH"

    # Create index.html
    cat > "$GUI_PATH/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NanoSimLab - Nanorobotics Simulation Platform</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🔬 NanoSimLab</h1>
            <p>Brownian Dynamics & Nanorobotics Simulation Platform</p>
            <div class="status-indicator" id="status">
                <span class="status-dot"></span>
                <span class="status-text">Connecting...</span>
            </div>
        </header>

        <main class="main">
            <div class="grid">
                <!-- Quick Start Panel -->
                <section class="card">
                    <h2>🚀 Quick Start</h2>
                    <div class="preset-buttons">
                        <button class="btn btn-primary" onclick="loadPreset('small_test')">
                            Small Test (50 particles)
                        </button>
                        <button class="btn btn-primary" onclick="loadPreset('nanoparticles')">
                            Nanoparticles (200 particles)
                        </button>
                        <button class="btn btn-primary" onclick="loadPreset('charged_particles')">
                            Charged Particles
                        </button>
                    </div>
                </section>

                <!-- Simulation Configuration -->
                <section class="card">
                    <h2>⚙️ Simulation Setup</h2>
                    <form id="sim-form">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="n_particles">Particles:</label>
                                <input type="number" id="n_particles" value="200" min="1" max="10000">
                            </div>
                            <div class="form-group">
                                <label for="box_size">Box Size:</label>
                                <input type="number" id="box_size" value="20.0" min="1" step="0.1">
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label for="steps">Steps:</label>
                                <input type="number" id="steps" value="10000" min="100" max="1000000">
                            </div>
                            <div class="form-group">
                                <label for="temperature">Temperature:</label>
                                <input type="number" id="temperature" value="1.0" min="0.1" step="0.1">
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label for="potential_type">Potential:</label>
                                <select id="potential_type">
                                    <option value="lj">Lennard-Jones</option>
                                    <option value="yukawa">Yukawa (Screened Coulomb)</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="epsilon">Epsilon/A:</label>
                                <input type="number" id="epsilon" value="1.0" step="0.1">
                            </div>
                        </div>

                        <button type="submit" class="btn btn-success" id="run-btn">
                            🎯 Run Simulation
                        </button>
                    </form>
                </section>

                <!-- Job Status -->
                <section class="card" id="status-card" style="display: none;">
                    <h2>📊 Simulation Status</h2>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress"></div>
                        </div>
                        <span class="progress-text" id="progress-text">0%</span>
                    </div>
                    <p class="status-message" id="status-message">Initializing...</p>
                    <div class="job-actions">
                        <button class="btn btn-secondary" id="view-results" style="display: none;">
                            📈 View Results
                        </button>
                    </div>
                </section>

                <!-- Results Visualization -->
                <section class="card full-width" id="results-card" style="display: none;">
                    <h2>📈 Results</h2>
                    <div class="results-tabs">
                        <button class="tab-btn active" onclick="showTab('trajectory')">Trajectory</button>
                        <button class="tab-btn" onclick="showTab('msd')">MSD</button>
                        <button class="tab-btn" onclick="showTab('rdf')">RDF</button>
                    </div>

                    <div class="tab-content">
                        <div id="trajectory-tab" class="tab-pane active">
                            <div class="plot-container" id="trajectory-plot">
                                <p>3D trajectory visualization will appear here</p>
                            </div>
                        </div>
                        <div id="msd-tab" class="tab-pane">
                            <div class="plot-container" id="msd-plot">
                                <p>Mean-squared displacement plot will appear here</p>
                            </div>
                        </div>
                        <div id="rdf-tab" class="tab-pane">
                            <div class="plot-container" id="rdf-plot">
                                <p>Radial distribution function plot will appear here</p>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- System Info -->
                <section class="card">
                    <h2>ℹ️ System Information</h2>
                    <div class="info-grid" id="system-info">
                        <div class="info-item">
                            <span class="info-label">API Status:</span>
                            <span class="info-value" id="api-status">Checking...</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Version:</span>
                            <span class="info-value" id="api-version">-</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Active Jobs:</span>
                            <span class="info-value" id="active-jobs">0</span>
                        </div>
                    </div>
                </section>
            </div>
        </main>

        <footer class="footer">
            <p>&copy; 2025 NanoSimLab - Lightweight toolkit for nanorobotics research</p>
        </footer>
    </div>

    <script src="app.js"></script>
</body>
</html>
EOF

    # Create styles.css
    cat > "$GUI_PATH/styles.css" << 'EOF'
/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    line-height: 1.6;
    color: #333;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

/* Header */
.header {
    text-align: center;
    color: white;
    margin-bottom: 30px;
}

.header h1 {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 10px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.header p {
    font-size: 1.2rem;
    opacity: 0.9;
    margin-bottom: 20px;
}

.status-indicator {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(255,255,255,0.2);
    padding: 8px 16px;
    border-radius: 20px;
    backdrop-filter: blur(10px);
}

.status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #ff4444;
    animation: pulse 2s infinite;
}

.status-dot.connected {
    background: #44ff44;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

/* Main content */
.main {
    flex: 1;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
}

.full-width {
    grid-column: 1 / -1;
}

/* Cards */
.card {
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.2);
}

.card h2 {
    color: #333;
    margin-bottom: 20px;
    font-size: 1.4rem;
    font-weight: 600;
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.3s ease;
    text-align: center;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn-success {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white;
}

.btn-secondary {
    background: #6c757d;
    color: white;
}

.btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
}

.preset-buttons {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

/* Forms */
.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 16px;
}

.form-group {
    display: flex;
    flex-direction: column;
}

.form-group label {
    font-weight: 500;
    margin-bottom: 4px;
    color: #555;
}

.form-group input,
.form-group select {
    padding: 10px;
    border: 2px solid #e1e5e9;
    border-radius: 6px;
    font-size: 14px;
    transition: border-color 0.3s ease;
}

.form-group input:focus,
.form-group select:focus {
    outline: none;
    border-color: #667eea;
}

/* Progress bar */
.progress-container {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
}

.progress-bar {
    flex: 1;
    height: 8px;
    background: #e1e5e9;
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
    border-radius: 4px;
    transition: width 0.3s ease;
    width: 0%;
}

.progress-text {
    font-weight: 500;
    color: #667eea;
    min-width: 40px;
}

.status-message {
    color: #666;
    font-style: italic;
    margin-bottom: 16px;
}

/* Tabs */
.results-tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
    border-bottom: 2px solid #e1e5e9;
}

.tab-btn {
    padding: 12px 20px;
    border: none;
    background: none;
    color: #666;
    font-weight: 500;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.3s ease;
}

.tab-btn.active {
    color: #667eea;
    border-bottom-color: #667eea;
}

.tab-pane {
    display: none;
}

.tab-pane.active {
    display: block;
}

.plot-container {
    min-height: 300px;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666;
}

/* Info grid */
.info-grid {
    display: grid;
    gap: 12px;
}

.info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #e1e5e9;
}

.info-label {
    font-weight: 500;
    color: #555;
}

.info-value {
    color: #333;
    font-weight: 400;
}

/* Footer */
.footer {
    text-align: center;
    color: white;
    opacity: 0.8;
    padding: 20px 0;
    margin-top: 20px;
}

/* Responsive design */
@media (max-width: 768px) {
    .container {
        padding: 15px;
    }

    .header h1 {
        font-size: 2rem;
    }

    .form-row {
        grid-template-columns: 1fr;
    }

    .grid {
        grid-template-columns: 1fr;
    }

    .preset-buttons {
        flex-direction: column;
    }

    .results-tabs {
        flex-wrap: wrap;
    }
}

@media (max-width: 480px) {
    .card {
        padding: 16px;
    }

    .btn {
        padding: 10px 16px;
        font-size: 13px;
    }
}
EOF

    # Create app.js
    cat > "$GUI_PATH/app.js" << 'EOF'
class NanoSimLabApp {
    constructor() {
        this.apiUrl = this.getApiUrl();
        this.currentJobId = null;
        this.statusCheckInterval = null;
        this.presets = {};

        this.init();
    }

    getApiUrl() {
        // Try to get API URL from config.json, fallback to environment or default
        if (window.ENV && window.ENV.API_URL) {
            return window.ENV.API_URL;
        }
        return 'http://localhost:8080';
    }

    async init() {
        await this.loadConfig();
        this.setupEventListeners();
        this.checkApiStatus();
        this.loadPresets();

        // Check API status every 30 seconds
        setInterval(() => this.checkApiStatus(), 30000);
    }

    async loadConfig() {
        try {
            const response = await fetch('./config.json');
            if (response.ok) {
                const config = await response.json();
                this.apiUrl = config.API_URL || this.apiUrl;
            }
        } catch (error) {
            console.log('No config.json found, using default API URL');
        }
    }

    setupEventListeners() {
        // Simulation form
        document.getElementById('sim-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.startSimulation();
        });

        // Potential type change
        document.getElementById('potential_type').addEventListener('change', (e) => {
            this.updatePotentialFields(e.target.value);
        });

        // View results button
        document.getElementById('view-results').addEventListener('click', () => {
            this.showResults();
        });
    }

    updatePotentialFields(potentialType) {
        const epsilonLabel = document.querySelector('label[for="epsilon"]');
        if (potentialType === 'lj') {
            epsilonLabel.textContent = 'Epsilon:';
        } else if (potentialType === 'yukawa') {
            epsilonLabel.textContent = 'A:';
        }
    }

    async checkApiStatus() {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');
        const apiStatus = document.getElementById('api-status');
        const apiVersion = document.getElementById('api-version');

        try {
            const response = await fetch(`${this.apiUrl}/status`);
            if (response.ok) {
                const data = await response.json();
                statusDot.classList.add('connected');
                statusText.textContent = 'Connected';
                apiStatus.textContent = 'Online';
                apiVersion.textContent = data.version;
            } else {
                throw new Error('API not responding');
            }
        } catch (error) {
            statusDot.classList.remove('connected');
            statusText.textContent = 'Disconnected';
            apiStatus.textContent = 'Offline';
            apiVersion.textContent = '-';
        }

        this.updateJobCount();
    }

    async loadPresets() {
        try {
            const response = await fetch(`${this.apiUrl}/presets`);
            if (response.ok) {
                this.presets = await response.json();
            }
        } catch (error) {
            console.error('Failed to load presets:', error);
        }
    }

    loadPreset(presetName) {
        const preset = this.presets[presetName];
        if (!preset) return;

        const config = preset.config;

        // Update form fields
        document.getElementById('n_particles').value = config.n_particles;
        document.getElementById('box_size').value = config.box_size;
        document.getElementById('steps').value = config.steps;
        document.getElementById('temperature').value = config.temperature || 1.0;
        document.getElementById('potential_type').value = config.potential.type;
        document.getElementById('epsilon').value = config.potential.epsilon || config.potential.A || 1.0;

        this.updatePotentialFields(config.potential.type);

        // Show notification
        this.showNotification(`Loaded preset: ${preset.name}`, 'success');
    }

    async startSimulation() {
        const formData = this.getFormData();
        const runBtn = document.getElementById('run-btn');

        // Disable run button
        runBtn.disabled = true;
        runBtn.textContent = '🔄 Starting...';

        try {
            const response = await fetch(`${this.apiUrl}/simulate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const result = await response.json();
                this.currentJobId = result.job_id;
                this.showStatusCard();
                this.startStatusPolling();
                this.showNotification('Simulation started successfully!', 'success');
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to start simulation');
            }
        } catch (error) {
            this.showNotification(`Error: ${error.message}`, 'error');
        } finally {
            // Re-enable run button
            runBtn.disabled = false;
            runBtn.textContent = '🎯 Run Simulation';
        }
    }

    getFormData() {
        const potentialType = document.getElementById('potential_type').value;
        const epsilonValue = parseFloat(document.getElementById('epsilon').value);

        const potential = {
            type: potentialType,
            rcut: 2.5
        };

        if (potentialType === 'lj') {
            potential.epsilon = epsilonValue;
            potential.sigma = 1.0;
        } else if (potentialType === 'yukawa') {
            potential.A = epsilonValue;
            potential.kappa = 1.0;
        }

        return {
            n_particles: parseInt(document.getElementById('n_particles').value),
            box_size: parseFloat(document.getElementById('box_size').value),
            dimension: 3,
            steps: parseInt(document.getElementById('steps').value),
            dt: 1e-4,
            temperature: parseFloat(document.getElementById('temperature').value),
            gamma: 1.0,
            save_every: 100,
            potential: potential
        };
    }

    showStatusCard() {
        document.getElementById('status-card').style.display = 'block';
        document.getElementById('results-card').style.display = 'none';
        document.getElementById('view-results').style.display = 'none';
    }

    startStatusPolling() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }

        this.statusCheckInterval = setInterval(() => {
            this.checkJobStatus();
        }, 2000);
    }

    async checkJobStatus() {
        if (!this.currentJobId) return;

        try {
            const response = await fetch(`${this.apiUrl}/simulate/${this.currentJobId}`);
            if (response.ok) {
                const status = await response.json();
                this.updateStatusDisplay(status);

                if (status.status === 'completed') {
                    clearInterval(this.statusCheckInterval);
                    document.getElementById('view-results').style.display = 'block';
                    this.showNotification('Simulation completed!', 'success');
                } else if (status.status === 'failed') {
                    clearInterval(this.statusCheckInterval);
                    this.showNotification(`Simulation failed: ${status.message}`, 'error');
                }
            }
        } catch (error) {
            console.error('Failed to check job status:', error);
        }
    }

    updateStatusDisplay(status) {
        const progressFill = document.getElementById('progress');
        const progressText = document.getElementById('progress-text');
        const statusMessage = document.getElementById('status-message');

        const progressPercent = Math.round(status.progress * 100);
        progressFill.style.width = `${progressPercent}%`;
        progressText.textContent = `${progressPercent}%`;
        statusMessage.textContent = status.message;
    }

    async showResults() {
        if (!this.currentJobId) return;

        try {
            const response = await fetch(`${this.apiUrl}/simulate/${this.currentJobId}/result`);
            if (response.ok) {
                const result = await response.json();
                this.displayResults(result);
                document.getElementById('results-card').style.display = 'block';
            }
        } catch (error) {
            this.showNotification(`Failed to load results: ${error.message}`, 'error');
        }
    }

    displayResults(result) {
        // Display trajectory info
        const trajectoryTab = document.getElementById('trajectory-tab');
        trajectoryTab.innerHTML = `
            <div class="plot-container">
                <div class="results-summary">
                    <h3>Trajectory Summary</h3>
                    <p><strong>Particles:</strong> ${result.trajectory.n_particles}</p>
                    <p><strong>Frames:</strong> ${result.trajectory.n_frames}</p>
                    <p><strong>Box Size:</strong> ${result.trajectory.box}</p>
                    <p><strong>Dimension:</strong> ${result.trajectory.dimension}D</p>
                    <p><strong>Final Time:</strong> ${result.trajectory.times[result.trajectory.times.length - 1].toFixed(3)}</p>
                </div>
            </div>
        `;

        // Display MSD results if available
        if (result.analysis && result.analysis.msd) {
            const msdTab = document.getElementById('msd-tab');
            msdTab.innerHTML = this.createPlotHtml('MSD vs Time', result.analysis.msd);
        }

        // Display RDF results if available
        if (result.analysis && result.analysis.rdf) {
            const rdfTab = document.getElementById('rdf-tab');
            rdfTab.innerHTML = this.createPlotHtml('Radial Distribution Function', result.analysis.rdf);
        }
    }

    createPlotHtml(title, data) {
        // Create a simple text-based plot representation
        const xData = data.times || data.r;
        const yData = data.values || data.g;

        return `
            <div class="plot-container">
                <h3>${title}</h3>
                <div class="plot-summary">
                    <p><strong>Data Points:</strong> ${xData.length}</p>
                    <p><strong>X Range:</strong> ${xData[0].toFixed(3)} - ${xData[xData.length-1].toFixed(3)}</p>
                    <p><strong>Y Range:</strong> ${Math.min(...yData).toFixed(3)} - ${Math.max(...yData).toFixed(3)}</p>
                    <p><em>Interactive plotting coming soon...</em></p>
                </div>
            </div>
        `;
    }

    async updateJobCount() {
        try {
            const response = await fetch(`${this.apiUrl}/jobs`);
            if (response.ok) {
                const data = await response.json();
                const activeJobs = data.jobs.filter(job =>
                    job.status === 'running' || job.status === 'queued'
                ).length;
                document.getElementById('active-jobs').textContent = activeJobs;
            }
        } catch (error) {
            // Silently fail for job count updates
        }
    }

    showTab(tabName) {
        // Remove active class from all tabs and panes
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

        // Add active class to selected tab and pane
        event.target.classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    showNotification(message, type = 'info') {
        // Simple notification system
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 20px',
            borderRadius: '8px',
            color: 'white',
            fontSize: '14px',
            fontWeight: '500',
            zIndex: '1000',
            opacity: '0',
            transform: 'translateY(-20px)',
            transition: 'all 0.3s ease'
        });

        if (type === 'success') {
            notification.style.background = '#28a745';
        } else if (type === 'error') {
            notification.style.background = '#dc3545';
        } else {
            notification.style.background = '#17a2b8';
        }

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, 100);

        // Remove after 4 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 4000);
    }
}

// Global functions for onclick handlers
window.loadPreset = function(presetName) {
    if (window.app) {
        window.app.loadPreset(presetName);
    }
};

window.showTab = function(tabName) {
    if (window.app) {
        window.app.showTab(tabName);
    }
};

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new NanoSimLabApp();
});
EOF

    # Create config.json
    cat > "$GUI_PATH/config.json" << EOF
{
    "API_URL": "$API_URL"
}
EOF

    # Create Dockerfile for GUI
    cat > "$GUI_PATH/Dockerfile" << 'EOF'
# Multi-stage build for GUI
FROM node:18-alpine AS builder

# Install nginx for serving static files
FROM nginx:alpine

# Copy GUI files
COPY index.html /usr/share/nginx/html/
COPY app.js /usr/share/nginx/html/
COPY styles.css /usr/share/nginx/html/
COPY config.json /usr/share/nginx/html/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF

    # Create nginx.conf for GUI
    cat > "$GUI_PATH/nginx.conf" << 'EOF'
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # Enable gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Serve index.html for all routes (SPA)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

    log_success "GUI scaffold created at $GUI_PATH"
}

# Open GUI in browser
open_gui() {
    local url="http://localhost:$GUI_PORT"
    log_info "Opening GUI at $url"

    if command -v xdg-open &> /dev/null; then
        xdg-open "$url"
    elif command -v open &> /dev/null; then
        open "$url"
    else
        log_warning "Could not detect browser opener. Please visit: $url"
    fi
}

# Build images
build_images() {
    log_info "Building Docker images..."

    # Set BuildKit
    export DOCKER_BUILDKIT=1

    # Parse build args
    local build_args_flags
    build_args_flags=$(parse_build_args "$BUILD_ARGS")

    # Platform flag
    local platform_flag
    platform_flag=$(get_platform_flag)

    # Build backend image
    log_info "Building backend image: $IMAGE_NAME"
    docker build $platform_flag $build_args_flags -t "$IMAGE_NAME" .

    # Build GUI image if GUI exists
    if has_gui; then
        log_info "Building GUI image: $GUI_IMAGE_NAME"
        docker build $platform_flag -t "$GUI_IMAGE_NAME" "$GUI_PATH"
    fi

    log_success "Images built successfully"
}

# Start services
start_services() {
    local compose_cmd
    compose_cmd=$(detect_compose)

    if has_compose_file; then
        log_info "Starting services with $compose_cmd"
        $compose_cmd up -d
    else
        log_info "No compose file found, starting containers directly"
        start_containers_direct
    fi

    log_success "Services started"
    log_info "API available at: http://localhost:${PORTS%:*}"
    if has_gui; then
        log_info "GUI available at: http://localhost:$GUI_PORT"
    fi
}

# Start containers directly (fallback)
start_containers_direct() {
    # Parse ports and mounts
    local port_flags
    port_flags=$(parse_ports "$PORTS")
    local mount_flags
    mount_flags=$(parse_mounts "$MOUNTS")
    local platform_flag
    platform_flag=$(get_platform_flag)

    # Start backend container
    log_info "Starting backend container"
    local env_file_flag=""
    if [[ -f "$ENV_FILE" ]]; then
        env_file_flag="--env-file $ENV_FILE"
    fi

    docker run -d \
        --name "${SERVICE_NAME}" \
        $platform_flag \
        $env_file_flag \
        -p $port_flags \
        $mount_flags \
        "$IMAGE_NAME"

    # Start GUI container if GUI exists
    if has_gui; then
        log_info "Starting GUI container"
        docker run -d \
            --name "${GUI_SERVICE_NAME}" \
            $platform_flag \
            -p "$GUI_PORT:80" \
            "$GUI_IMAGE_NAME"
    fi
}

# Stop services
stop_services() {
    local compose_cmd
    compose_cmd=$(detect_compose)

    if has_compose_file; then
        log_info "Stopping services with $compose_cmd"
        $compose_cmd down
    else
        log_info "Stopping containers directly"
        docker stop "${SERVICE_NAME}" 2>/dev/null || true
        docker rm "${SERVICE_NAME}" 2>/dev/null || true

        if has_gui; then
            docker stop "${GUI_SERVICE_NAME}" 2>/dev/null || true
            docker rm "${GUI_SERVICE_NAME}" 2>/dev/null || true
        fi
    fi

    log_success "Services stopped"
}

# Show logs
show_logs() {
    local service="${1:-$SERVICE_NAME}"
    local compose_cmd
    compose_cmd=$(detect_compose)

    if has_compose_file; then
        $compose_cmd logs -f "$service"
    else
        docker logs -f "$service"
    fi
}

# Execute command in container
exec_command() {
    local cmd="${1:-/bin/sh}"
    local service="${2:-$SERVICE_NAME}"
    local compose_cmd
    compose_cmd=$(detect_compose)

    if has_compose_file; then
        $compose_cmd exec "$service" $cmd
    else
        docker exec -it "$service" $cmd
    fi
}

# Show running containers
show_ps() {
    local compose_cmd
    compose_cmd=$(detect_compose)

    if has_compose_file; then
        $compose_cmd ps
    else
        docker ps --filter "name=${SERVICE_NAME}" --filter "name=${GUI_SERVICE_NAME}"
    fi
}

# Clean up containers and volumes
clean_up() {
    local compose_cmd
    compose_cmd=$(detect_compose)

    log_info "Cleaning up containers and volumes..."

    if has_compose_file; then
        $compose_cmd down -v --remove-orphans
    else
        docker stop "${SERVICE_NAME}" "${GUI_SERVICE_NAME}" 2>/dev/null || true
        docker rm "${SERVICE_NAME}" "${GUI_SERVICE_NAME}" 2>/dev/null || true
    fi

    log_success "Cleanup complete"
}

# Prune Docker system
prune_docker() {
    log_warning "This will remove all unused Docker images, containers, and networks"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker system prune -af
        log_success "Docker system pruned"
    else
        log_info "Prune cancelled"
    fi
}

# Show status
show_status() {
    log_info "=== NanoSimLab Docker Status ==="
    echo

    # API Status
    if curl -s "http://localhost:${PORTS%:*}/status" &>/dev/null; then
        log_success "API: Running (http://localhost:${PORTS%:*})"
    else
        log_error "API: Not accessible"
    fi

    # GUI Status
    if has_gui; then
        if curl -s "http://localhost:$GUI_PORT/health" &>/dev/null; then
            log_success "GUI: Running (http://localhost:$GUI_PORT)"
        else
            log_error "GUI: Not accessible"
        fi
    else
        log_warning "GUI: Not configured"
    fi

    echo
    log_info "Container Status:"
    show_ps
}

# Show usage
show_usage() {
    cat << EOF
🔬 NanoSimLab Docker Orchestration Script

USAGE:
    ./run.sh <command> [options]

COMMANDS:
    help                Show this help message
    build               Build Docker images
    up                  Start all services (build if needed)
    down                Stop and remove all services
    stop                Stop services without removing
    restart             Restart all services
    logs [service]      Show logs (default: $SERVICE_NAME)
    exec [cmd]          Execute command in container (default: /bin/sh)
    shell [service]     Open shell in container (default: $SERVICE_NAME)
    ps                  Show running containers
    clean               Clean up containers and volumes
    prune               Prune entire Docker system (WARNING: removes all unused images)
    gui:create [--force] Create GUI scaffold
    gui:open            Open GUI in browser
    status              Show service status

EXAMPLES:
    ./run.sh up                    # Start all services
    ./run.sh logs api             # Show API logs
    ./run.sh exec "pytest tests/" # Run tests in container
    ./run.sh shell gui            # Open shell in GUI container
    ./run.sh gui:create --force   # Recreate GUI scaffold

ENVIRONMENT VARIABLES:
    IMAGE_NAME="$IMAGE_NAME"
    GUI_IMAGE_NAME="$GUI_IMAGE_NAME"
    SERVICE_NAME="$SERVICE_NAME"
    GUI_SERVICE_NAME="$GUI_SERVICE_NAME"
    ENV_FILE="$ENV_FILE"
    PORTS="$PORTS"
    GUI_PORT="$GUI_PORT"
    API_URL="$API_URL"
    GUI_PATH="$GUI_PATH"
    DEV_MODE="$DEV_MODE"
    DOCKER_PLATFORM="$DOCKER_PLATFORM"
    MOUNTS="$MOUNTS"
    BUILD_ARGS="$BUILD_ARGS"

CONFIGURATION:
    - Place environment variables in $ENV_FILE
    - Modify docker-compose.yml for advanced configuration
    - GUI files are in $GUI_PATH/

For more information, visit: https://github.com/hkevin01/NanoSimLab
EOF
}

# Main command dispatcher
main() {
    local command="${1:-help}"

    # Always check Docker for commands that need it
    case "$command" in
        help)
            show_usage
            ;;
        gui:create)
            create_gui "${2:-}"
            ;;
        gui:open)
            open_gui
            ;;
        build)
            check_docker
            build_images
            ;;
        up)
            check_docker
            # Create GUI if it doesn't exist
            if ! has_gui; then
                log_info "GUI not found, creating scaffold..."
                create_gui
            fi
            # Build images if they don't exist
            if ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
                build_images
            fi
            start_services
            ;;
        down)
            check_docker
            stop_services
            ;;
        stop)
            check_docker
            local compose_cmd
            compose_cmd=$(detect_compose)
            if has_compose_file; then
                $compose_cmd stop
            else
                docker stop "${SERVICE_NAME}" "${GUI_SERVICE_NAME}" 2>/dev/null || true
            fi
            ;;
        restart)
            check_docker
            stop_services
            start_services
            ;;
        logs)
            check_docker
            show_logs "${2:-}"
            ;;
        exec)
            check_docker
            exec_command "${2:-/bin/sh}" "${3:-}"
            ;;
        shell)
            check_docker
            exec_command "/bin/sh" "${2:-$SERVICE_NAME}"
            ;;
        ps)
            check_docker
            show_ps
            ;;
        clean)
            check_docker
            clean_up
            ;;
        prune)
            check_docker
            prune_docker
            ;;
        status)
            show_status
            ;;
        *)
            log_error "Unknown command: $command"
            echo
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
