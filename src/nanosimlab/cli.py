"""
Command-line interface for NanoSimLab.

This module provides a user-friendly CLI for running simulations and
analyzing trajectories without requiring Python programming knowledge.
"""

from __future__ import annotations

import click
import numpy as np
from typing import Optional

from .system import BDSimulation
from .potentials import LennardJones, Yukawa
from .analysis import msd, rdf, diffusion_coefficient


@click.group()
@click.version_option()
def main() -> None:
    """
    NanoSimLab: Brownian dynamics toolkit for nanoparticles.
    
    Simulate and analyze nanoparticle systems using Brownian dynamics.
    Run 'nanosim COMMAND --help' for detailed options.
    """
    pass


@main.command()
@click.option(
    "--n", 
    type=int, 
    default=200, 
    help="Number of particles"
)
@click.option(
    "--box", 
    type=float, 
    default=20.0, 
    help="Periodic box length (use 'none' for open boundaries)"
)
@click.option(
    "--dim", 
    type=int, 
    default=3, 
    help="Spatial dimensionality (2 or 3)"
)
@click.option(
    "--steps", 
    type=int, 
    default=10000, 
    help="Number of integration steps"
)
@click.option(
    "--dt", 
    type=float, 
    default=1e-4, 
    help="Integration time step"
)
@click.option(
    "--temp", 
    type=float, 
    default=1.0, 
    help="System temperature (k_B=1)"
)
@click.option(
    "--gamma", 
    type=float, 
    default=1.0, 
    help="Friction coefficient"
)
@click.option(
    "--potential", 
    type=click.Choice(["lj", "yukawa", "none"]), 
    default="lj",
    help="Pair potential type"
)
@click.option(
    "--epsilon", 
    type=float, 
    default=1.0, 
    help="Lennard-Jones epsilon parameter"
)
@click.option(
    "--sigma", 
    type=float, 
    default=1.0, 
    help="Lennard-Jones sigma parameter"
)
@click.option(
    "--rcut", 
    type=float, 
    default=2.5, 
    help="Potential cutoff radius"
)
@click.option(
    "--A", 
    "A_yuk", 
    type=float, 
    default=1.0, 
    help="Yukawa A parameter"
)
@click.option(
    "--kappa", 
    type=float, 
    default=1.0, 
    help="Yukawa kappa parameter"
)
@click.option(
    "--seed", 
    type=int, 
    default=None, 
    help="Random seed for reproducibility"
)
@click.option(
    "--save-every", 
    type=int, 
    default=100, 
    help="Save trajectory every N steps"
)
@click.option(
    "--out", 
    type=str, 
    default="trajectory.npz", 
    help="Output trajectory file"
)
def simulate(
    n: int,
    box: float,
    dim: int,
    steps: int,
    dt: float,
    temp: float,
    gamma: float,
    potential: str,
    epsilon: float,
    sigma: float,
    rcut: float,
    A_yuk: float,
    kappa: float,
    seed: Optional[int],
    save_every: int,
    out: str
) -> None:
    """Run Brownian dynamics simulation."""
    
    # Handle box specification
    box_size = None if box == 0 else box
    
    # Set up potential
    if potential == "lj":
        pot = LennardJones(epsilon=epsilon, sigma=sigma, rcut=rcut)
    elif potential == "yukawa":
        pot = Yukawa(A=A_yuk, kappa=kappa, rcut=rcut)
    else:
        pot = None
    
    # Create simulation
    sim = BDSimulation(
        n=n,
        box=box_size,
        dim=dim,
        temperature=temp,
        gamma=gamma,
        potential=pot,
        seed=seed
    )
    
    # Run simulation with progress indication
    click.echo(f"Running simulation: {n} particles, {steps} steps...")
    
    traj = sim.run(steps=steps, dt=dt, save_every=save_every)
    
    # Save trajectory
    np.savez(
        out,
        positions=traj["positions"],
        times=traj["times"],
        box=traj["box"],
        dim=traj["dim"],
        n_particles=traj["n_particles"]
    )
    
    click.echo(f"Simulation complete! Saved {traj['positions'].shape[0]} "
               f"frames to {out}")


@main.command()
@click.option(
    "--traj", 
    type=str, 
    required=True, 
    help="Input trajectory file (NPZ format)"
)
@click.option(
    "--box", 
    type=float, 
    default=None, 
    help="Override box length from file"
)
@click.option(
    "--rdf/--no-rdf", 
    default=True, 
    help="Compute radial distribution function"
)
@click.option(
    "--msd/--no-msd", 
    "do_msd", 
    default=True, 
    help="Compute mean-squared displacement"
)
@click.option(
    "--diffusion/--no-diffusion", 
    "do_diffusion", 
    default=False,
    help="Estimate diffusion coefficient from MSD"
)
@click.option(
    "--output", 
    type=str, 
    default=None, 
    help="Save analysis results to file"
)
def analyze(
    traj: str,
    box: Optional[float],
    rdf: bool,
    do_msd: bool,
    do_diffusion: bool,
    output: Optional[str]
) -> None:
    """Analyze simulation trajectory."""
    
    # Load trajectory data
    try:
        data = np.load(traj)
    except FileNotFoundError:
        click.echo(f"Error: Trajectory file '{traj}' not found.", err=True)
        return
    except Exception as e:
        click.echo(f"Error loading trajectory: {e}", err=True)
        return
    
    positions = data["positions"]
    times = data["times"]
    file_box = float(data["box"]) if "box" in data and data["box"] else None
    dim = int(data["dim"]) if "dim" in data else 3
    
    # Use file box or override
    box_size = file_box if box is None else box
    
    click.echo(f"Loaded trajectory: {positions.shape[0]} frames, "
               f"{positions.shape[1]} particles, {dim}D")
    
    results = {}
    
    # Mean-squared displacement
    if do_msd:
        click.echo("Computing mean-squared displacement...")
        t_msd, msd_values = msd(positions, times, box=box_size)
        results["msd"] = {"times": t_msd, "values": msd_values}
        
        # Print sample values
        n_show = min(10, len(t_msd))
        click.echo("MSD results (first 10 points):")
        for i in range(n_show):
            click.echo(f"  t={t_msd[i]:.6f}, MSD={msd_values[i]:.6f}")
        
        # Diffusion coefficient
        if do_diffusion and len(t_msd) > 10:
            try:
                D, r2 = diffusion_coefficient(t_msd, msd_values, dim=dim)
                results["diffusion"] = {"coefficient": D, "r_squared": r2}
                click.echo(f"Diffusion coefficient: D = {D:.6f} "
                          f"(R² = {r2:.4f})")
            except Exception as e:
                click.echo(f"Could not compute diffusion coefficient: {e}")
    
    # Radial distribution function
    if rdf:
        if box_size is None:
            click.echo("Warning: RDF requires periodic boundaries. Skipping.")
        else:
            click.echo("Computing radial distribution function...")
            r_vals, g_vals = rdf(positions, box=box_size)
            results["rdf"] = {"r": r_vals, "g": g_vals}
            
            # Print sample values
            n_show = min(10, len(r_vals))
            click.echo("RDF results (first 10 points):")
            for i in range(n_show):
                click.echo(f"  r={r_vals[i]:.3f}, g(r)={g_vals[i]:.3f}")
    
    # Save results if requested
    if output:
        np.savez(output, **results)
        click.echo(f"Analysis results saved to {output}")


if __name__ == "__main__":
    main()
