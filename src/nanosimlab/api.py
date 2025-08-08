"""
FastAPI web server for NanoSimLab.

This module provides a REST API interface for running simulations and analysis
through a web interface.
"""

from __future__ import annotations

import io
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import __version__
from .analysis import msd, rdf
from .potentials import LennardJones, Yukawa
from .system import BDSimulation


# Pydantic models for API requests/responses
class PotentialConfig(BaseModel):
    """Configuration for pair potentials."""
    type: str = Field(..., description="Potential type: 'lj' or 'yukawa'")
    epsilon: float = Field(1.0, description="LJ epsilon parameter")
    sigma: float = Field(1.0, description="LJ sigma parameter")
    rcut: Optional[float] = Field(2.5, description="Cutoff radius")
    A: float = Field(1.0, description="Yukawa A parameter")
    kappa: float = Field(1.0, description="Yukawa kappa parameter")


class SimulationConfig(BaseModel):
    """Configuration for simulation parameters."""
    n_particles: int = Field(200, ge=1, le=10000, description="Number of particles")
    box_size: float = Field(20.0, gt=0, description="Periodic box size")
    dimension: int = Field(3, ge=2, le=3, description="Spatial dimension")
    steps: int = Field(10000, ge=1, le=1000000, description="Number of integration steps")
    dt: float = Field(1e-4, gt=0, description="Time step")
    temperature: float = Field(1.0, gt=0, description="System temperature")
    gamma: float = Field(1.0, gt=0, description="Friction coefficient")
    save_every: int = Field(100, ge=1, description="Save frequency")
    seed: Optional[int] = Field(None, description="Random seed")
    potential: PotentialConfig = Field(..., description="Potential configuration")


class AnalysisConfig(BaseModel):
    """Configuration for analysis parameters."""
    compute_msd: bool = Field(True, description="Compute mean-squared displacement")
    compute_rdf: bool = Field(True, description="Compute radial distribution function")
    rdf_bins: int = Field(100, ge=10, le=1000, description="Number of RDF bins")
    rdf_max: Optional[float] = Field(None, description="Maximum RDF distance")


class SimulationStatus(BaseModel):
    """Status of a simulation job."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: 'running', 'completed', 'failed'")
    progress: float = Field(0.0, ge=0, le=1, description="Completion progress (0-1)")
    message: str = Field("", description="Status message")
    result: Optional[Dict[str, Any]] = Field(None, description="Simulation results")


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = Field("healthy", description="Service status")
    version: str = Field(__version__, description="NanoSimLab version")
    timestamp: str = Field(..., description="Current timestamp")


# Global storage for simulation jobs (in production, use Redis/database)
simulation_jobs: Dict[str, SimulationStatus] = {}


def create_potential(config: PotentialConfig):
    """Create potential object from configuration."""
    if config.type == "lj":
        return LennardJones(
            epsilon=config.epsilon,
            sigma=config.sigma,
            rcut=config.rcut
        )
    elif config.type == "yukawa":
        return Yukawa(
            A=config.A,
            kappa=config.kappa,
            rcut=config.rcut
        )
    else:
        raise ValueError(f"Unsupported potential type: {config.type}")


def run_simulation_task(job_id: str, sim_config: SimulationConfig, analysis_config: AnalysisConfig):
    """Background task for running simulation."""
    try:
        # Update status to running
        simulation_jobs[job_id].status = "running"
        simulation_jobs[job_id].progress = 0.1
        simulation_jobs[job_id].message = "Initializing simulation..."

        # Create potential
        potential = create_potential(sim_config.potential)

        # Create simulation
        sim = BDSimulation(
            n=sim_config.n_particles,
            box=sim_config.box_size,
            dim=sim_config.dimension,
            temperature=sim_config.temperature,
            gamma=sim_config.gamma,
            potential=potential,
            seed=sim_config.seed
        )

        simulation_jobs[job_id].progress = 0.2
        simulation_jobs[job_id].message = "Running simulation..."

        # Run simulation
        trajectory = sim.run(
            steps=sim_config.steps,
            dt=sim_config.dt,
            save_every=sim_config.save_every
        )

        simulation_jobs[job_id].progress = 0.8
        simulation_jobs[job_id].message = "Analyzing results..."

        # Prepare results
        results = {
            "trajectory": {
                "positions": trajectory["positions"].tolist(),
                "times": trajectory["times"].tolist(),
                "box": trajectory["box"],
                "dimension": trajectory["dim"],
                "n_frames": len(trajectory["times"]),
                "n_particles": sim_config.n_particles
            },
            "parameters": sim_config.dict()
        }

        # Run analysis if requested
        if analysis_config.compute_msd:
            times, msd_values = msd(trajectory["positions"], trajectory["times"], box=trajectory["box"])
            results["analysis"] = results.get("analysis", {})
            results["analysis"]["msd"] = {
                "times": times.tolist(),
                "values": msd_values.tolist()
            }

        if analysis_config.compute_rdf:
            r_values, g_values = rdf(
                trajectory["positions"],
                box=trajectory["box"],
                r_max=analysis_config.rdf_max,
                bins=analysis_config.rdf_bins
            )
            results["analysis"] = results.get("analysis", {})
            results["analysis"]["rdf"] = {
                "r": r_values.tolist(),
                "g": g_values.tolist()
            }

        # Update status to completed
        simulation_jobs[job_id].status = "completed"
        simulation_jobs[job_id].progress = 1.0
        simulation_jobs[job_id].message = "Simulation completed successfully"
        simulation_jobs[job_id].result = results

    except Exception as e:
        simulation_jobs[job_id].status = "failed"
        simulation_jobs[job_id].message = f"Simulation failed: {str(e)}"


# Create FastAPI app
app = FastAPI(
    title="NanoSimLab API",
    description="REST API for Brownian dynamics simulations and nanorobotics research",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    from datetime import datetime
    return HealthCheck(
        status="healthy",
        version=__version__,
        timestamp=datetime.now().isoformat()
    )


@app.get("/status", response_model=HealthCheck)
async def get_status():
    """Get service status."""
    return await health_check()


@app.post("/simulate", response_model=SimulationStatus)
async def start_simulation(
    background_tasks: BackgroundTasks,
    sim_config: SimulationConfig,
    analysis_config: AnalysisConfig = AnalysisConfig()
):
    """Start a new simulation job."""
    import uuid

    job_id = str(uuid.uuid4())

    # Initialize job status
    simulation_jobs[job_id] = SimulationStatus(
        job_id=job_id,
        status="queued",
        progress=0.0,
        message="Simulation queued for execution"
    )

    # Start background task
    background_tasks.add_task(run_simulation_task, job_id, sim_config, analysis_config)

    return simulation_jobs[job_id]


@app.get("/simulate/{job_id}", response_model=SimulationStatus)
async def get_simulation_status(job_id: str):
    """Get status of a simulation job."""
    if job_id not in simulation_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return simulation_jobs[job_id]


@app.get("/simulate/{job_id}/result")
async def get_simulation_result(job_id: str):
    """Get results of a completed simulation."""
    if job_id not in simulation_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = simulation_jobs[job_id]
    if job.status != "completed":
        raise HTTPException(status_code=400, detail=f"Job status: {job.status}")

    return job.result


@app.get("/jobs")
async def list_jobs():
    """List all simulation jobs."""
    return {
        "jobs": [
            {
                "job_id": job_id,
                "status": job.status,
                "progress": job.progress,
                "message": job.message
            }
            for job_id, job in simulation_jobs.items()
        ]
    }


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a simulation job."""
    if job_id not in simulation_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    del simulation_jobs[job_id]
    return {"message": f"Job {job_id} deleted successfully"}


@app.post("/analyze")
async def analyze_trajectory(
    trajectory_file: UploadFile = File(...),
    analysis_config: AnalysisConfig = AnalysisConfig()
):
    """Analyze an uploaded trajectory file."""
    try:
        # Read uploaded file
        content = await trajectory_file.read()

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Load trajectory
            data = np.load(tmp_path)
            positions = data["positions"]
            times = data["times"]
            box = float(data["box"]) if "box" in data else None

            results = {}

            # Run analysis
            if analysis_config.compute_msd:
                times_msd, msd_values = msd(positions, times, box=box)
                results["msd"] = {
                    "times": times_msd.tolist(),
                    "values": msd_values.tolist()
                }

            if analysis_config.compute_rdf and box is not None:
                r_values, g_values = rdf(
                    positions,
                    box=box,
                    r_max=analysis_config.rdf_max,
                    bins=analysis_config.rdf_bins
                )
                results["rdf"] = {
                    "r": r_values.tolist(),
                    "g": g_values.tolist()
                }

            return results

        finally:
            # Clean up temporary file
            Path(tmp_path).unlink()

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Analysis failed: {str(e)}")


@app.get("/presets")
async def get_simulation_presets():
    """Get predefined simulation presets."""
    presets = {
        "small_test": {
            "name": "Small Test System",
            "description": "Quick test with 50 particles",
            "config": {
                "n_particles": 50,
                "box_size": 10.0,
                "steps": 5000,
                "potential": {"type": "lj", "epsilon": 1.0, "sigma": 1.0}
            }
        },
        "nanoparticles": {
            "name": "Nanoparticle Suspension",
            "description": "200 nanoparticles in solution",
            "config": {
                "n_particles": 200,
                "box_size": 20.0,
                "steps": 20000,
                "potential": {"type": "lj", "epsilon": 1.0, "sigma": 1.0}
            }
        },
        "charged_particles": {
            "name": "Charged Nanoparticles",
            "description": "Electrostatically interacting particles",
            "config": {
                "n_particles": 100,
                "box_size": 15.0,
                "steps": 15000,
                "potential": {"type": "yukawa", "A": 2.0, "kappa": 1.5}
            }
        }
    }
    return presets


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
